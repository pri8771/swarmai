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
