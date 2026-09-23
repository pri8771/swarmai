"""V2A-004 / ART-V15-WORKER-PROTOCOL — durable worker service/client tests."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from swarm.contracts.common import new_id
from swarm.contracts.enums import MissionStatus, TaskStatus
from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.lease_fencing import WorkerNotEligibleError
from swarm.db.models import Base, TaskRow
from swarm.db.repositories import MissionRepository
from swarm.workers.client import WorkerClient
from swarm.workers.envelopes import (
    EnrollmentRequest,
    WorkerHeartbeatRequest,
)
from swarm.workers.service import DurableWorkerService, ProtocolVersionError
from swarm.workers.transport import InProcessWorkerTransport

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


def _mission():
    mission = sample_mission()
    return mission.model_copy(update={"id": new_id("msn_"), "status": MissionStatus.RUNNING})


def _ready_task(session, *, mission, caps: list[str] | None = None) -> TaskRow:
    tid = new_id("tsk_")
    task = sample_task(mission_id=mission.id).model_copy(
        update={
            "id": tid,
            "project_id": mission.project_id,
            "required_capabilities": list(caps or ["code.read"]),
            "scopes": ["scope_repo_demo"],
            "status": TaskStatus.READY,
            "priority": 10,
            "graph_revision": mission.revision,
        }
    )
    row = TaskRow(
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
    session.add(row)
    session.flush()
    return row


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


def _client(session) -> WorkerClient:
    service = DurableWorkerService(session)
    return WorkerClient(transport=InProcessWorkerTransport(service))


def test_enroll_heartbeat_claim_submit_accept_via_client(session) -> None:
    mission = _mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _ready_task(session, mission=mission)

    client = _client(session)
    enrolled = client.enroll(
        EnrollmentRequest(
            host_alias="node-b2",
            project_id=mission.project_id,
            capabilities=["code.read", "chat"],
            trust_class="compute_only",
        )
    )
    assert enrolled.membership_token.startswith("wt_")
    assert "code.read" in enrolled.capabilities_granted

    hb = client.heartbeat(health={"executor": "ready"})
    assert hb.status == "online"
    assert hb.generation == enrolled.generation

    claimed = client.claim()
    assert claimed.claimed is True
    assert claimed.lease_id

    renewed = client.renew(lease_id=claimed.lease_id, progress_class="running")
    assert renewed.state == "renewed"

    submitted = client.submit_result(
        lease_id=claimed.lease_id,
        status="succeeded",
        checks={"review_passed": True},
        artifact_manifest={"sha256": "deadbeef"},
        summary="ok",
    )
    assert submitted.acceptance_state == "submitted"

    # Worker path must not self-accept; control-plane accept is explicit.
    accepted = client.control_plane_accept(result_id=submitted.result_id)
    assert accepted.acceptance_state == "accepted"


def test_capability_expansion_forbidden(session) -> None:
    mission = _mission()
    MissionRepository(session).insert(mission)
    session.flush()
    client = _client(session)
    client.enroll(
        EnrollmentRequest(
            host_alias="node-cap",
            project_id=mission.project_id,
            capabilities=["chat"],
        )
    )
    with pytest.raises(WorkerNotEligibleError, match="capability_expansion"):
        client.advertise(capabilities=["chat", "code.write"])


def test_capability_reduction_allowed(session) -> None:
    mission = _mission()
    MissionRepository(session).insert(mission)
    session.flush()
    client = _client(session)
    client.enroll(
        EnrollmentRequest(
            host_alias="node-reduce",
            project_id=mission.project_id,
            capabilities=["chat", "code.read"],
            capacity_units=2.0,
        )
    )
    row = client.advertise(capabilities=["chat"], capacity_units=1.0)
    assert set(row.capabilities) == {"chat"}
    assert row.capacity_units == 1.0


def test_drain_blocks_new_claims(session) -> None:
    mission = _mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _ready_task(session, mission=mission)
    _ready_task(session, mission=mission)

    client = _client(session)
    client.enroll(
        EnrollmentRequest(
            host_alias="node-drain",
            project_id=mission.project_id,
            capabilities=["code.read"],
        )
    )
    first = client.claim()
    assert first.claimed is True
    drained = client.drain()
    assert drained.status in {"draining", "offline"}
    # Still has active lease → draining
    assert first.lease_id in drained.active_lease_ids or drained.status == "draining"
    with pytest.raises(WorkerNotEligibleError, match="draining"):
        client.claim()


def test_reconnect_reconstructs_active_leases(session) -> None:
    mission = _mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _ready_task(session, mission=mission)

    client = _client(session)
    enrolled = client.enroll(
        EnrollmentRequest(
            host_alias="node-restart",
            project_id=mission.project_id,
            capabilities=["code.read"],
        )
    )
    claimed = client.claim()
    assert claimed.claimed is True

    # Simulate process restart: new client with same credentials, empty memory.
    restarted = WorkerClient(
        transport=InProcessWorkerTransport(DurableWorkerService(session)),
        worker_id=enrolled.worker_id,
        generation=enrolled.generation,
        membership_token=enrolled.membership_token,
        project_id=enrolled.project_id,
    )
    recovered = restarted.reconnect()
    assert any(row["lease_id"] == claimed.lease_id for row in recovered.active_leases)
    assert claimed.lease_id in restarted.active_lease_ids


def test_cancel_lease_via_service(session) -> None:
    mission = _mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _ready_task(session, mission=mission)
    client = _client(session)
    client.enroll(
        EnrollmentRequest(
            host_alias="node-cancel",
            project_id=mission.project_id,
            capabilities=["code.read"],
        )
    )
    claimed = client.claim()
    assert claimed.lease_id
    cancelled = client.cancel_lease(lease_id=claimed.lease_id)
    assert cancelled.state == "cancelled"


def test_unsupported_protocol_denied(session) -> None:
    service = DurableWorkerService(session)
    with pytest.raises(ProtocolVersionError):
        service.enroll(
            EnrollmentRequest(
                protocol_version="9.9",
                host_alias="bad",
                project_id="proj_x",
                capabilities=["chat"],
            )
        )


def test_heartbeat_capability_changes_rejected(session) -> None:
    mission = _mission()
    MissionRepository(session).insert(mission)
    session.flush()
    service = DurableWorkerService(session)
    transport = InProcessWorkerTransport(service)
    enrolled = transport.enroll(
        EnrollmentRequest(
            host_alias="node-hb",
            project_id=mission.project_id,
            capabilities=["chat"],
        )
    )
    with pytest.raises(WorkerNotEligibleError, match="capability_changes"):
        transport.heartbeat(
            WorkerHeartbeatRequest(
                worker_id=enrolled.worker_id,
                generation=enrolled.generation,
                membership_token=enrolled.membership_token,
                capability_changes=["code.write"],
            )
        )


def test_grant_allowlist_narrows_capabilities(session) -> None:
    mission = _mission()
    MissionRepository(session).insert(mission)
    session.flush()
    service = DurableWorkerService(
        session, granted_capability_allowlist={"chat"}
    )
    enrolled = service.enroll(
        EnrollmentRequest(
            host_alias="node-allow",
            project_id=mission.project_id,
            capabilities=["chat", "code.write", "vision.ocr"],
        )
    )
    assert enrolled.capabilities_granted == ["chat"]


def test_secret_bearing_enrollment_rejected(session) -> None:
    service = DurableWorkerService(session)
    with pytest.raises(WorkerNotEligibleError, match="provider_secret"):
        service.enroll(
            EnrollmentRequest(
                host_alias="evil",
                project_id="proj_x",
                capabilities=["chat"],
                worker_nonce="sk-live-secret",
            )
        )
