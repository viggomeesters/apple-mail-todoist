from datetime import UTC, datetime
from pathlib import Path

import pytest

from apple_mail_todoist.domain import (
    ErrorCode,
    OutcomeKind,
    RedactedError,
    RequestIdentity,
    SelectedMail,
    TaskDraft,
)
from apple_mail_todoist.reconciliation import ReconciliationStore
from apple_mail_todoist.service import CaptureService
from apple_mail_todoist.todoist_cli import TodoistCliError


class Mail:
    def __init__(self) -> None:
        self.reads = 0

    def selected_mail(self) -> SelectedMail:
        self.reads += 1
        return SelectedMail(
            "local-id",
            "synthetic@example.invalid",
            "Synthetic question",
            "Example Sender",
            datetime(2026, 9, 6, 10, tzinfo=UTC),
        )


class Todoist:
    def __init__(self, error: TodoistCliError | None = None) -> None:
        self.calls: list[tuple[TaskDraft, RequestIdentity]] = []
        self.error = error

    def create_task(self, task: TaskDraft, identity: RequestIdentity) -> str:
        self.calls.append((task, identity))
        if self.error:
            self.error.identity = identity
            raise self.error
        return "6XCreated"


def service(tmp_path: Path, *, todoist: Todoist | None = None):
    mail = Mail()
    todoist = todoist or Todoist()
    store = ReconciliationStore(tmp_path / "state.json")
    return CaptureService(mail, todoist, store), mail, todoist, store


def test_success_then_replay_creates_exactly_one_todoist_task(tmp_path: Path) -> None:
    capture, mail, todoist, _store = service(tmp_path)

    first = capture.capture()
    second = capture.capture()

    assert first.kind is OutcomeKind.CREATED
    assert second.kind is OutcomeKind.EXISTING
    assert second.todoist_task_id == "6XCreated"
    assert mail.reads == 2
    assert len(todoist.calls) == 1


def test_missing_cli_auth_is_safe_and_releases_claim_for_retry(tmp_path: Path) -> None:
    missing = TodoistCliError(
        RedactedError(ErrorCode.CREDENTIAL_MISSING, "Synthetic"),
        RequestIdentity.from_source("placeholder@example.invalid"),
        delivery_uncertain=False,
    )
    todoist = Todoist(missing)
    capture, _mail, _todoist, store = service(tmp_path, todoist=todoist)

    outcome = capture.capture()

    assert outcome.kind is OutcomeKind.SAFE_FAILURE
    assert outcome.error and outcome.error.code is ErrorCode.CREDENTIAL_MISSING
    assert len(todoist.calls) == 1
    assert store.begin(RequestIdentity.from_source("synthetic@example.invalid")).created is True


@pytest.mark.parametrize("uncertain", [False, True])
def test_api_failure_distinguishes_safe_from_uncertain_and_never_reposts(
    tmp_path: Path, uncertain: bool
) -> None:
    error = TodoistCliError(
        RedactedError(
            ErrorCode.DELIVERY_UNCERTAIN if uncertain else ErrorCode.API_REJECTED,
            "Synthetic",
        ),
        RequestIdentity.from_source("placeholder@example.invalid"),
        delivery_uncertain=uncertain,
    )
    todoist = Todoist(error)
    capture, _mail, _todoist, _store = service(tmp_path, todoist=todoist)

    first = capture.capture()
    second = capture.capture()

    assert first.kind is (
        OutcomeKind.RECONCILIATION_NEEDED if uncertain else OutcomeKind.SAFE_FAILURE
    )
    assert second.kind is (
        OutcomeKind.RECONCILIATION_NEEDED if uncertain else OutcomeKind.SAFE_FAILURE
    )
    assert len(todoist.calls) == (1 if uncertain else 2)
