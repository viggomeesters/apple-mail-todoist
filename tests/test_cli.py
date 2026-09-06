from apple_mail_todoist.cli import main
from apple_mail_todoist.domain import CaptureOutcome, ErrorCode, RedactedError


class Service:
    def __init__(self, outcome: CaptureOutcome) -> None:
        self.outcome = outcome

    def capture(self) -> CaptureOutcome:
        return self.outcome


def test_capture_cli_emits_only_quiet_success_confirmation() -> None:
    output: list[str] = []
    code = main(
        ["capture"],
        service_factory=lambda: Service(CaptureOutcome.created("6XSynthetic")),
        output=output.append,
    )

    assert code == 0
    assert output == ["Todoist task created"]


def test_capture_cli_renders_safe_selection_hint() -> None:
    output: list[str] = []
    outcome = CaptureOutcome.failure(RedactedError(ErrorCode.NO_SELECTION, "Synthetic"))

    code = main(["capture"], service_factory=lambda: Service(outcome), output=output.append)

    assert code == 2
    assert output == ["Select one message in Apple Mail"]


def test_capture_notify_sends_safe_result_without_stdout() -> None:
    output: list[str] = []
    notifications: list[str] = []

    code = main(
        ["capture-notify"],
        service_factory=lambda: Service(CaptureOutcome.created("6XSynthetic")),
        output=output.append,
        notifier=notifications.append,
    )

    assert code == 0
    assert output == []
    assert notifications == ["Todoist task created"]
