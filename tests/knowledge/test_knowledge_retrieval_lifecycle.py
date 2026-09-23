"""V2B-003b/c/d/e — permission-first retrieval, lifecycle, migration, budget."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import text

from swarm.contracts.common import new_id
from swarm.contracts.knowledge import (
    KnowledgeItem,
    KnowledgeLink,
    RetrievalActor,
    RetrievalQuery,
)
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.knowledge import (
    KnowledgeRepository,
    KnowledgeScopeError,
    MemoryStoreKnowledgeAdapter,
    PermissionFirstRetriever,
    measure_context_budget,
    seed_fixed_mission_knowledge,
)
from swarm.memory.store import MemoryRecord, MemoryStore

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)

_TRUNCATE = (
    "TRUNCATE knowledge_tombstones, knowledge_links, knowledge_items, "
    "missions, tasks, graph_revisions, findings, artifact_metadata, "
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


def _item(
    project_id: str,
    *,
    topic: str,
    body: str,
    labels: list[str],
    class_: str = "observation",
    producer: str = "system",
) -> KnowledgeItem:
    return KnowledgeItem.model_validate(
        {
            "project_id": project_id,
            "class": class_,
            "topic": topic,
            "body": body,
            "producer_type": producer,
            "permission_labels": labels,
            "retrieval_labels": [topic],
        }
    )


def test_permission_first_retrieval_order_and_receipt(session) -> None:
    repo = KnowledgeRepository(session)
    project = new_id("proj_")
    other = new_id("proj_")
    labels = ["reader"]
    repo.create_item(_item(project, topic="api", body="limit 60 rpm", labels=labels))
    repo.create_item(_item(project, topic="noise", body="lunch plans forever", labels=labels))
    secret = repo.create_item(
        _item(other, topic="api", body="other project secret", labels=labels)
    )
    inv: list[dict] = []
    retriever = PermissionFirstRetriever(repo, invalidation_log=inv)
    bundle = retriever.retrieve(
        RetrievalQuery(
            actor=RetrievalActor(
                actor_id="u1",
                project_id=project,
                permission_labels=labels,
                scopes=[f"project:{project}"],
            ),
            query_text="limit",
            token_budget=64,
            max_items=4,
        )
    )
    receipt = bundle.receipt
    assert receipt.project_id == project
    assert receipt.tokens_used <= 64
    assert receipt.tokens_avoided_estimate >= 0
    assert all(ref.item_id != secret.item_id for ref in receipt.selected)
    assert any(ref.topic == "api" for ref in receipt.selected)
    assert receipt.query_digest
    assert receipt.actor_scope_digest


def test_cross_project_actor_scope_denied(session) -> None:
    repo = KnowledgeRepository(session)
    retriever = PermissionFirstRetriever(repo)
    with pytest.raises(KnowledgeScopeError):
        retriever.retrieve(
            RetrievalQuery(
                actor=RetrievalActor(
                    actor_id="u1",
                    project_id="proj_a",
                    scopes=["project:proj_b"],
                ),
                query_text="x",
            )
        )


def test_supersession_changes_future_retrieval(session) -> None:
    repo = KnowledgeRepository(session)
    project = new_id("proj_")
    labels = ["reader"]
    obs = repo.create_item(_item(project, topic="ttl", body="TTL is 5m", labels=labels))
    accepted = repo.accept_fact(
        project_id=project,
        item_id=obs.item_id,
        version=obs.version,
        reviewer_ref="lead",
    )
    replacement = repo.supersede(
        project_id=project,
        old_item_id=accepted.item_id,
        old_version=accepted.version,
        new_body="TTL is 10m",
        reviewer_ref="lead",
    )
    retriever = PermissionFirstRetriever(repo)
    bundle = retriever.retrieve(
        RetrievalQuery(
            actor=RetrievalActor(
                actor_id="u1",
                project_id=project,
                permission_labels=labels,
                scopes=[f"project:{project}"],
            ),
            query_text="TTL",
            topics=["ttl"],
        )
    )
    bodies = [i.body for i in bundle.items]
    assert any("10m" in b for b in bodies)
    assert not any(i.version == accepted.version and i.acceptance_state == "accepted" for i in bundle.items)
    assert replacement.acceptance_state == "accepted"


def test_contradiction_set_in_receipt(session) -> None:
    repo = KnowledgeRepository(session)
    project = new_id("proj_")
    labels = ["reader"]
    a = repo.create_item(_item(project, topic="x", body="A says yes", labels=labels))
    b = repo.create_item(_item(project, topic="x", body="B says no", labels=labels))
    repo.record_contradiction(
        project_id=project,
        left_item_id=a.item_id,
        left_version=1,
        right_item_id=b.item_id,
        right_version=1,
    )
    bundle = PermissionFirstRetriever(repo).retrieve(
        RetrievalQuery(
            actor=RetrievalActor(
                actor_id="u1",
                project_id=project,
                permission_labels=labels,
                scopes=[f"project:{project}"],
            ),
            query_text="says",
            topics=["x"],
        )
    )
    flat = {i for pair in bundle.receipt.conflict_sets for i in pair}
    assert a.item_id in flat and b.item_id in flat


def test_tombstone_invalidates_summary(session) -> None:
    repo = KnowledgeRepository(session)
    project = new_id("proj_")
    labels = ["reader"]
    inv: list[dict] = []
    src = repo.create_item(_item(project, topic="src", body="source fact", labels=labels))
    summary = repo.create_item(
        KnowledgeItem.model_validate(
            {
                "project_id": project,
                "class": "summary",
                "topic": "src",
                "body": "summary of source",
                "producer_type": "system",
                "permission_labels": labels,
            }
        )
    )
    repo.add_link(
        KnowledgeLink(
            project_id=project,
            from_item_id=summary.item_id,
            from_version=1,
            relation="summarizes",
            to_item_id=src.item_id,
            to_version=1,
        )
    )
    repo.tombstone(
        project_id=project, item_id=src.item_id, reason_class="test", invalidation_log=inv
    )
    latest_summary = repo.get_latest(project_id=project, item_id=summary.item_id)
    assert latest_summary is not None
    assert latest_summary.acceptance_state == "disputed"
    assert any(e["kind"] == "summary_invalidated" for e in inv)
    assert any(e["kind"] == "prompt_assembly_invalidate" for e in inv)
    bundle = PermissionFirstRetriever(repo, invalidation_log=inv).retrieve(
        RetrievalQuery(
            actor=RetrievalActor(
                actor_id="u1",
                project_id=project,
                permission_labels=labels,
                scopes=[f"project:{project}"],
            ),
            query_text="summary",
            classes=["summary"],
        )
    )
    # Disputed summaries may still appear unless invalidated filter hides them —
    # invalidated_summary omission applies when class=summary and in log.
    assert bundle.receipt.omitted_reason_counts.get("invalidated_summary", 0) >= 1 or not any(
        i.item_id == summary.item_id for i in bundle.items
    )


def test_memory_adapter_never_auto_accepts(session, tmp_path: Path) -> None:
    store = MemoryStore(tmp_path)
    project = new_id("proj_")
    store.append(
        MemoryRecord(
            memory_id=new_id("mem_"),
            project_id=project,
            mission_id="msn_1",
            kind="durable_fact",
            topic="goal",
            content="ship V1.6 knowledge",
            provenance="mission:msn_1",
            tokens_estimate=5,
            confidence=1.0,
            tags=["goal"],
        )
    )
    store.append(
        MemoryRecord(
            memory_id=new_id("mem_"),
            project_id="",
            mission_id=None,
            kind="model_obs",
            topic="bad",
            content="no project",
            provenance="x",
            tokens_estimate=1,
        )
    )
    repo = KnowledgeRepository(session)
    report = MemoryStoreKnowledgeAdapter(repo).migrate(
        store, default_permission_labels=["migrated"]
    )
    assert report.imported == 1
    assert report.quarantined == 1
    item = repo.get_item(project_id=project, item_id=report.item_ids[0], version=1)
    assert item is not None
    assert item.class_ == "observation"
    assert item.acceptance_state == "unreviewed"
    assert item.payload.get("legacy_kind") == "durable_fact"


def test_context_budget_fixed_mission_set(session) -> None:
    repo = KnowledgeRepository(session)
    project = new_id("proj_")
    other = new_id("proj_")
    labels = ["reader"]
    seed_fixed_mission_knowledge(repo, project_id=project, permission_labels=labels)
    repo.create_item(_item(other, topic="secret", body="foreign only", labels=labels))
    report = measure_context_budget(
        repo,
        project_id=project,
        permission_labels=labels,
        query_text="rate limit",
        token_budget=40,
        other_project_id=other,
    )
    assert report.cross_project_leaks == 0
    assert report.tokens_loaded <= 40
    assert report.tokens_avoided >= 0
    assert report.task_quality.startswith("UNKNOWN")
    assert report.mission_set_size >= 5
