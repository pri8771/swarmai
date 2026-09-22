"""V2A-005 recovery harness tests — simulated multi-worker, not live multi-host."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.workers.recovery_harness import MultiWorkerRecoveryHarness

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)

_TRUNCATE = (
    "TRUNCATE missions, tasks, graph_revisions, findings, artifact_metadata, "
    "reservations, attempt_receipts, events, outbox, provider_accounts, "
    "route_snapshots, quota_buckets, capability_profiles, approvals, "
    "worker_results, task_leases, worker_leases, task_attempts "
    "RESTART IDENTITY CASCADE"
)


@pytest.fixture(scope="module")
def engine():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.drop_all(eng)
    with eng.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    yield eng
    Base.metadata.drop_all(eng)
    with eng.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    eng.dispose()


@pytest.fixture()
def session(engine):
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    sess = factory()
    try:
        yield sess
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    finally:
        sess.execute(text(_TRUNCATE))
        sess.commit()
        sess.close()


def test_recovery_harness_all_scenarios_pass(session) -> None:
    report = MultiWorkerRecoveryHarness(session).run_all()
    assert report.live_multi_host_evidence.startswith("UNKNOWN")
    assert report.mode == "simulated_multi_worker_single_process"
    failed = [s for s in report.scenarios if not s.passed]
    assert not failed, report.to_dict()
    assert report.all_passed
    names = {s.name for s in report.scenarios}
    assert names >= {
        "host_enrollment",
        "dispatch_exactly_one_lease",
        "worker_kill_lease_expiry_reassignment",
        "stale_result_after_reassignment_rejected",
        "drain_blocks_new_leases",
        "restart_reconnect_recovers_leases",
    }


# ---- R17a: CP3 harness requirement map and "the step can fail" negatives


def _load_cp3_harness():
    # Imported by module path so spawned child processes can unpickle its targets.
    import importlib

    return importlib.import_module("scripts.r17_cp3_separate_process_recovery")


def test_cp3_report_lists_all_nine_requirements() -> None:
    harness = _load_cp3_harness()
    assert set(harness.REQUIREMENTS) == {
        "durable_worker_registration",
        "claim",
        "renew",
        "process_restart_real_kill",
        "expiry_reassignment",
        "stale_result_rejection",
        "duplicate_result_race_concurrent",
        "cancellation_generation_rejection",
        "exactly_one_accepted_result",
    }
    report = {
        "steps": {
            "victim_claim": {"pid": 1, "lease_id": "l1", "attempt_id": "a1", "killed": True},
            "expire_reassign": {"expired_leases": ["l1"]},
            "survivor_submit": {"pid": 2, "lease_id": "l2", "result_id": "r2"},
            "stale_reject": {"accept_rejected": True},
            "exactly_one_accept": {"exactly_one_accepted": True},
        },
        "r17a": {
            "cancellation_fence": {"demonstrated": True, "detail": {"renew_rejected": True}},
            "concurrent_duplicate_accept": {"demonstrated": True, "detail": {}},
        },
    }
    requirements = harness.build_requirements(report)
    assert set(requirements) == set(harness.REQUIREMENTS)
    assert all(r["demonstrated"] for r in requirements.values())


def test_cancellation_step_detects_missing_fence(session) -> None:
    """Prove the step can fail: with the durable generation bump disabled the accept
    succeeds and the step must report demonstrated=false (real Postgres, real process)."""
    import multiprocessing as mp

    harness = _load_cp3_harness()
    ctx = mp.get_context("spawn")
    outcome = harness.run_cancellation_step(
        session, DATABASE_URL, ctx, bump_generation=False
    )
    assert outcome["demonstrated"] is False
    detail = outcome["detail"]
    assert detail["generation_bumped"] is False
    assert detail["accept_rejected"] is False  # accept went through: fence was not triggered
    assert detail["accepted_count_for_task"] == 1
    # And the pure evaluator rejects any reason other than the exact fence reason.
    bad = dict(detail, generation_bumped=True, accept_rejected=True, accept_reason="lease_expired")
    assert harness.evaluate_cancellation_step(bad)["demonstrated"] is False


def test_concurrent_accept_step_detects_double_accept() -> None:
    harness = _load_cp3_harness()
    double = [
        {
            "index": 0,
            "outcomes": [
                {"accepted": True, "pid": 1},
                {"accepted": True, "pid": 2},
            ],
            "accepted_count_for_task": 2,
            "winner_pid": None,
        }
    ]
    assert harness.evaluate_concurrent_step(double)["demonstrated"] is False
    assert harness.evaluate_concurrent_step([])["demonstrated"] is False
    good = [
        {
            "index": 0,
            "outcomes": [
                {"accepted": True, "pid": 1},
                {"accepted": False, "pid": 2, "reason": "attempt_already_accepted"},
            ],
            "accepted_count_for_task": 1,
            "winner_pid": 1,
        }
    ]
    assert harness.evaluate_concurrent_step(good)["demonstrated"] is True
