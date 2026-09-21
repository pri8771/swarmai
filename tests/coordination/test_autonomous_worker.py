"""OPS-AUTO-001-R fail-closed autonomous worker selection and fencing."""

from __future__ import annotations

import importlib.util
import os
import time
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
WORKER_PATH = ROOT / "scripts" / "coordination" / "autonomous_worker.py"


def load_worker() -> ModuleType:
    spec = importlib.util.spec_from_file_location("autonomous_worker", WORKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


worker = load_worker()


def _root(**overrides: object) -> dict:
    base: dict = {
        "enabled": True,
        "assignment_id": "A-TEST-01",
        "generation": 2,
        "host_alias": "HOST-MAC-DEV",
        "session_id": "A",
        "branch": "cursor/v2-runtime-lane",
        "items": [
            {"packet_id": "PKT-ONE", "artifact_id": "ART-ONE"},
            {"packet_id": "PKT-TWO", "artifact_id": "ART-TWO"},
        ],
    }
    base.update(overrides)
    return base


def test_selects_exactly_one_packet_per_invocation() -> None:
    assignment, key, reason = worker.select_next_item(_root(), {})
    assert reason == "selected"
    assert assignment is not None
    assert assignment["packet_id"] == "PKT-ONE"
    assert key == "A-TEST-01:2:PKT-ONE"


def test_completed_item_is_not_rerun() -> None:
    state = {"completed_item_keys": ["A-TEST-01:2:PKT-ONE"]}
    assignment, key, reason = worker.select_next_item(_root(), state)
    assert reason == "selected"
    assert assignment is not None
    assert assignment["packet_id"] == "PKT-TWO"
    assert key == "A-TEST-01:2:PKT-TWO"

    state["completed_item_keys"].append("A-TEST-01:2:PKT-TWO")
    assignment, key, reason = worker.select_next_item(_root(), state)
    assert reason == "exhausted"
    assert assignment is None
    assert key is None


def test_started_but_incomplete_item_waits_for_new_generation() -> None:
    state = {
        "last_started_key": "A-TEST-01:2:PKT-ONE",
        "last_completed_key": "something-else",
    }
    assignment, key, reason = worker.select_next_item(_root(), state)
    assert reason == "wait_generation"
    assert assignment is None
    assert key == "A-TEST-01:2:PKT-ONE"

    later = _root(generation=3)
    assignment, key, reason = worker.select_next_item(later, state)
    assert reason == "selected"
    assert assignment is not None
    assert key == "A-TEST-01:3:PKT-ONE"


def test_identity_mismatch_fails_closed() -> None:
    root = _root()
    assert worker.assignment_identity_ok(root, "HOST-MAC-DEV", "A", "cursor/v2-runtime-lane")
    assert not worker.assignment_identity_ok(root, "HOST-WIN-DEV", "A", "cursor/v2-runtime-lane")
    assert not worker.assignment_identity_ok(root, "HOST-MAC-DEV", "B", "cursor/v2-runtime-lane")
    assert not worker.assignment_identity_ok(root, "HOST-MAC-DEV", "A", "cursor/v2-product-lane")


def test_dirty_or_wrong_branch_fails_closed() -> None:
    assert (
        worker.preflight_block_reason("other", "cursor/v2-runtime-lane", "") == "wrong_branch:other"
    )
    assert (
        worker.preflight_block_reason("cursor/v2-runtime-lane", "cursor/v2-runtime-lane", " M file")
        == "autonomous_runner_dirty_worktree"
    )
    assert (
        worker.preflight_block_reason("cursor/v2-runtime-lane", "cursor/v2-runtime-lane", "")
        is None
    )


def test_no_remote_advancement_is_blocked() -> None:
    assert (
        worker.post_agent_block_reason(dirty_after="", after="abc", before="abc")
        == "no_remote_change"
    )
    assert (
        worker.post_agent_block_reason(dirty_after=" M file", after="def", before="abc")
        == "dirty_after_agent"
    )
    assert worker.post_agent_block_reason(dirty_after="", after="def", before="abc") is None


def test_acquire_lock_blocks_overlap(tmp_path: Path) -> None:
    lock = tmp_path / "runner.lock"
    assert worker.acquire_lock(lock, stale_seconds=900) is True
    assert worker.acquire_lock(lock, stale_seconds=900) is False
    past = time.time() - 1000
    os.utime(lock, (past, past))
    assert worker.acquire_lock(lock, stale_seconds=900) is True
