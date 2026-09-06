"""Minimal, user-only delivery state for safe Todoist retries."""

from __future__ import annotations

import fcntl
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from apple_mail_todoist.domain import ErrorCode, RedactedError, RequestIdentity

SCHEMA = "apple-mail-todoist.reconciliation.v1"
DEFAULT_PATH = (
    Path.home() / "Library" / "Application Support" / "apple-mail-todoist" / "reconciliation.json"
)


class DeliveryState(StrEnum):
    PENDING = "pending"
    UNCERTAIN = "uncertain"
    CONFIRMED = "confirmed"


@dataclass(frozen=True, slots=True)
class DeliveryRecord:
    source_fingerprint: str
    request_id: str
    state: DeliveryState
    created_at: str
    updated_at: str
    todoist_task_id: str | None = None


@dataclass(frozen=True, slots=True)
class BeginResult:
    record: DeliveryRecord
    created: bool


class ReconciliationError(RuntimeError):
    def __init__(self, error: RedactedError) -> None:
        self.error = error
        super().__init__("reconciliation_state_error")


class ReconciliationStore:
    def __init__(self, path: Path = DEFAULT_PATH) -> None:
        self.path = path
        self._lock_path = path.with_suffix(path.suffix + ".lock")

    def begin(self, identity: RequestIdentity) -> BeginResult:
        with self._locked() as data:
            raw = data["records"].get(identity.source_fingerprint)
            if raw is not None:
                return BeginResult(self._decode(raw, identity.source_fingerprint), False)
            now = self._now()
            record = DeliveryRecord(
                source_fingerprint=identity.source_fingerprint,
                request_id=identity.request_id,
                state=DeliveryState.PENDING,
                created_at=now,
                updated_at=now,
            )
            data["records"][identity.source_fingerprint] = self._encode(record)
            self._write(data)
            return BeginResult(record, True)

    def confirm(self, source_fingerprint: str, todoist_task_id: str) -> DeliveryRecord:
        if not todoist_task_id.strip():
            raise ValueError("todoist_task_id must be non-empty")
        return self._transition(
            source_fingerprint,
            DeliveryState.CONFIRMED,
            todoist_task_id=todoist_task_id,
        )

    def mark_uncertain(self, source_fingerprint: str) -> DeliveryRecord:
        return self._transition(source_fingerprint, DeliveryState.UNCERTAIN)

    def permit_retry(self, source_fingerprint: str) -> DeliveryRecord:
        with self._locked() as data:
            record = self._existing(data, source_fingerprint)
            if record.state is not DeliveryState.UNCERTAIN:
                self._fail(ValueError("only uncertain delivery can be retried"))
            updated = replace(record, state=DeliveryState.PENDING, updated_at=self._now())
            data["records"][source_fingerprint] = self._encode(updated)
            self._write(data)
            return updated

    def abandon(self, source_fingerprint: str) -> None:
        """Release a claim only when delivery definitively did not happen."""
        with self._locked() as data:
            record = self._existing(data, source_fingerprint)
            if record.state is not DeliveryState.PENDING:
                self._fail(ValueError("protected delivery state cannot be abandoned"))
            del data["records"][source_fingerprint]
            self._write(data)

    def _transition(
        self,
        source_fingerprint: str,
        state: DeliveryState,
        *,
        todoist_task_id: str | None = None,
    ) -> DeliveryRecord:
        with self._locked() as data:
            record = self._existing(data, source_fingerprint)
            updated = replace(
                record,
                state=state,
                updated_at=self._now(),
                todoist_task_id=todoist_task_id,
            )
            data["records"][source_fingerprint] = self._encode(updated)
            self._write(data)
            return updated

    @contextmanager
    def _locked(self) -> Iterator[dict[str, Any]]:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.path.parent, 0o700)
        descriptor = os.open(self._lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        os.chmod(self._lock_path, 0o600)
        with os.fdopen(descriptor, "r+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield self._read()
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema": SCHEMA, "records": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if (
                not isinstance(data, dict)
                or data.get("schema") != SCHEMA
                or not isinstance(data.get("records"), dict)
            ):
                raise ValueError("invalid state envelope")
            return data
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exception:
            self._fail(exception)

    def _write(self, data: dict[str, Any]) -> None:
        temporary = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
            with os.fdopen(descriptor, "wb") as output:
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.path)
            os.chmod(self.path, 0o600)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _existing(self, data: dict[str, Any], fingerprint: str) -> DeliveryRecord:
        try:
            return self._decode(data["records"][fingerprint], fingerprint)
        except KeyError as exception:
            self._fail(exception)

    @staticmethod
    def _encode(record: DeliveryRecord) -> dict[str, Any]:
        payload = asdict(record)
        payload["state"] = record.state.value
        return payload

    def _decode(self, raw: object, fingerprint: str) -> DeliveryRecord:
        try:
            if not isinstance(raw, dict) or raw.get("source_fingerprint") != fingerprint:
                raise ValueError("invalid record")
            record = DeliveryRecord(
                source_fingerprint=raw["source_fingerprint"],
                request_id=raw["request_id"],
                state=DeliveryState(raw["state"]),
                created_at=raw["created_at"],
                updated_at=raw["updated_at"],
                todoist_task_id=raw.get("todoist_task_id"),
            )
            if any(
                not isinstance(value, str) or not value
                for value in (
                    record.source_fingerprint,
                    record.request_id,
                    record.created_at,
                    record.updated_at,
                )
            ):
                raise ValueError("invalid record fields")
            return record
        except (KeyError, TypeError, ValueError) as exception:
            self._fail(exception)

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _fail(exception: BaseException) -> None:
        raise ReconciliationError(
            RedactedError.from_exception(ErrorCode.INTERNAL_ERROR, exception)
        ) from None
