"""One-shot orchestration for the Mail-to-Todoist capture workflow."""

from __future__ import annotations

from contextlib import suppress

from apple_mail_todoist.apple_mail import MailSelectionError
from apple_mail_todoist.domain import (
    CaptureOutcome,
    ErrorCode,
    MailSelectionPort,
    RedactedError,
    RequestIdentity,
    TodoistPort,
)
from apple_mail_todoist.mail_link import normalize_rfc_message_id
from apple_mail_todoist.reconciliation import (
    DeliveryState,
    ReconciliationError,
    ReconciliationStore,
)
from apple_mail_todoist.task_builder import build_task
from apple_mail_todoist.todoist_cli import TodoistCliError


class CaptureService:
    def __init__(
        self,
        mail: MailSelectionPort,
        todoist: TodoistPort,
        reconciliation: ReconciliationStore,
    ) -> None:
        self._mail = mail
        self._todoist = todoist
        self._reconciliation = reconciliation

    def capture(self) -> CaptureOutcome:
        try:
            selected = self._mail.selected_mail()
            source = normalize_rfc_message_id(selected.rfc_message_id)
            task = build_task(selected)
            proposed = RequestIdentity.from_source(source)
            begin = self._reconciliation.begin(proposed)
        except MailSelectionError as exception:
            return CaptureOutcome.failure(exception.error)
        except ReconciliationError as exception:
            return CaptureOutcome.failure(exception.error)
        except Exception as exception:
            return CaptureOutcome.failure(
                RedactedError.from_exception(ErrorCode.INVALID_RESPONSE, exception)
            )

        if not begin.created:
            if begin.record.state is DeliveryState.CONFIRMED:
                return CaptureOutcome.existing(begin.record.todoist_task_id or "")
            return CaptureOutcome.uncertain(
                RedactedError(ErrorCode.DELIVERY_UNCERTAIN, "ExistingDeliveryClaim")
            )

        identity = RequestIdentity(begin.record.source_fingerprint, begin.record.request_id)
        try:
            task_id = self._todoist.create_task(task, identity)
        except TodoistCliError as exception:
            if exception.delivery_uncertain:
                self._mark_uncertain(identity.source_fingerprint)
                return CaptureOutcome.uncertain(exception.error)
            self._abandon(identity.source_fingerprint)
            return CaptureOutcome.failure(exception.error)
        except Exception as exception:
            self._mark_uncertain(identity.source_fingerprint)
            return CaptureOutcome.uncertain(
                RedactedError.from_exception(ErrorCode.DELIVERY_UNCERTAIN, exception)
            )

        try:
            self._reconciliation.confirm(identity.source_fingerprint, task_id)
        except Exception as exception:
            self._mark_uncertain(identity.source_fingerprint)
            return CaptureOutcome.uncertain(
                RedactedError.from_exception(ErrorCode.DELIVERY_UNCERTAIN, exception)
            )
        return CaptureOutcome.created(task_id)

    def _abandon(self, fingerprint: str) -> None:
        with suppress(ReconciliationError):
            self._reconciliation.abandon(fingerprint)

    def _mark_uncertain(self, fingerprint: str) -> None:
        with suppress(ReconciliationError):
            self._reconciliation.mark_uncertain(fingerprint)
