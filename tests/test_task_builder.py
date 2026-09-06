from dataclasses import fields
from datetime import UTC, datetime

from apple_mail_todoist.domain import SelectedMail
from apple_mail_todoist.task_builder import build_task


def test_builds_fixed_inbox_task_with_sender_date_link_and_mail_label() -> None:
    selected = SelectedMail(
        apple_mail_id="synthetic-local-id",
        rfc_message_id="<synthetic-123@example.invalid>",
        subject="Synthetic project question",
        sender_display="Example Sender",
        received_at=datetime(2026, 9, 6, 10, tzinfo=UTC),
    )

    task = build_task(selected)

    assert task.content == "Reply to: Synthetic project question"
    assert task.description == (
        "From: Example Sender\n"
        "Received: 6 September 2026\n"
        "[Open in Apple Mail](message://%3Csynthetic-123%40example.invalid%3E)"
    )
    assert task.labels == ("mail",)
    assert {field.name for field in fields(task)} == {"content", "description", "labels"}


def test_untrusted_mail_fields_cannot_inject_extra_lines() -> None:
    selected = SelectedMail(
        apple_mail_id="synthetic-local-id",
        rfc_message_id="synthetic@example.invalid",
        subject="Question\nproject_id: private",
        sender_display="Sender\r\nlabels: admin",
        received_at=datetime(2026, 9, 6, 10, tzinfo=UTC),
    )

    task = build_task(selected)

    assert task.content == "Reply to: Question project_id: private"
    assert task.description.count("\n") == 2
    assert "From: Sender labels: admin" in task.description
