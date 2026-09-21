"""V2A-003b / ART-V15-LEASE-FENCING — atomic claim/renew/expire (+ V2A-H3)."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import select, text

from swarm.contracts.common import new_id
from swarm.contracts.enums import MissionStatus, TaskStatus
from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.lease_fencing import (
    LeaseLifecycleService,
    LeaseRenewError,
    WorkerRegistrationRepository,
)
from swarm.db.models import Base, MissionRow, TaskAttemptRow, TaskLeaseRow, TaskRow
from swarm.db.repositories import MissionRepository

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[3]
DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)


def _unique_mission(*, status: MissionStatus = MissionStatus.RUNNING):
    mission = sample_mission()
    return mission.model_copy(update={"id": new_id("msn_"), "status": status})


def _insert_ready_task(
    session,
    *,
    mission,
    required_capabilities: list[str],
    scopes: list[str] | None = None,
    priority: int = 100,
    task_id: str | None = None,
    graph_revision: int | None = None,
    source_revision: str | None = None,
    cancellation_generation: int | None = None,
    dependency_ids: list[str] | None = None,
) -> TaskRow:
    tid = task_id or new_id("tsk_")
    rev = mission.revision if graph_revision is None else graph_revision
    task = sample_task(mission_id=mission.id).model_copy(
        update={
            "id": tid,
            "project_id": mission.project_id,
            "required_capabilities": required_capabilities,
            "scopes": list(scopes or ["scope_repo_demo"]),
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
        dependency_ids=list(dependency_ids or []),
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
    privacy_classes: list[str] | None = None,
    worker_id: str | None = None,
    generation: int = 1,
) -> str:
    wid = worker_id or new_id("wrk_")
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
        privacy_classes=list(privacy_classes or ["local"]),
    )
    session.flush()
    return wid


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
        sess.execute(
            text(
                "TRUNCATE missions, tasks, graph_revisions, findings, artifact_metadata, "
                "reservations, attempt_receipts, events, outbox, provider_accounts, "
                "route_snapshots, quota_buckets, capability_profiles, approvals, "
                "worker_results, task_leases, worker_leases, task_attempts "
                "RESTART IDENTITY CASCADE"
            )
        )
        sess.commit()
        sess.close()


@pytest.fixture()
def session_factory(engine):
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    yield factory
    with factory() as sess:
        sess.execute(
            text(
                "TRUNCATE missions, tasks, graph_revisions, findings, artifact_metadata, "
                "reservations, attempt_receipts, events, outbox, provider_accounts, "
                "route_snapshots, quota_buckets, capability_profiles, approvals, "
                "worker_results, task_leases, worker_leases, task_attempts "
                "RESTART IDENTITY CASCADE"
            )
        )
        sess.commit()


def test_two_claimers_race_exactly_one_wins(session_factory) -> None:
    """Two concurrent claim transactions: exactly one active lease for the task."""
    import threading

    with session_factory() as setup:
        mission = _unique_mission()
        MissionRepository(setup).insert(mission)
        setup.flush()
        task = _insert_ready_task(
            setup, mission=mission, required_capabilities=["code.read"], priority=10
        )
        token_a = new_id("wt_")
        token_b = new_id("wt_")
        worker_a = _register_worker(
            setup,
            project_id=mission.project_id,
            capabilities=["code.read", "chat"],
            token=token_a,
        )
        worker_b = _register_worker(
            setup,
            project_id=mission.project_id,
            capabilities=["code.read", "tools"],
            token=token_b,
        )
        setup.commit()
        task_id = task.id
        project_id = mission.project_id

    start = threading.Barrier(2)

    def _claim(worker_id: str, token: str) -> str | None:
        start.wait(timeout=10)
        with session_factory() as sess:
            svc = LeaseLifecycleService(sess)
            claimed = svc.claim_eligible_attempt(worker_id=worker_id, membership_token=token)
            sess.commit()
            return None if claimed is None else claimed.lease_id

    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_a = pool.submit(_claim, worker_a, token_a)
        fut_b = pool.submit(_claim, worker_b, token_b)
        results = [fut_a.result(timeout=30), fut_b.result(timeout=30)]

    winners = [lease_id for lease_id in results if lease_id is not None]
    assert len(winners) == 1

    with session_factory() as verify:
        rows = list(
            verify.scalars(
                select(TaskLeaseRow).where(
                    TaskLeaseRow.task_id == task_id,
                    TaskLeaseRow.state.in_(("active", "renewed")),
                )
            )
        )
        assert len(rows) == 1
        assert rows[0].lease_id == winners[0]
        task_row = verify.get(TaskRow, task_id)
        assert task_row is not None
        assert task_row.status == "leased"
        assert task_row.project_id == project_id


def test_incompatible_head_does_not_block_eligible_claim(session) -> None:
    """V2A-H3 durable: OCR-only head left ready; code.read worker claims later eligible."""
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    blocked = _insert_ready_task(
        session,
        mission=mission,
        required_capabilities=["vision.ocr"],
        priority=1,
    )
    eligible = _insert_ready_task(
        session,
        mission=mission,
        required_capabilities=["code.read"],
        priority=50,
    )
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read", "chat"],
        token=token,
    )
    session.flush()

    claimed = LeaseLifecycleService(session).claim_eligible_attempt(
        worker_id=worker_id, membership_token=token
    )
    session.flush()
    assert claimed is not None
    assert claimed.task_id == eligible.id

    blocked_row = session.get(TaskRow, blocked.id)
    assert blocked_row is not None
    assert blocked_row.status == "ready"
    eligible_row = session.get(TaskRow, eligible.id)
    assert eligible_row is not None
    assert eligible_row.status == "leased"


def test_renew_and_expire_persist_across_new_session(session_factory) -> None:
    """Lease renew then expire survives a new SQLAlchemy session/process boundary."""
    with session_factory() as s1:
        mission = _unique_mission()
        MissionRepository(s1).insert(mission)
        s1.flush()
        task = _insert_ready_task(
            s1, mission=mission, required_capabilities=["code.read"], priority=5
        )
        token = new_id("wt_")
        worker_id = _register_worker(
            s1,
            project_id=mission.project_id,
            capabilities=["code.read"],
            token=token,
            generation=2,
        )
        s1.flush()
        claimed = LeaseLifecycleService(s1, default_lease_seconds=30).claim_eligible_attempt(
            worker_id=worker_id,
            membership_token=token,
            lease_seconds=30,
        )
        s1.commit()
        assert claimed is not None
        lease_id = claimed.lease_id
        original_expiry = claimed.expires_at
        generation = claimed.worker_generation
        assert generation == 2

    with session_factory() as s2:
        svc = LeaseLifecycleService(s2, default_lease_seconds=45)
        renewed = svc.renew_lease(
            lease_id=lease_id,
            worker_id=worker_id,
            worker_generation=generation,
            membership_token=token,
            extend_seconds=45,
        )
        s2.commit()
        assert renewed.state == "renewed"
        assert renewed.expires_at > original_expiry
        renewed_expiry = renewed.expires_at

    with session_factory() as s3:
        loaded = s3.get(TaskLeaseRow, lease_id)
        assert loaded is not None
        assert loaded.state == "renewed"
        assert loaded.expires_at == renewed_expiry

        past = renewed_expiry + timedelta(seconds=1)
        expired = LeaseLifecycleService(s3).expire_leases(now=past)
        s3.commit()
        assert lease_id in expired

    with session_factory() as s4:
        loaded = s4.get(TaskLeaseRow, lease_id)
        assert loaded is not None
        assert loaded.state == "expired"
        task_row = s4.get(TaskRow, task.id)
        assert task_row is not None
        assert task_row.status == "ready"

        # Stale renew after expiry must fail.
        with pytest.raises(LeaseRenewError):
            LeaseLifecycleService(s4).renew_lease(
                lease_id=lease_id,
                worker_id=worker_id,
                worker_generation=generation,
                membership_token=token,
            )


def test_privacy_mismatch_skips_without_mutating_task(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    local_task = _insert_ready_task(
        session,
        mission=mission,
        required_capabilities=["code.read"],
        scopes=["local_only", "scope_repo_demo"],
        priority=1,
    )
    open_task = _insert_ready_task(
        session,
        mission=mission,
        required_capabilities=["code.read"],
        scopes=["scope_repo_demo"],
        priority=2,
    )
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
        privacy_classes=["cloud"],
    )
    claimed = LeaseLifecycleService(session).claim_eligible_attempt(
        worker_id=worker_id, membership_token=token
    )
    session.flush()
    assert claimed is not None
    assert claimed.task_id == open_task.id
    assert session.get(TaskRow, local_task.id).status == "ready"  # type: ignore[union-attr]


def test_cancelled_mission_claim_leaves_task_unmutated(session) -> None:
    """V2A-003b-R: cancelled mission cannot be claimed; task stays ready."""
    mission = _unique_mission(status=MissionStatus.CANCELLED)
    MissionRepository(session).insert(mission)
    session.flush()
    task = _insert_ready_task(
        session, mission=mission, required_capabilities=["code.read"], priority=1
    )
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
    )
    claimed = LeaseLifecycleService(session).claim_eligible_attempt(
        worker_id=worker_id, membership_token=token
    )
    session.flush()
    assert claimed is None
    loaded = session.get(TaskRow, task.id)
    assert loaded is not None
    assert loaded.status == "ready"
    assert session.scalars(select(TaskLeaseRow)).all() == []


def test_stale_source_revision_claim_leaves_task_unmutated(session) -> None:
    """V2A-003b-R: stale task source_revision cannot bind a lease."""
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    stale = _insert_ready_task(
        session,
        mission=mission,
        required_capabilities=["code.read"],
        priority=1,
        source_revision="stale_source_v0",
    )
    current = LeaseLifecycleService._mission_source_revision(
        session.get(MissionRow, mission.id)  # type: ignore[arg-type]
    )
    fresh = _insert_ready_task(
        session,
        mission=mission,
        required_capabilities=["code.read"],
        priority=50,
        source_revision=current,
    )
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
    )
    claimed = LeaseLifecycleService(session).claim_eligible_attempt(
        worker_id=worker_id, membership_token=token
    )
    session.flush()
    assert claimed is not None
    assert claimed.task_id == fresh.id
    assert session.get(TaskRow, stale.id).status == "ready"  # type: ignore[union-attr]


def test_stale_cancellation_generation_skips_without_mutation(session) -> None:
    mission = _unique_mission()
    # Bump mission cancellation generation without cancelling status.
    mission = mission.model_copy(update={"cancellation_generation": 3, "status": MissionStatus.RUNNING})
    MissionRepository(session).insert(mission)
    session.flush()
    stale = _insert_ready_task(
        session,
        mission=mission,
        required_capabilities=["code.read"],
        priority=1,
        cancellation_generation=0,
    )
    ok = _insert_ready_task(
        session,
        mission=mission,
        required_capabilities=["code.read"],
        priority=2,
        cancellation_generation=3,
    )
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
    )
    claimed = LeaseLifecycleService(session).claim_eligible_attempt(
        worker_id=worker_id, membership_token=token
    )
    session.flush()
    assert claimed is not None
    assert claimed.task_id == ok.id
    assert session.get(TaskRow, stale.id).status == "ready"  # type: ignore[union-attr]


def test_renew_rejects_worker_project_reassignment(session) -> None:
    """V2A-003b-R: renew requires durable worker.project_id == lease.project_id."""
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
        generation=1,
    )
    svc = LeaseLifecycleService(session)
    claimed = svc.claim_eligible_attempt(worker_id=worker_id, membership_token=token)
    session.flush()
    assert claimed is not None

    # Reassign worker to another project (same token/generation).
    worker = WorkerRegistrationRepository(session).get(worker_id)
    assert worker is not None
    worker.project_id = new_id("proj_")
    session.flush()

    with pytest.raises(LeaseRenewError, match="lease_project_mismatch"):
        svc.renew_lease(
            lease_id=claimed.lease_id,
            worker_id=worker_id,
            worker_generation=claimed.worker_generation,
            membership_token=token,
        )


def test_paginated_claim_beyond_32_incompatible_heads(session) -> None:
    """V2A-003b-R: >32 incompatible higher-priority rows cannot HOL-block an eligible task."""
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    for i in range(40):
        _insert_ready_task(
            session,
            mission=mission,
            required_capabilities=["vision.ocr"],
            priority=i,  # 0..39 higher priority than eligible
        )
    eligible = _insert_ready_task(
        session,
        mission=mission,
        required_capabilities=["code.read"],
        priority=100,
    )
    token = new_id("wt_")
    # Tiny page size forces multiple pagination rounds past the old 32 ceiling.
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
    )
    claimed = LeaseLifecycleService(session, candidate_page_size=8).claim_eligible_attempt(
        worker_id=worker_id, membership_token=token
    )
    session.flush()
    assert claimed is not None
    assert claimed.task_id == eligible.id
    assert session.get(TaskRow, eligible.id).status == "leased"  # type: ignore[union-attr]


def test_renew_rejects_stale_mission_authority(session) -> None:
    """V2A-003b-R: renew fails when mission/source/cancel authority drifts after claim."""
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
    )
    svc = LeaseLifecycleService(session)
    claimed = svc.claim_eligible_attempt(worker_id=worker_id, membership_token=token)
    session.flush()
    assert claimed is not None

    row = session.get(MissionRow, mission.id)
    assert row is not None
    row.status = "cancelled"
    session.flush()

    with pytest.raises(LeaseRenewError, match="authority_stale"):
        svc.renew_lease(
            lease_id=claimed.lease_id,
            worker_id=worker_id,
            worker_generation=claimed.worker_generation,
            membership_token=token,
        )


def test_expire_does_not_revive_cancelled_mission_task(session) -> None:
    """V2A-003b-R: expiry must not return cancelled-authority work to ready."""
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    task = _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
    )
    svc = LeaseLifecycleService(session, default_lease_seconds=5)
    claimed = svc.claim_eligible_attempt(
        worker_id=worker_id, membership_token=token, lease_seconds=5
    )
    session.flush()
    assert claimed is not None

    row = session.get(MissionRow, mission.id)
    assert row is not None
    row.status = "cancelled"
    session.flush()

    past = claimed.expires_at + timedelta(seconds=1)
    expired = svc.expire_leases(now=past)
    session.flush()
    assert claimed.lease_id in expired
    task_row = session.get(TaskRow, task.id)
    assert task_row is not None
    assert task_row.status == "cancelled"
    assert task_row.status != "ready"


def test_claim_skips_unresolved_dependencies(session) -> None:
    """V2A-003b-R: unresolved deps leave dependent unmutated; eligible peer is claimed."""
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    blocker = _insert_ready_task(
        session, mission=mission, required_capabilities=["code.read"], priority=1
    )
    blocker.status = "running"
    session.flush()
    blocked = _insert_ready_task(
        session,
        mission=mission,
        required_capabilities=["code.read"],
        priority=2,
        dependency_ids=[blocker.id],
    )
    eligible = _insert_ready_task(
        session, mission=mission, required_capabilities=["code.read"], priority=3
    )
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
    )
    claimed = LeaseLifecycleService(session).claim_eligible_attempt(
        worker_id=worker_id, membership_token=token
    )
    session.flush()
    assert claimed is not None
    assert claimed.task_id == eligible.id
    assert session.get(TaskRow, blocked.id).status == "ready"  # type: ignore[union-attr]


def test_renew_caps_expires_at_to_renewable_until(session) -> None:
    """V2A-003b-R: renew cannot push expires_at past renewable_until; empty window fails."""
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
    )
    svc = LeaseLifecycleService(
        session, default_lease_seconds=30, renewable_horizon_seconds=40
    )
    claimed = svc.claim_eligible_attempt(
        worker_id=worker_id, membership_token=token, lease_seconds=30
    )
    session.flush()
    assert claimed is not None
    lease = session.get(TaskLeaseRow, claimed.lease_id)
    assert lease is not None
    assert lease.renewable_until is not None

    renewed = svc.renew_lease(
        lease_id=claimed.lease_id,
        worker_id=worker_id,
        worker_generation=claimed.worker_generation,
        membership_token=token,
        extend_seconds=120,
    )
    session.flush()
    assert renewed.expires_at == lease.renewable_until

    # Already at the horizon with time remaining on the lease: no positive extension window.
    just_before = lease.renewable_until - timedelta(seconds=1)
    with pytest.raises(LeaseRenewError, match="no_positive_renewal_window"):
        svc.renew_lease(
            lease_id=claimed.lease_id,
            worker_id=worker_id,
            worker_generation=claimed.worker_generation,
            membership_token=token,
            extend_seconds=10,
            now=just_before,
        )


def test_renew_rejects_terminal_task_status(session) -> None:
    """V2A-003b-R2: terminal TaskRow cannot renew even if mission stays runnable."""
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    task = _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
    )
    svc = LeaseLifecycleService(session)
    claimed = svc.claim_eligible_attempt(worker_id=worker_id, membership_token=token)
    session.flush()
    assert claimed is not None

    row = session.get(TaskRow, task.id)
    assert row is not None
    row.status = "accepted"
    session.flush()

    with pytest.raises(LeaseRenewError, match="task_terminal:accepted"):
        svc.renew_lease(
            lease_id=claimed.lease_id,
            worker_id=worker_id,
            worker_generation=claimed.worker_generation,
            membership_token=token,
        )


def test_renew_rejects_accepted_attempt(session) -> None:
    """V2A-003b-R2: attempt with accepted_result_id / terminal markers cannot renew."""
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
    )
    svc = LeaseLifecycleService(session)
    claimed = svc.claim_eligible_attempt(worker_id=worker_id, membership_token=token)
    session.flush()
    assert claimed is not None

    attempt = session.get(TaskAttemptRow, claimed.attempt_id)
    assert attempt is not None
    attempt.accepted_result_id = new_id("res_")
    attempt.status = "succeeded"
    attempt.terminal_at = claimed.expires_at
    session.flush()

    with pytest.raises(LeaseRenewError, match="attempt_terminal|attempt_accepted_result"):
        svc.renew_lease(
            lease_id=claimed.lease_id,
            worker_id=worker_id,
            worker_generation=claimed.worker_generation,
            membership_token=token,
        )


def test_expire_source_drift_via_lease_stamp_never_requeues(session) -> None:
    """V2A-003b-R2: mission source drift after claim keeps expired task non-dispatchable.

    TaskRow payload intentionally omits source_revision so task-only checks would
    miss the drift; lease/attempt stamps must fence it.
    """
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    task = _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    # Ensure payload has no source_revision marker.
    row = session.get(TaskRow, task.id)
    assert row is not None
    payload = dict(row.payload or {})
    payload.pop("source_revision", None)
    row.payload = payload
    session.flush()

    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
    )
    svc = LeaseLifecycleService(session, default_lease_seconds=5)
    claimed = svc.claim_eligible_attempt(
        worker_id=worker_id, membership_token=token, lease_seconds=5
    )
    session.flush()
    assert claimed is not None
    lease = session.get(TaskLeaseRow, claimed.lease_id)
    assert lease is not None
    assert lease.source_revision  # stamped at claim

    msn = session.get(MissionRow, mission.id)
    assert msn is not None
    msn_payload = dict(msn.payload or {})
    msn_payload["source_revision"] = "post_claim_source_v2"
    msn.payload = msn_payload
    session.flush()

    past = claimed.expires_at + timedelta(seconds=1)
    expired = svc.expire_leases(now=past)
    session.flush()
    assert claimed.lease_id in expired
    task_row = session.get(TaskRow, task.id)
    assert task_row is not None
    assert task_row.status == "superseded"
    assert task_row.status != "ready"


def test_expire_cancellation_generation_drift_never_requeues(session) -> None:
    """V2A-003b-R2: post-claim cancellation_generation bump keeps expired task non-ready."""
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    task = _insert_ready_task(session, mission=mission, required_capabilities=["code.read"])
    token = new_id("wt_")
    worker_id = _register_worker(
        session,
        project_id=mission.project_id,
        capabilities=["code.read"],
        token=token,
    )
    svc = LeaseLifecycleService(session, default_lease_seconds=5)
    claimed = svc.claim_eligible_attempt(
        worker_id=worker_id, membership_token=token, lease_seconds=5
    )
    session.flush()
    assert claimed is not None

    msn = session.get(MissionRow, mission.id)
    assert msn is not None
    msn.cancellation_generation = int(msn.cancellation_generation) + 1
    # Keep mission runnable so only stamp drift fences expiry.
    assert msn.status == "running"
    session.flush()

    past = claimed.expires_at + timedelta(seconds=1)
    expired = svc.expire_leases(now=past)
    session.flush()
    assert claimed.lease_id in expired
    task_row = session.get(TaskRow, task.id)
    assert task_row is not None
    assert task_row.status == "superseded"
    assert task_row.status != "ready"
