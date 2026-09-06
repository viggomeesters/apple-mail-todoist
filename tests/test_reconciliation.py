import json
import stat
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from apple_mail_todoist.domain import RequestIdentity
from apple_mail_todoist.reconciliation import (
    DeliveryState,
    ReconciliationError,
    ReconciliationStore,
)


def identity(request_id: str = "12345678-1234-4234-8234-123456789abc") -> RequestIdentity:
    return RequestIdentity("f" * 64, request_id)


def test_begin_persists_only_minimal_pending_state_with_private_permissions(tmp_path: Path) -> None:
    path = tmp_path / "private" / "reconciliation.json"
    result = ReconciliationStore(path).begin(identity())

    assert result.created is True
    assert result.record.state is DeliveryState.PENDING
    stored = path.read_text()
    assert set(json.loads(stored)) == {"schema", "records"}
    for forbidden in ("subject", "sender", "body", "token", "description", "payload"):
        assert forbidden not in stored.lower()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700


def test_confirmed_replay_returns_existing_task_and_original_request(tmp_path: Path) -> None:
    store = ReconciliationStore(tmp_path / "state.json")
    original = identity()
    store.begin(original)
    store.confirm(original.source_fingerprint, "6XExisting")

    replay = store.begin(identity("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"))

    assert replay.created is False
    assert replay.record.state is DeliveryState.CONFIRMED
    assert replay.record.request_id == original.request_id
    assert replay.record.todoist_task_id == "6XExisting"


def test_pending_or_uncertain_state_blocks_a_second_logical_request(tmp_path: Path) -> None:
    store = ReconciliationStore(tmp_path / "state.json")
    original = identity()
    store.begin(original)
    pending = store.begin(identity("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"))
    store.mark_uncertain(original.source_fingerprint)
    uncertain = store.begin(identity("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"))

    assert pending.created is False
    assert uncertain.created is False
    assert uncertain.record.state is DeliveryState.UNCERTAIN
    assert uncertain.record.request_id == original.request_id


def test_explicit_reconciliation_can_permit_same_request_retry(tmp_path: Path) -> None:
    store = ReconciliationStore(tmp_path / "state.json")
    original = identity()
    store.begin(original)
    store.mark_uncertain(original.source_fingerprint)

    retry = store.permit_retry(original.source_fingerprint)

    assert retry.state is DeliveryState.PENDING
    assert retry.request_id == original.request_id


def test_abandon_releases_only_pending_delivery(tmp_path: Path) -> None:
    store = ReconciliationStore(tmp_path / "state.json")
    original = identity()
    store.begin(original)

    store.abandon(original.source_fingerprint)

    replacement = identity("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    assert store.begin(replacement).record.request_id == replacement.request_id


@pytest.mark.parametrize("state", [DeliveryState.UNCERTAIN, DeliveryState.CONFIRMED])
def test_abandon_preserves_protected_delivery_states(
    tmp_path: Path, state: DeliveryState
) -> None:
    store = ReconciliationStore(tmp_path / "state.json")
    original = identity()
    store.begin(original)
    if state is DeliveryState.UNCERTAIN:
        store.mark_uncertain(original.source_fingerprint)
    else:
        store.confirm(original.source_fingerprint, "6XExisting")

    with pytest.raises(ReconciliationError):
        store.abandon(original.source_fingerprint)

    assert store.begin(identity("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")).record.request_id == (
        original.request_id
    )


def test_corruption_fails_closed_without_overwriting_state(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text("private corrupt bytes")

    with pytest.raises(ReconciliationError):
        ReconciliationStore(path).begin(identity())

    assert path.read_text() == "private corrupt bytes"


def test_concurrent_begin_has_exactly_one_winner(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    identities = [
        identity(f"00000000-0000-4000-8000-{number:012d}") for number in range(12)
    ]

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda item: ReconciliationStore(path).begin(item), identities))

    assert sum(result.created for result in results) == 1
    assert len({result.record.request_id for result in results}) == 1
