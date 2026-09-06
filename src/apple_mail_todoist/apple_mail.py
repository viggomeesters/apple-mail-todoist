"""Bounded read-only access to the current Apple Mail selection."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from datetime import datetime

from apple_mail_todoist.domain import ErrorCode, RedactedError, SelectedMail

MAX_SELECTION_OUTPUT_BYTES = 64 * 1024
CONVERSATION_PREFIX = re.compile(
    r"^(?:(?:re|fw|fwd|aw|antw)\s*(?:\[\d+\])?\s*:\s*)+",
    re.IGNORECASE,
)

SELECTION_JXA = r'''
// APPLE_MAIL_TODOIST_SELECTION_V1 -- read-only selection metadata.
function run() {
  const Mail = Application("Mail");
  return JSON.stringify(Mail.selection().map(message => {
    const received = message.dateReceived();
    return {
      apple_mail_id: String(message.id()),
      rfc_message_id: String(message.messageId() || ""),
      subject: String(message.subject() || "(no subject)"),
      sender_display: String(message.sender() || "(unknown sender)"),
      received_at: received ? received.toISOString() : ""
    };
  }));
}
'''.strip()


class MailSelectionError(RuntimeError):
    """A safe typed selection failure without raw Mail output."""

    def __init__(self, error: RedactedError) -> None:
        super().__init__(error.code.value)
        self.error = error


def run_jxa_selection(script: str, timeout_seconds: float) -> str:
    """Execute a constant JXA program and return stdout only on success."""

    try:
        completed = subprocess.run(
            ["/usr/bin/osascript", "-l", "JavaScript", "-e", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exception:
        raise MailSelectionError(
            RedactedError.from_exception(ErrorCode.MAIL_UNAVAILABLE, exception)
        ) from None
    if completed.returncode != 0:
        raise MailSelectionError(
            RedactedError(ErrorCode.MAIL_UNAVAILABLE, "JxaProcessError")
        )
    return completed.stdout


class AppleMailReader:
    def __init__(
        self,
        *,
        execute_jxa: Callable[[str, float], str] = run_jxa_selection,
        timeout_seconds: float = 5.0,
        max_output_bytes: int = MAX_SELECTION_OUTPUT_BYTES,
    ) -> None:
        self._execute_jxa = execute_jxa
        self._timeout_seconds = timeout_seconds
        self._max_output_bytes = max_output_bytes

    def selected_mail(self) -> SelectedMail:
        try:
            output = self._execute_jxa(SELECTION_JXA, self._timeout_seconds)
            if len(output.encode("utf-8")) > self._max_output_bytes:
                raise OverflowError("selection output too large")
            payload = json.loads(output)
            if not isinstance(payload, list):
                raise TypeError("selection must be an array")
        except MailSelectionError:
            raise
        except Exception as exception:
            raise MailSelectionError(
                RedactedError.from_exception(ErrorCode.INVALID_RESPONSE, exception)
            ) from None

        if not payload:
            raise MailSelectionError(RedactedError(ErrorCode.NO_SELECTION, "SelectionCount"))
        is_conversation = len(payload) > 1
        if is_conversation:
            canonical_subjects = {
                _canonical_conversation_subject(str(row.get("subject", "")))
                for row in payload
                if isinstance(row, dict)
            }
            if len(canonical_subjects) != 1 or not next(iter(canonical_subjects), ""):
                raise MailSelectionError(
                    RedactedError(ErrorCode.MULTIPLE_SELECTION, "SelectionCount")
                )
            try:
                row = max(
                    payload,
                    key=lambda item: datetime.fromisoformat(
                        str(item["received_at"]).replace("Z", "+00:00")
                    ),
                )
            except Exception as exception:
                raise MailSelectionError(
                    RedactedError.from_exception(ErrorCode.INVALID_RESPONSE, exception)
                ) from None
        else:
            row = payload[0]

        try:
            if not isinstance(row, dict):
                raise TypeError("selected row must be an object")
            rfc_message_id = str(row["rfc_message_id"])
            if not rfc_message_id.strip():
                raise MailSelectionError(
                    RedactedError(ErrorCode.MISSING_MESSAGE_ID, "MissingMessageId")
                )
            received_at = datetime.fromisoformat(str(row["received_at"]).replace("Z", "+00:00"))
            return SelectedMail(
                apple_mail_id=str(row["apple_mail_id"]),
                rfc_message_id=rfc_message_id,
                subject=(
                    _strip_conversation_prefixes(str(row["subject"]))
                    if is_conversation
                    else str(row["subject"])
                ),
                sender_display=str(row["sender_display"]),
                received_at=received_at,
            )
        except MailSelectionError:
            raise
        except Exception as exception:
            raise MailSelectionError(
                RedactedError.from_exception(ErrorCode.INVALID_RESPONSE, exception)
            ) from None


def _canonical_conversation_subject(subject: str) -> str:
    return _strip_conversation_prefixes(subject).casefold()


def _strip_conversation_prefixes(subject: str) -> str:
    without_prefixes = CONVERSATION_PREFIX.sub("", subject.strip())
    return " ".join(without_prefixes.split())
