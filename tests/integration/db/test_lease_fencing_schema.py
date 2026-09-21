"""V2A-003a / ART-V15-LEASE-FENCING — schema + repository evidence (Postgres)."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.lease_fencing import (
    RawTokenPersistenceError,
    TaskAttemptRepository,
    TaskLeaseRepository,
    WorkerRegistrationRepository,
    WorkerResultRepository,
)
from swarm.db.models import Base, TaskAttemptRow, TaskRow, WorkerLeaseRow
from swarm.db.repositories import MissionRepository
from swarm.db.token_hash import hash_membership_token, verify_membership_token

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[3]
DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)


def _alembic_config(url: str) -> Config:
    cfg = Config(str(REPO / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _unique_mission():
    mission = sample_mission()
    return mission.model_copy(update={"id": new_id("msn_")})


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


def test_alembic_upgrade_empty_db(engine) -> None:
    cfg = _alembic_config(DATABASE_URL)
    command.upgrade(cfg, "head")
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    assert "worker_leases" in tables
    assert "task_attempts" in tables
    assert "task_leases" in tables
    assert "worker_results" in tables
    worker_cols = {c["name"] for c in insp.get_columns("worker_leases")}
    assert {
        "project_id",
        "token_hash",
        "token_id",
        "trust_class",
        "resource_payload",
    } <= worker_cols
    assert "token" not in worker_cols
    attempt_cols = {c["name"] for c in insp.get_columns("task_attempts")}
    assert {
        "project_id",
        "mission_id",
        "task_revision",
        "input_digest",
        "accepted_result_id",
    } <= attempt_cols


def test_migration_preserves_legacy_worker_and_attempt_rows(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    task_id = new_id("tsk_")
    task = sample_task(mission_id=mission.id)
    session.add(
        TaskRow(
            id=task_id,
            project_id=mission.project_id,
            mission_id=mission.id,
            objective=task.objective,
            task_family=task.task_family,
            status=task.status.value,
            graph_revision=1,
            priority=task.priority,
            scopes=[],
            dependency_ids=[],
            payload={},
        )
    )
    session.flush()
    legacy_worker = WorkerLeaseRow(
        worker_id=new_id("wrk_"),
        node_identity="node-legacy",
        architecture="arm64",
        runtime_version="1.0",
        capacity_units=1.0,
        lease_generation=1,
        status="online",
        heartbeat_at=utc_now(),
        labels=[],
        capabilities=["code.read"],
        project_id=None,
        token_hash=None,
        token_id=None,
        privacy_classes=[],
        resource_payload={},
    )
    session.add(legacy_worker)
    legacy_attempt = TaskAttemptRow(
        attempt_id=new_id("att_"),
        task_id=task_id,
        agent_profile_id="ap_legacy",
        status="running",
        started_at=utc_now(),
        payload={},
    )
    session.add(legacy_attempt)
    session.flush()
    assert session.get(WorkerLeaseRow, legacy_worker.worker_id) is not None
    loaded = session.get(TaskAttemptRow, legacy_attempt.attempt_id)
    assert loaded is not None
    assert loaded.project_id is None
    assert loaded.accepted_result_id is None
    modern = TaskAttemptRepository(session).insert(
        task_id=task_id,
        agent_profile_id="ap_modern",
        status="running",
        project_id=mission.project_id,
        mission_id=mission.id,
        task_revision=2,
        input_digest="sha256:deadbeef",
        source_revision="src_1",
    )
    session.flush()
    assert modern.project_id == mission.project_id
    assert modern.task_revision == 2


def test_registration_persists_hash_not_raw_token(session) -> None:
    raw_token = "wt_must_never_hit_disk_" + new_id("x")
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    workers = WorkerRegistrationRepository(session)
    row, token_id = workers.upsert_registration(
        worker_id=new_id("wrk_"),
        project_id=mission.project_id,
        node_identity="node-a",
        architecture="arm64",
        runtime_version="py3.12",
        capacity_units=2.0,
        membership_token=raw_token,
        trust_class="standard",
        software_version="0.1.0",
        build_sha="deadbeef",
    )
    session.flush()
    assert row.token_id == token_id
    assert row.token_hash == hash_membership_token(raw_token)
    assert verify_membership_token(token=raw_token, token_hash=row.token_hash or "")
    dumped = {c.key: getattr(row, c.key) for c in row.__table__.columns}
    assert raw_token not in {str(v) for v in dumped.values()}
    assert "token" not in dumped
    assert dumped["token_hash"] != raw_token

    with pytest.raises(RawTokenPersistenceError):
        workers.upsert_registration(
            worker_id=new_id("wrk_"),
            project_id=mission.project_id,
            node_identity="node-b",
            architecture="arm64",
            runtime_version="py3.12",
            capacity_units=1.0,
            membership_token="wt_ok",
            resource_payload={"token": "wt_leaked"},
        )


def test_attempt_lease_result_repository_roundtrip(session) -> None:
    mission = _unique_mission()
    MissionRepository(session).insert(mission)
    session.flush()
    task = sample_task(mission_id=mission.id)
    task_id = new_id("tsk_")
    session.add(
        TaskRow(
            id=task_id,
            project_id=mission.project_id,
            mission_id=mission.id,
            objective=task.objective,
            task_family=task.task_family,
            status=task.status.value,
            graph_revision=1,
            priority=100,
            scopes=[],
            dependency_ids=[],
            payload={},
        )
    )
    session.flush()
    worker_id = new_id("wrk_")
    WorkerRegistrationRepository(session).upsert_registration(
        worker_id=worker_id,
        project_id=mission.project_id,
        node_identity="node-c",
        architecture="arm64",
        runtime_version="py3.12",
        capacity_units=1.0,
        membership_token="wt_roundtrip",
        generation=3,
    )
    attempt = TaskAttemptRepository(session).insert(
        task_id=task_id,
        agent_profile_id="ap_1",
        status="leased",
        project_id=mission.project_id,
        mission_id=mission.id,
        worker_id=worker_id,
        lease_generation=3,
        task_revision=1,
        input_digest="sha256:abc",
        source_revision="rev_a",
    )
    lease = TaskLeaseRepository(session).insert(
        attempt_id=attempt.attempt_id,
        task_id=task_id,
        mission_id=mission.id,
        project_id=mission.project_id,
        worker_id=worker_id,
        worker_generation=3,
        expires_at=utc_now() + timedelta(seconds=60),
        task_revision=1,
        input_digest="sha256:abc",
        source_revision="rev_a",
    )
    result = WorkerResultRepository(session).insert(
        attempt_id=attempt.attempt_id,
        lease_id=lease.lease_id,
        task_id=task_id,
        mission_id=mission.id,
        project_id=mission.project_id,
        worker_id=worker_id,
        worker_generation=3,
        result_status="ok",
        checks={"inference_ok": True},
        usage={"requests": 1, "cost_usd": 0.0},
    )
    session.flush()
    assert TaskLeaseRepository(session).list_active_for_attempt(attempt.attempt_id)
    assert WorkerResultRepository(session).get(result.result_id) is not None
    assert result.acceptance_state == "submitted"
    assert result.usage.get("cost_usd") == 0.0
