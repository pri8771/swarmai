"""PostgreSQL integration tests for P02."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import FindingStatus, GraphOperation, SettlementState
from swarm.contracts.fixtures import (
    sample_mission,
    sample_receipt,
    sample_reservation,
    sample_task,
)
from swarm.contracts.mission import GraphProposal
from swarm.contracts.provider import AttemptReceipt
from swarm.contracts.workspace import ArtifactRef, Finding
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base, OutboxRow
from swarm.db.outbox import OutboxPublisher
from swarm.db.repositories import (
    ArtifactRepository,
    FindingRepository,
    GraphRevisionConflict,
    LedgerRepository,
    MissionRepository,
    OutboxRepository,
)

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)


@pytest.fixture(scope="module")
def engine():
    eng = create_db_engine(DATABASE_URL)
    ping(eng)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session(engine):
    factory = make_session_factory(engine)
    sess = factory()
    try:
        yield sess
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    finally:
        # Truncate for isolation
        sess.execute(
            text(
                "TRUNCATE missions, tasks, graph_revisions, findings, artifact_metadata, "
                "reservations, attempt_receipts, events, outbox, provider_accounts, "
                "route_snapshots, quota_buckets, capability_profiles, approvals, "
                "worker_leases, task_attempts RESTART IDENTITY CASCADE"
            )
        )
        sess.commit()
        sess.close()


def test_migrate_validate_roundtrip(engine) -> None:
    assert ping(engine) is True


def test_graph_revision_conflict(session) -> None:
    mission = sample_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    proposal = GraphProposal(
        project_id="proj_demo",
        mission_id=mission.id,
        based_on_revision=1,
        author_session_id="as_1",
        operation=GraphOperation.SPAWN,
        rationale_summary="spawn",
        task_specs=[sample_task()],
    )
    MissionRepository(session).commit_graph_revision(proposal)
    session.flush()
    with pytest.raises(GraphRevisionConflict):
        MissionRepository(session).commit_graph_revision(proposal)


def test_unique_receipt_settlement(session) -> None:
    ledger = LedgerRepository(session)
    reservation = sample_reservation()
    ledger.insert_reservation(reservation)
    receipt = sample_receipt()
    receipt.idempotency_key = "idem-1"
    ledger.insert_receipt(receipt)
    session.flush()
    dup = AttemptReceipt(
        logical_call_id=receipt.logical_call_id,
        network_attempt_id=new_id("na_"),
        idempotency_key="idem-1",
        send_phase=receipt.send_phase,
        actual_route=receipt.actual_route,
        settlement_state=SettlementState.SETTLED,
        started_at=utc_now(),
        finished_at=utc_now(),
    )
    with pytest.raises(IntegrityError):
        ledger.insert_receipt(dup)
        session.flush()
    session.rollback()


def test_tenant_scope_filtering(session) -> None:
    findings = FindingRepository(session)
    findings.append(
        Finding(
            project_id="proj_demo",
            content="visible",
            author="a",
            task_id="t1",
            status=FindingStatus.HYPOTHESIS,
            acl=["scope_a"],
        ),
        scopes=["scope_a"],
    )
    findings.append(
        Finding(
            project_id="proj_demo",
            content="hidden",
            author="a",
            task_id="t2",
            status=FindingStatus.HYPOTHESIS,
            acl=["scope_b"],
        ),
        scopes=["scope_b"],
    )
    session.flush()
    visible = findings.query_scoped("proj_demo", {"scope_a"})
    assert len(visible) == 1
    assert visible[0].content == "visible"


def test_artifact_metadata_without_blob(session) -> None:
    ArtifactRepository(session).put_metadata(
        ArtifactRef(
            content_hash="abc123",
            uri="s3://bucket/key",
            media_type="text/plain",
            byte_length=12,
            owner_scope="scope_a",
            retention_class="mission",
        )
    )
    session.flush()


def test_commit_before_enqueue_crash(session) -> None:
    """Domain commit + outbox insert succeed; publisher crash leaves pending row."""
    mission = sample_mission()
    MissionRepository(session).insert(mission)
    OutboxRepository(session).enqueue(
        stable_workflow_id=f"wf:{mission.id}:1",
        aggregate_type="mission",
        aggregate_id=mission.id,
        event_type="mission.created",
        payload={"mission_id": mission.id},
    )
    session.commit()

    def boom(_wf: str, _payload: dict) -> None:
        raise RuntimeError("enqueue_failed")

    publisher = OutboxPublisher(session, enqueue=boom)
    assert publisher.drain() == 0
    session.commit()
    pending = session.query(OutboxRow).filter_by(status="pending").all()
    assert len(pending) == 1
    assert pending[0].attempts == 1


def test_enqueue_before_ack_replay(session) -> None:
    """Replay publishes once via stable workflow id uniqueness."""
    published: list[str] = []

    def enqueue(wf: str, payload: dict) -> None:
        published.append(wf)

    OutboxRepository(session).enqueue(
        stable_workflow_id="wf:stable:1",
        aggregate_type="task",
        aggregate_id="t1",
        event_type="task.ready",
        payload={"task_id": "t1"},
    )
    session.commit()
    pub = OutboxPublisher(session, enqueue=enqueue)
    assert pub.drain() == 1
    session.commit()
    assert published == ["wf:stable:1"]
    # Second enqueue with same workflow id must fail uniquely
    with pytest.raises(IntegrityError):
        OutboxRepository(session).enqueue(
            stable_workflow_id="wf:stable:1",
            aggregate_type="task",
            aggregate_id="t1",
            event_type="task.ready",
            payload={"task_id": "t1"},
        )
        session.flush()
    session.rollback()


def test_pooled_connection_pressure(engine) -> None:
    factory = make_session_factory(engine)

    def work(_: int) -> bool:
        with factory() as sess:
            sess.execute(text("SELECT 1"))
            sess.commit()
        return True

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(work, range(32)))
    assert all(results)
