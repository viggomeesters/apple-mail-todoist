import json
import subprocess
from collections.abc import Sequence

import pytest

from apple_mail_todoist.domain import ErrorCode, RequestIdentity, TaskDraft
from apple_mail_todoist.todoist_cli import TodoistCliClient, TodoistCliError


def identity() -> RequestIdentity:
    return RequestIdentity.from_source("synthetic@example.invalid")


def draft() -> TaskDraft:
    return TaskDraft(
        content="Reply to: Synthetic question",
        description="From: Example Sender\n[Open in Apple Mail](message://synthetic%40example.invalid)",
        labels=("mail",),
    )


def test_cli_creates_exact_structured_task_without_due_date() -> None:
    calls: list[tuple[Sequence[str], dict[str, object]]] = []

    def run(command: Sequence[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        if "auth" in command:
            return subprocess.CompletedProcess(command, 0, '{"source":"secure-store"}', "")
        return subprocess.CompletedProcess(command, 0, json.dumps({"id": "6XCreated"}), "")

    task_id = TodoistCliClient(executable="/synthetic/td", run=run).create_task(
        draft(), identity()
    )

    assert task_id == "6XCreated"
    assert calls[0][0] == ("/synthetic/td", "auth", "status", "--json", "--no-spinner")
    create = calls[1][0]
    assert create == (
        "/synthetic/td",
        "task",
        "add",
        "Reply to: Synthetic question",
        "--description",
        "From: Example Sender\n[Open in Apple Mail](message://synthetic%40example.invalid)",
        "--labels",
        "mail",
        "--json",
        "--no-spinner",
    )
    assert "--due" not in create
    assert calls[1][1]["timeout"] == 20.0
    assert calls[1][1]["capture_output"] is True


def test_missing_cli_authentication_is_definitive_and_redacted() -> None:
    secret = "synthetic-secret-never-print"

    def run(command: Sequence[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, secret, secret)

    with pytest.raises(TodoistCliError) as caught:
        TodoistCliClient(executable="/synthetic/td", run=run).create_task(draft(), identity())

    assert caught.value.error.code is ErrorCode.CREDENTIAL_MISSING
    assert caught.value.delivery_uncertain is False
    assert secret not in str(caught.value)
    assert secret not in repr(caught.value.error)


def test_create_timeout_is_delivery_uncertain_and_redacted() -> None:
    calls = 0

    def run(command: Sequence[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return subprocess.CompletedProcess(command, 0, "{}", "")
        raise subprocess.TimeoutExpired(command, 20, output="private mail")

    with pytest.raises(TodoistCliError) as caught:
        TodoistCliClient(executable="/synthetic/td", run=run).create_task(draft(), identity())

    assert caught.value.error.code is ErrorCode.DELIVERY_UNCERTAIN
    assert caught.value.delivery_uncertain is True
    assert "private mail" not in str(caught.value)


def test_invalid_success_json_is_delivery_uncertain() -> None:
    responses = iter(
        (
            subprocess.CompletedProcess(("td",), 0, "{}", ""),
            subprocess.CompletedProcess(("td",), 0, "not-json", ""),
        )
    )

    with pytest.raises(TodoistCliError) as caught:
        client = TodoistCliClient(
            executable="/synthetic/td",
            run=lambda *_args, **_kwargs: next(responses),
        )
        client.create_task(draft(), identity())

    assert caught.value.error.code is ErrorCode.INVALID_RESPONSE
    assert caught.value.delivery_uncertain is True
