"""V2A-003c / ART-V15-LEASE-FENCING — durable result acceptance fence."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import text

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import MissionStatus, TaskStatus
from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.lease_fencing import (
    LeaseLifecycleService,
    ResultAcceptanceError,
    WorkerNotEligibleError,
    WorkerRegistrationRepository,
)
from swarm.db.models import Base, MissionRow, TaskAttemptRow, TaskLeaseRow, TaskRow, WorkerResultRow
from swarm.db.repositories import MissionRepository
from swarm.workers.durable_protocol import DurableWorkerProtocol

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[3]
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


def _unique_mission(*, status: MissionStatus = MissionStatus.RUNNING):
    mission = sample_mission()
    return mission.model_copy(update={"id": new_id("msn_"), "status": status})


def _insert_ready_task(
    session,
    *,
    mission,
    required_capabilities: list[str],
    priority: int = 100,
    graph_revision: int | None = None,
    source_revision: str | None = None,
    cancellation_generation: int | None = None,
) -> TaskRow:
    tid = new_id("tsk_")
    rev = mission.revision if graph_revision is None else graph_revision
    task = sample_task(mission_id=mission.id).model_copy(
        update={
            "id": tid,
            "project_id": mission.project_id,
            "required_capabilities": required_capabilities,
            "scopes": ["scope_repo_demo"],
            "status": TaskStatus.READY,
            "priority": priority,
            "graph_revision": rev,
        }
    )
    payload = task.model_dump(mode="json")
    if source_revision is not None:
        payload["source_revision"] = source_revision
    if cancellation_generation is not None:
        payload["cancellation_generation"] = cancellation_generation
    row = TaskRow(
        id=tid,
        project_id=mission.project_id,
        mission_id=mission.id,
        objective=task.objective,
        task_family=task.task_family,
        status="ready",
        graph_revision=rev,
        priority=priority,
        scopes=list(task.scopes),
        dependency_ids=[],
        payload=payload,
    )
    session.add(row)
    session.flush()
    return row


def _register_worker(
    session,
    *,
    project_id: str,
    capabilities: list[str],
    token: str,
    generation: int = 1,
) -> str:
    wid = new_id("wrk_")
    WorkerRegistrationRepository(session).upsert_registration(
        worker_id=wid,
        project_id=project_id,
        node_identity=f"node-{wid}",
        architecture="arm64",
        runtime_version="py3.12",
        capacity_units=1.0,
        membership_token=token,
        generation=generation,
        capabilities=capabilities,
        privacy_classes=["local"],
    )
    session.flush()
    return wid


def _claim(session, *, worker_id: str, token: str, now=None):
    return LeaseLifecycleService(session).claim_eligible_attempt(
        worker_id=worker_id,
        membership_token=token,
        now=now,
    )


def _passing_checks() -> dict:
    return {"review_passed": True, "verification_passed": True}


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


def test_accept_happy_path_exactly_one(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session, project_id=mission.project_id, capabilities=["code.read"], token=token
    )
    claimed = _claim(session, worker_id=worker_id, token=token)
    assert claimed is not None
    proto = DurableWorkerProtocol(session)
    submitted = proto.submit_result(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        membership_token=token,
        worker_generation=claimed.worker_generation,
        result_status="succeeded",
        checks=_passing_checks(),
        artifact_manifest={"sha256": "abc"},
    )
    accepted = proto.accept_result(result_id=submitted.result_id)
    assert accepted.acceptance_state == "accepted"
    attempt = session.get(TaskAttemptRow, claimed.attempt_id)
    assert attempt is not None
    assert attempt.accepted_result_id == submitted.result_id
    assert attempt.status == "accepted"
    task = session.get(TaskRow, claimed.task_id)
    assert task is not None and task.status == "accepted"
    # Idempotent re-accept
    again = proto.accept_result(result_id=submitted.result_id)
    assert again.result_id == submitted.result_id


def test_duplicate_result_second_rejected(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session, project_id=mission.project_id, capabilities=["code.read"], token=token
    )
    claimed = _claim(session, worker_id=worker_id, token=token)
    assert claimed is not None
    svc = LeaseLifecycleService(session)
    first = svc.submit_result(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        membership_token=token,
        worker_generation=claimed.worker_generation,
        result_status="succeeded",
        checks=_passing_checks(),
    )
    second = svc.submit_result(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        membership_token=token,
        worker_generation=claimed.worker_generation,
        result_status="succeeded",
        checks=_passing_checks(),
    )
    svc.accept_result(result_id=first.result_id)
    with pytest.raises(ResultAcceptanceError, match="attempt_already_accepted|duplicate"):
        svc.accept_result(result_id=second.result_id)
    rejected = session.get(WorkerResultRow, second.result_id)
    assert rejected is not None
    assert rejected.acceptance_state == "rejected"


def test_stale_worker_generation_rejected(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session, project_id=mission.project_id, capabilities=["code.read"], token=token
    )
    claimed = _claim(session, worker_id=worker_id, token=token)
    assert claimed is not None
    svc = LeaseLifecycleService(session)
    submitted = svc.submit_result(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        membership_token=token,
        worker_generation=claimed.worker_generation,
        result_status="succeeded",
        checks=_passing_checks(),
    )
    # Rotate membership → generation bump fences prior results.
    WorkerRegistrationRepository(session).rotate_membership_token(
        worker_id=worker_id, current_token=token, new_token=new_id("wt_")
    )
    with pytest.raises(ResultAcceptanceError, match="worker_generation_stale"):
        svc.accept_result(result_id=submitted.result_id)


def test_expired_lease_result_rejected(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session, project_id=mission.project_id, capabilities=["code.read"], token=token
    )
    clock = utc_now()
    claimed = _claim(session, worker_id=worker_id, token=token, now=clock)
    assert claimed is not None
    svc = LeaseLifecycleService(session)
    svc.expire_leases(now=clock + timedelta(seconds=120))
    submitted = svc.submit_result(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        membership_token=token,
        worker_generation=claimed.worker_generation,
        result_status="succeeded",
        checks=_passing_checks(),
        now=clock + timedelta(seconds=121),
    )
    with pytest.raises(ResultAcceptanceError, match="lease_not_current|lease_expired"):
        svc.accept_result(result_id=submitted.result_id, now=clock + timedelta(seconds=122))
    row = session.get(WorkerResultRow, submitted.result_id)
    assert row is not None and row.acceptance_state == "rejected"


def test_cancelled_mission_rejects_accept(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(
        session,
        mission=mission,
        required_capabilities=["code.read"],
        cancellation_generation=0,
    )
    token = new_id("wt_")
    worker_id = _register_worker(
        session, project_id=mission.project_id, capabilities=["code.read"], token=token
    )
    claimed = _claim(session, worker_id=worker_id, token=token)
    assert claimed is not None
    svc = LeaseLifecycleService(session)
    submitted = svc.submit_result(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        membership_token=token,
        worker_generation=claimed.worker_generation,
        result_status="succeeded",
        checks=_passing_checks(),
    )
    mrow = session.get(MissionRow, mission.id)
    assert mrow is not None
    mrow.status = "cancelled"
    mrow.cancellation_generation = int(mrow.cancellation_generation) + 1
    session.flush()
    with pytest.raises(ResultAcceptanceError, match="mission_cancelled|cancellation"):
        svc.accept_result(result_id=submitted.result_id)


def test_task_revision_mismatch_rejects(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session, project_id=mission.project_id, capabilities=["code.read"], token=token
    )
    claimed = _claim(session, worker_id=worker_id, token=token)
    assert claimed is not None
    svc = LeaseLifecycleService(session)
    submitted = svc.submit_result(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        membership_token=token,
        worker_generation=claimed.worker_generation,
        result_status="succeeded",
        checks=_passing_checks(),
    )
    task = session.get(TaskRow, claimed.task_id)
    assert task is not None
    task.graph_revision = int(task.graph_revision) + 1
    mrow = session.get(MissionRow, mission.id)
    assert mrow is not None
    mrow.revision = int(mrow.revision) + 1
    session.flush()
    with pytest.raises(ResultAcceptanceError, match="task_revision_mismatch|source_revision"):
        svc.accept_result(result_id=submitted.result_id)


def test_cancel_lease_blocks_accept(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session, project_id=mission.project_id, capabilities=["code.read"], token=token
    )
    claimed = _claim(session, worker_id=worker_id, token=token)
    assert claimed is not None
    svc = LeaseLifecycleService(session)
    submitted = svc.submit_result(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        membership_token=token,
        worker_generation=claimed.worker_generation,
        result_status="succeeded",
        checks=_passing_checks(),
    )
    svc.cancel_active_lease(lease_id=claimed.lease_id)
    with pytest.raises(ResultAcceptanceError, match="lease_not_current|attempt_terminal"):
        svc.accept_result(result_id=submitted.result_id)


def test_drain_blocks_new_claims_allows_late_submit(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"], priority=10)
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"], priority=20)
    token = new_id("wt_")
    worker_id = _register_worker(
        session, project_id=mission.project_id, capabilities=["code.read"], token=token
    )
    claimed = _claim(session, worker_id=worker_id, token=token)
    assert claimed is not None
    WorkerRegistrationRepository(session).request_drain(worker_id=worker_id)
    svc = LeaseLifecycleService(session)
    with pytest.raises(WorkerNotEligibleError, match="draining"):
        svc.claim_eligible_attempt(worker_id=worker_id, membership_token=token)
    # Late submit still allowed for audit.
    submitted = svc.submit_result(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        membership_token=token,
        worker_generation=claimed.worker_generation,
        result_status="succeeded",
        checks=_passing_checks(),
    )
    accepted = svc.accept_result(result_id=submitted.result_id)
    assert accepted.acceptance_state == "accepted"


def test_review_checks_required(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session, project_id=mission.project_id, capabilities=["code.read"], token=token
    )
    claimed = _claim(session, worker_id=worker_id, token=token)
    assert claimed is not None
    svc = LeaseLifecycleService(session)
    submitted = svc.submit_result(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        membership_token=token,
        worker_generation=claimed.worker_generation,
        result_status="succeeded",
        checks={},
    )
    with pytest.raises(ResultAcceptanceError, match="review_checks_failed"):
        svc.accept_result(result_id=submitted.result_id)


def test_reservation_refs_must_reconcile(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session, project_id=mission.project_id, capabilities=["code.read"], token=token
    )
    claimed = _claim(session, worker_id=worker_id, token=token)
    assert claimed is not None
    lease = session.get(TaskLeaseRow, claimed.lease_id)
    assert lease is not None
    lease.reservation_refs = ["resv_1"]
    session.flush()
    svc = LeaseLifecycleService(session)
    submitted = svc.submit_result(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        membership_token=token,
        worker_generation=claimed.worker_generation,
        result_status="succeeded",
        checks=_passing_checks(),
        usage={},
    )
    with pytest.raises(ResultAcceptanceError, match="reservations_unreconciled"):
        svc.accept_result(result_id=submitted.result_id)
    ok = svc.submit_result(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        membership_token=token,
        worker_generation=claimed.worker_generation,
        result_status="succeeded",
        checks=_passing_checks(),
        usage={"reservation_refs": ["resv_1"]},
    )
    accepted = svc.accept_result(result_id=ok.result_id)
    assert accepted.acceptance_state == "accepted"
