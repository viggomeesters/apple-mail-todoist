import json
import re
import subprocess
from datetime import UTC, datetime

import pytest

from apple_mail_todoist.apple_mail import (
    SELECTION_JXA,
    AppleMailReader,
    MailSelectionError,
    run_jxa_selection,
)
from apple_mail_todoist.domain import ErrorCode, SelectedMail


def test_reader_returns_one_minimal_selected_mail_from_constant_read_only_jxa() -> None:
    calls: list[tuple[str, float]] = []

    def execute(script: str, timeout: float) -> str:
        calls.append((script, timeout))
        return json.dumps(
            [
                {
                    "apple_mail_id": "synthetic-local-id",
                    "rfc_message_id": "synthetic-123@example.invalid",
                    "subject": "Synthetic project question",
                    "sender_display": "Example Sender <sender@example.invalid>",
                    "received_at": "2026-09-06T10:00:00Z",
                }
            ]
        )

    reader = AppleMailReader(execute_jxa=execute, timeout_seconds=2.5)

    assert reader.selected_mail() == SelectedMail(
        apple_mail_id="synthetic-local-id",
        rfc_message_id="synthetic-123@example.invalid",
        subject="Synthetic project question",
        sender_display="Example Sender <sender@example.invalid>",
        received_at=datetime(2026, 9, 6, 10, tzinfo=UTC),
    )
    assert calls == [(SELECTION_JXA, 2.5)]


def test_reader_uses_newest_message_from_one_selected_conversation() -> None:
    older = {
        "apple_mail_id": "synthetic-older",
        "rfc_message_id": "older@example.invalid",
        "subject": "Synthetic project question",
        "sender_display": "First Example Sender",
        "received_at": "2026-09-05T10:00:00Z",
    }
    newest = {
        "apple_mail_id": "synthetic-newest",
        "rfc_message_id": "newest@example.invalid",
        "subject": "RE: Synthetic project question",
        "sender_display": "Latest Example Sender",
        "received_at": "2026-09-06T10:00:00Z",
    }
    middle = {
        "apple_mail_id": "synthetic-middle",
        "rfc_message_id": "middle@example.invalid",
        "subject": "Re: Re: Synthetic project question",
        "sender_display": "Middle Example Sender",
        "received_at": "2026-09-05T14:00:00Z",
    }

    reader = AppleMailReader(
        execute_jxa=lambda _script, _timeout: json.dumps([older, newest, middle])
    )

    selected = reader.selected_mail()

    assert selected.apple_mail_id == "synthetic-newest"
    assert selected.rfc_message_id == "newest@example.invalid"
    assert selected.subject == "Synthetic project question"


def test_reader_still_rejects_multiple_unrelated_messages() -> None:
    rows = [
        {
            "apple_mail_id": f"synthetic-{number}",
            "rfc_message_id": f"synthetic-{number}@example.invalid",
            "subject": subject,
            "sender_display": "Example Sender",
            "received_at": f"2026-09-0{number}T10:00:00Z",
        }
        for number, subject in ((5, "First subject"), (6, "Second subject"))
    ]
    reader = AppleMailReader(execute_jxa=lambda _script, _timeout: json.dumps(rows))

    with pytest.raises(MailSelectionError) as caught:
        reader.selected_mail()

    assert caught.value.error.code is ErrorCode.MULTIPLE_SELECTION


def test_selection_program_has_no_mail_mutation_surface() -> None:
    lowered = SELECTION_JXA.lower()
    for mutation in (r"\bdelete\b", r"\barchive\b", r"\.move\(", r"\.send\(", r"flagged\s*="):
        assert re.search(mutation, lowered) is None
    assert "message.source" not in lowered
    assert "message.content" not in lowered


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ([], ErrorCode.NO_SELECTION),
        ([{}, {}], ErrorCode.MULTIPLE_SELECTION),
        ({"not": "an array"}, ErrorCode.INVALID_RESPONSE),
        ("not json", ErrorCode.INVALID_RESPONSE),
    ],
)
def test_reader_fails_closed_for_selection_shape(payload: object, code: ErrorCode) -> None:
    output = payload if isinstance(payload, str) else json.dumps(payload)
    reader = AppleMailReader(execute_jxa=lambda _script, _timeout: output)

    with pytest.raises(MailSelectionError) as caught:
        reader.selected_mail()

    assert caught.value.error.code is code
    assert output not in repr(caught.value.error)


def test_reader_reports_missing_message_id_and_oversized_output() -> None:
    row = {
        "apple_mail_id": "synthetic-local-id",
        "rfc_message_id": "",
        "subject": "Synthetic subject",
        "sender_display": "Example Sender",
        "received_at": "2026-09-06T10:00:00Z",
    }
    with pytest.raises(MailSelectionError) as missing:
        AppleMailReader(execute_jxa=lambda _script, _timeout: json.dumps([row])).selected_mail()
    assert missing.value.error.code is ErrorCode.MISSING_MESSAGE_ID

    with pytest.raises(MailSelectionError) as oversized:
        AppleMailReader(
            execute_jxa=lambda _script, _timeout: "[]" * 20,
            max_output_bytes=8,
        ).selected_mail()
    assert oversized.value.error.code is ErrorCode.INVALID_RESPONSE


def test_actual_runner_redacts_timeout_and_process_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired("osascript", 1, stderr="private mail detail")

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(MailSelectionError) as timed_out:
        run_jxa_selection(SELECTION_JXA, 1)
    assert timed_out.value.error.code is ErrorCode.MAIL_UNAVAILABLE
    assert "private mail detail" not in repr(timed_out.value.error)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="private mail detail"
        ),
    )
    with pytest.raises(MailSelectionError) as failed:
        run_jxa_selection(SELECTION_JXA, 1)
    assert failed.value.error.code is ErrorCode.MAIL_UNAVAILABLE
    assert "private mail detail" not in repr(failed.value.error)
