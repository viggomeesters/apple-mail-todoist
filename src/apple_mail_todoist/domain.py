"""Pure domain contracts shared by platform and network adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import Protocol
from uuid import uuid4


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")


@dataclass(frozen=True, slots=True)
class SelectedMail:
    """Minimal immutable snapshot of one selected Apple Mail message."""

    apple_mail_id: str
    rfc_message_id: str
    subject: str
    sender_display: str
    received_at: datetime

    def __post_init__(self) -> None:
        for name in ("apple_mail_id", "rfc_message_id", "subject", "sender_display"):
            _require_text(name, getattr(self, name))
        if self.received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class TaskDraft:
    """Explicit Todoist fields produced by the deterministic composer."""

    content: str
    description: str
    labels: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text("content", self.content)
        _require_text("description", self.description)
        if not self.labels or any(not label.strip() for label in self.labels):
            raise ValueError("labels must contain non-empty values")


@dataclass(frozen=True, slots=True)
class RequestIdentity:
    """Stable source fingerprint paired with one logical request UUID."""

    source_fingerprint: str
    request_id: str

    @classmethod
    def from_source(cls, normalized_source: str) -> RequestIdentity:
        _require_text("normalized_source", normalized_source)
        fingerprint = sha256(
            f"apple-mail-todoist:v1\0{normalized_source}".encode()
        ).hexdigest()
        return cls(source_fingerprint=fingerprint, request_id=str(uuid4()))


class OutcomeKind(StrEnum):
    CREATED = "created"
    EXISTING = "existing"
    SAFE_FAILURE = "safe_failure"
    RECONCILIATION_NEEDED = "reconciliation_needed"


class ErrorCode(StrEnum):
    NO_SELECTION = "no_selection"
    MULTIPLE_SELECTION = "multiple_selection"
    MISSING_MESSAGE_ID = "missing_message_id"
    MAIL_UNAVAILABLE = "mail_unavailable"
    CREDENTIAL_MISSING = "credential_missing"
    API_REJECTED = "api_rejected"
    INVALID_RESPONSE = "invalid_response"
    DELIVERY_UNCERTAIN = "delivery_uncertain"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True, slots=True)
class RedactedError:
    """Safe diagnostic that never retains exception text or payloads."""

    code: ErrorCode
    cause_type: str

    @classmethod
    def from_exception(cls, code: ErrorCode, exception: BaseException) -> RedactedError:
        return cls(code=code, cause_type=type(exception).__name__)


@dataclass(frozen=True, slots=True)
class CaptureOutcome:
    kind: OutcomeKind
    todoist_task_id: str | None = None
    error: RedactedError | None = None

    def __post_init__(self) -> None:
        if self.kind in {OutcomeKind.CREATED, OutcomeKind.EXISTING}:
            _require_text("todoist_task_id", self.todoist_task_id or "")
            if self.error is not None:
                raise ValueError("successful outcomes cannot contain an error")
        elif self.todoist_task_id is not None or self.error is None:
            raise ValueError("failure outcomes require only a redacted error")

    @classmethod
    def created(cls, task_id: str) -> CaptureOutcome:
        return cls(kind=OutcomeKind.CREATED, todoist_task_id=task_id)

    @classmethod
    def existing(cls, task_id: str) -> CaptureOutcome:
        return cls(kind=OutcomeKind.EXISTING, todoist_task_id=task_id)

    @classmethod
    def failure(cls, error: RedactedError) -> CaptureOutcome:
        return cls(kind=OutcomeKind.SAFE_FAILURE, error=error)

    @classmethod
    def uncertain(cls, error: RedactedError) -> CaptureOutcome:
        return cls(kind=OutcomeKind.RECONCILIATION_NEEDED, error=error)


class MailSelectionPort(Protocol):
    def selected_mail(self) -> SelectedMail: ...


class TodoistPort(Protocol):
    def create_task(self, task: TaskDraft, identity: RequestIdentity) -> str: ...


class HudPort(Protocol):
    def show(self, outcome: CaptureOutcome) -> None: ...
