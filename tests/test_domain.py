import json
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from apple_mail_todoist.domain import (
    CaptureOutcome,
    ErrorCode,
    OutcomeKind,
    RedactedError,
    RequestIdentity,
    SelectedMail,
    TaskDraft,
)

FIXTURE = Path(__file__).parent / "fixtures" / "selected-mail.json"


def test_selected_mail_is_immutable_and_rejects_missing_identity() -> None:
    mail = SelectedMail(
        apple_mail_id="synthetic-local-id",
        rfc_message_id="synthetic-123@example.invalid",
        subject="Synthetic project question",
        sender_display="Example Sender <sender@example.invalid>",
        received_at=datetime(2026, 9, 6, 10, tzinfo=UTC),
    )

    assert mail.subject == "Synthetic project question"
    with pytest.raises(AttributeError):
        mail.subject = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="rfc_message_id"):
        SelectedMail(
            apple_mail_id="synthetic-local-id",
            rfc_message_id=" ",
            subject="Synthetic project question",
            sender_display="Example Sender",
            received_at=datetime(2026, 9, 6, 10, tzinfo=UTC),
        )


def test_capture_contracts_are_minimal_typed_and_redacted() -> None:
    task = TaskDraft(
        content="Reply to: Synthetic project question",
        description="From: Example Sender\n[Open in Apple Mail](message://synthetic)",
        labels=("mail",),
    )
    identity = RequestIdentity.from_source("synthetic-123@example.invalid")
    outcome = CaptureOutcome.created("synthetic-task-id")
    secret = "not-a-real-secret-value"
    error = RedactedError.from_exception(ErrorCode.INTERNAL_ERROR, RuntimeError(secret))

    assert {field.name for field in fields(task)} == {"content", "description", "labels"}
    assert UUID(identity.request_id).version == 4
    assert len(identity.source_fingerprint) == 64
    assert outcome == CaptureOutcome(
        kind=OutcomeKind.CREATED,
        todoist_task_id="synthetic-task-id",
        error=None,
    )
    assert secret not in repr(error)
    assert error.cause_type == "RuntimeError"


def test_synthetic_fixture_contains_no_live_identity_or_extra_mail_data() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert fixture["rfc_message_id"].endswith("@example.invalid")
    assert set(fixture) == {
        "apple_mail_id",
        "rfc_message_id",
        "subject",
        "sender_display",
        "received_at",
    }
    assert "body" not in fixture
    assert "attachment" not in fixture
