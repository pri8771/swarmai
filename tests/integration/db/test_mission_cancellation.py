"""MISSION-CANCEL-01 / ART-V15-WORKER-PROTOCOL — durable mission cancellation generation.

Closes the CP3 finding: the control plane now has a service method that bumps the
mission's durable `cancellation_generation` *before* advisory lease notification.
Fences are enforced by PostgreSQL rows, not by the worker's cooperation.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import select, text

from swarm.contracts.common import new_id
from swarm.contracts.enums import MissionStatus, TaskStatus
from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.lease_fencing import LeaseRenewError, ResultAcceptanceError
from swarm.db.models import Base, MissionRow, TaskRow, WorkerResultRow
from swarm.db.repositories import MissionRepository
from swarm.workers.client import WorkerClient
from swarm.workers.envelopes import EnrollmentRequest
from swarm.workers.service import DurableWorkerService
from swarm.workers.transport import InProcessWorkerTransport

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
CAPS = ["code.read", "chat"]
_TRUNCATE = (
    "TRUNCATE missions, tasks, graph_revisions, findings, artifact_metadata, reservations, "
    "attempt_receipts, events, outbox, provider_accounts, route_snapshots, quota_buckets, "
    "capability_profiles, approvals, worker_results, task_leases, worker_leases, task_attempts "
    "RESTART IDENTITY CASCADE"
)


@pytest.fixture(scope="module")
def engine():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def session(engine):
    sess = make_session_factory(engine)()
    try:
        yield sess
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    finally:
        sess.rollback()
        sess.execute(text(_TRUNCATE))
        sess.commit()
        sess.close()


def _seed(session) -> tuple[MissionRow, str]:
    mission = sample_mission().model_copy(
        update={"id": new_id("msn_"), "status": MissionStatus.RUNNING}
    )
    MissionRepository(session).insert(mission)
    session.flush()
    tid = new_id("tsk_")
    task = sample_task(mission_id=mission.id).model_copy(
        update={
            "id": tid,
            "project_id": mission.project_id,
            "required_capabilities": list(CAPS),
            "scopes": ["scope_repo_demo"],
            "status": TaskStatus.READY,
            "priority": 10,
            "graph_revision": mission.revision,
        }
    )
    session.add(
        TaskRow(
            id=tid,
            project_id=mission.project_id,
            mission_id=mission.id,
            objective=task.objective,
            task_family=task.task_family,
            status="ready",
            graph_revision=mission.revision,
            priority=10,
            scopes=list(task.scopes),
            dependency_ids=[],
            payload=task.model_dump(mode="json"),
        )
    )
    session.commit()
    row = session.get(MissionRow, mission.id)
    assert row is not None
    return row, tid


def _worker(session, project_id: str, host: str) -> tuple[DurableWorkerService, WorkerClient]:
    service = DurableWorkerService(session)
    client = WorkerClient(InProcessWorkerTransport(service))
    client.enroll(
        EnrollmentRequest(
            host_alias=host,
            project_id=project_id,
            capabilities=list(CAPS),
            trust_class="compute_only",
        )
    )
    return service, client


def _accepted_count(session, task_id: str) -> int:
    session.expire_all()
    return len(
        session.scalars(
            select(WorkerResultRow).where(
                WorkerResultRow.task_id == task_id, WorkerResultRow.acceptance_state == "accepted"
            )
        ).all()
    )


def test_revoke_without_notification_fences_result_and_renew(session) -> None:
    """A lost advisory notification never weakens the durable fence."""
    mission, tid = _seed(session)
    service, worker = _worker(session, mission.project_id, "w1")
    claimed = worker.claim()
    assert claimed.claimed and claimed.lease_id
    session.commit()

    outcome = service.revoke_mission_work(mission_id=mission.id, notify_leases=False)
    session.commit()
    assert (outcome.previous_generation, outcome.new_generation) == (0, 1)
    assert outcome.notified_lease_ids == ()
    assert outcome.terminal is False

    submitted = worker.submit_result(
        lease_id=claimed.lease_id,
        status="succeeded",
        checks={"review_passed": True},
        summary="late",
    )
    session.commit()
    with pytest.raises(ResultAcceptanceError, match="cancellation_generation_stale"):
        service.accept_result(result_id=submitted.result_id)
    session.rollback()
    with pytest.raises(LeaseRenewError, match="cancellation_generation_stale"):
        worker.renew(lease_id=claimed.lease_id)
    session.rollback()
    assert _accepted_count(session, tid) == 0
    session.expire_all()
    assert session.get(MissionRow, mission.id).status == "running"  # not terminal


def test_revoke_notifies_leases_and_new_claim_carries_new_generation(session) -> None:
    mission, tid = _seed(session)
    service, w1 = _worker(session, mission.project_id, "w1")
    first = w1.claim()
    assert first.claimed and first.lease_id
    session.commit()

    outcome = service.revoke_mission_work(mission_id=mission.id, reason="revoked")
    session.commit()
    assert outcome.notified_lease_ids == (first.lease_id,)
    # Old holder is fenced on the lease state as well as the generation.
    late = w1.submit_result(
        lease_id=first.lease_id, status="succeeded", checks={"review_passed": True}, summary="old"
    )
    session.commit()
    with pytest.raises(ResultAcceptanceError):
        service.accept_result(result_id=late.result_id)
    session.rollback()

    # The task went back to ready; a fresh worker claims it under generation 1 and is accepted.
    session.expire_all()
    assert session.get(TaskRow, tid).status == "ready"
    _, w2 = _worker(session, mission.project_id, "w2")
    second = w2.claim()
    assert second.claimed and second.lease_id and second.task_id == tid
    session.commit()
    good = w2.submit_result(
        lease_id=second.lease_id, status="succeeded", checks={"review_passed": True}, summary="new"
    )
    session.commit()
    accepted = service.accept_result(result_id=good.result_id)
    session.commit()
    assert accepted.result_id == good.result_id
    assert _accepted_count(session, tid) == 1


def test_cancel_mission_is_terminal(session) -> None:
    mission, tid = _seed(session)
    service, w1 = _worker(session, mission.project_id, "w1")
    claimed = w1.claim()
    assert claimed.claimed and claimed.lease_id
    session.commit()

    outcome = service.cancel_mission(mission_id=mission.id)
    session.commit()
    assert outcome.terminal is True and outcome.new_generation == 1
    session.expire_all()
    assert session.get(MissionRow, mission.id).status == "cancelled"
    assert session.get(TaskRow, tid).status == "cancelled"

    late = w1.submit_result(
        lease_id=claimed.lease_id, status="succeeded", checks={"review_passed": True}, summary="x"
    )
    session.commit()
    with pytest.raises(ResultAcceptanceError):
        service.accept_result(result_id=late.result_id)
    session.rollback()
    _, w2 = _worker(session, mission.project_id, "w2")
    assert w2.claim().claimed is False  # nothing claimable in a cancelled mission
    assert _accepted_count(session, tid) == 0


def test_generation_is_monotonic_and_durable(session) -> None:
    mission, _tid = _seed(session)
    service = DurableWorkerService(session)
    a = service.revoke_mission_work(mission_id=mission.id, notify_leases=False)
    session.commit()
    b = service.revoke_mission_work(mission_id=mission.id, notify_leases=False)
    session.commit()
    assert (a.new_generation, b.previous_generation, b.new_generation) == (1, 1, 2)
    fresh = make_session_factory(session.get_bind())()
    try:
        assert fresh.get(MissionRow, mission.id).cancellation_generation == 2
        events = fresh.execute(
            text(
                "SELECT count(*) FROM outbox WHERE aggregate_id = :m "
                "AND event_type = 'mission.cancellation_generation_bumped'"
            ),
            {"m": mission.id},
        ).scalar()
        assert events == 2
    finally:
        fresh.close()
    with pytest.raises(ResultAcceptanceError, match="mission_missing"):
        service.revoke_mission_work(mission_id="msn_does_not_exist", notify_leases=False)
