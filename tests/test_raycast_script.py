import os
import subprocess
import time
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts/raycast/create-todoist-task-from-mail.sh"


def run_script(
    tmp_path: Path, message: str, exit_code: int
) -> tuple[subprocess.CompletedProcess[str], Path]:
    fake = tmp_path / "apple-mail-todoist"
    marker = tmp_path / "called"
    fake.write_text(
        "#!/bin/sh\n"
        f"printf '%s' \"$1:{message}:{exit_code}\" > '{marker}'\n"
        f"exit {exit_code}\n"
    )
    fake.chmod(0o700)
    environment = {**os.environ, "APPLE_MAIL_TODOIST_CLI": str(fake)}
    result = subprocess.run(
        [str(SCRIPT)], capture_output=True, text=True, check=False, env=environment
    )
    deadline = time.monotonic() + 5
    while not marker.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    return result, marker


def test_script_has_silent_raycast_metadata_and_no_focus_changing_commands() -> None:
    source = SCRIPT.read_text()
    assert "# @raycast.schemaVersion 1" in source
    assert "# @raycast.title Create Todoist Task from Mail" in source
    assert "# @raycast.mode silent" in source
    assert " open " not in f" {source.lower()} "
    assert "activate" not in source.lower()
    assert os.access(SCRIPT, os.X_OK)


def test_script_returns_immediately_and_runs_notifying_capture_in_background(
    tmp_path: Path,
) -> None:
    result, marker = run_script(tmp_path, "ignored", 0)

    assert result.returncode == 0
    assert result.stdout.strip() == "Creating Todoist task"
    assert result.stderr == ""
    assert marker.read_text() == "capture-notify:ignored:0"
