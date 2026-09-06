"""Console entry point used directly and by the Raycast Script Command."""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Callable, Sequence
from contextlib import suppress

from apple_mail_todoist.apple_mail import AppleMailReader
from apple_mail_todoist.domain import CaptureOutcome, ErrorCode, OutcomeKind
from apple_mail_todoist.reconciliation import ReconciliationStore
from apple_mail_todoist.service import CaptureService
from apple_mail_todoist.todoist_cli import TodoistCliClient

SAFE_NOTIFICATIONS = {
    "Todoist task created",
    "Todoist task already exists",
    "Select one message in Apple Mail",
    "Select only one message in Apple Mail",
    "Selected message has no stable Mail link",
    "Sign in to Todoist with td first",
    "Todoist rejected the task",
    "Todoist task was not created",
    "Todoist delivery needs reconciliation",
}


def notify_macos(message: str) -> None:
    """Show only an allowlisted result through Notification Center."""
    safe_message = message if message in SAFE_NOTIFICATIONS else "Todoist task was not created"
    script = f'display notification "{safe_message}" with title "Apple Mail to Todoist"'
    with suppress(OSError, subprocess.SubprocessError):
        subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=2.0,
        )


def build_service() -> CaptureService:
    return CaptureService(
        AppleMailReader(),
        TodoistCliClient(),
        ReconciliationStore(),
    )


def render_outcome(outcome: CaptureOutcome) -> tuple[str, int]:
    if outcome.kind is OutcomeKind.CREATED:
        return "Todoist task created", 0
    if outcome.kind is OutcomeKind.EXISTING:
        return "Todoist task already exists", 0
    if outcome.kind is OutcomeKind.RECONCILIATION_NEEDED:
        return "Todoist delivery needs reconciliation", 3
    code = outcome.error.code if outcome.error else ErrorCode.INTERNAL_ERROR
    messages = {
        ErrorCode.NO_SELECTION: "Select one message in Apple Mail",
        ErrorCode.MULTIPLE_SELECTION: "Select only one message in Apple Mail",
        ErrorCode.MISSING_MESSAGE_ID: "Selected message has no stable Mail link",
        ErrorCode.CREDENTIAL_MISSING: "Sign in to Todoist with td first",
        ErrorCode.API_REJECTED: "Todoist rejected the task",
    }
    return messages.get(code, "Todoist task was not created"), 2


def main(
    argv: Sequence[str] | None = None,
    *,
    service_factory: Callable[[], object] = build_service,
    output: Callable[[str], None] = print,
    notifier: Callable[[str], None] = notify_macos,
) -> int:
    parser = argparse.ArgumentParser(prog="apple-mail-todoist")
    parser.add_argument("command", choices=("capture", "capture-notify"))
    args = parser.parse_args(argv)

    outcome = service_factory().capture()  # type: ignore[attr-defined]
    message, exit_code = render_outcome(outcome)
    if args.command == "capture-notify":
        notifier(message)
    else:
        output(message)
    return exit_code
