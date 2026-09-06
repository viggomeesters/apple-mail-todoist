"""Bounded adapter for the official Todoist ``td`` command-line client."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from apple_mail_todoist.domain import ErrorCode, RedactedError, RequestIdentity, TaskDraft

DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_CANDIDATES = (Path("/opt/homebrew/bin/td"), Path("/usr/local/bin/td"))

Runner = Callable[..., subprocess.CompletedProcess[str]]


class TodoistCliError(RuntimeError):
    """Redacted CLI failure tied to the attempted logical request."""

    def __init__(
        self,
        error: RedactedError,
        identity: RequestIdentity,
        *,
        delivery_uncertain: bool,
    ) -> None:
        self.error = error
        self.identity = identity
        self.delivery_uncertain = delivery_uncertain
        super().__init__(error.code.value)


def resolve_td_executable() -> str | None:
    override = os.environ.get("APPLE_MAIL_TODOIST_TD", "").strip()
    if override and Path(override).is_file() and os.access(override, os.X_OK):
        return override
    for candidate in DEFAULT_CANDIDATES:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return shutil.which("td")


class TodoistCliClient:
    def __init__(
        self,
        *,
        executable: str | None = None,
        run: Runner = subprocess.run,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._executable = executable or resolve_td_executable()
        self._run = run
        self._timeout_seconds = timeout_seconds

    def create_task(self, task: TaskDraft, identity: RequestIdentity) -> str:
        if not self._executable:
            self._raise(
                ErrorCode.CREDENTIAL_MISSING,
                identity,
                FileNotFoundError("td unavailable"),
                delivery_uncertain=False,
            )

        auth_command = (
            self._executable,
            "auth",
            "status",
            "--json",
            "--no-spinner",
        )
        try:
            auth = self._execute(auth_command)
        except (OSError, subprocess.SubprocessError) as exception:
            self._raise(
                ErrorCode.CREDENTIAL_MISSING,
                identity,
                exception,
                delivery_uncertain=False,
            )
        if auth.returncode != 0:
            self._raise(
                ErrorCode.CREDENTIAL_MISSING,
                identity,
                RuntimeError("td authentication unavailable"),
                delivery_uncertain=False,
            )

        create_command = (
            self._executable,
            "task",
            "add",
            task.content,
            "--description",
            task.description,
            "--labels",
            ",".join(task.labels),
            "--json",
            "--no-spinner",
        )
        try:
            created = self._execute(create_command)
        except (OSError, subprocess.SubprocessError) as exception:
            self._raise(
                ErrorCode.DELIVERY_UNCERTAIN,
                identity,
                exception,
                delivery_uncertain=True,
            )
        if created.returncode != 0:
            self._raise(
                ErrorCode.DELIVERY_UNCERTAIN,
                identity,
                RuntimeError("td task creation failed"),
                delivery_uncertain=True,
            )
        try:
            payload = json.loads(created.stdout)
            task_id = payload["id"]
            if not isinstance(task_id, (str, int)) or not str(task_id).strip():
                raise ValueError("invalid task id")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exception:
            self._raise(
                ErrorCode.INVALID_RESPONSE,
                identity,
                exception,
                delivery_uncertain=True,
            )
        return str(task_id)

    def _execute(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return self._run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=self._timeout_seconds,
        )

    @staticmethod
    def _raise(
        code: ErrorCode,
        identity: RequestIdentity,
        exception: BaseException,
        *,
        delivery_uncertain: bool,
    ) -> None:
        raise TodoistCliError(
            RedactedError.from_exception(code, exception),
            identity,
            delivery_uncertain=delivery_uncertain,
        ) from None
