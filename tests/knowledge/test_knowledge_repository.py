"""V2B-003a / ART-V16 — versioned knowledge repository tests."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from swarm.contracts.common import new_id
from swarm.contracts.knowledge import KnowledgeItem, KnowledgeLink, assert_model_output_class
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.knowledge import KnowledgeRepository, KnowledgeScopeError, KnowledgeWriteError

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


def test_model_output_cannot_be_accepted_fact() -> None:
    with pytest.raises(ValueError, match="model_output_cannot_be_accepted_fact"):
        assert_model_output_class("accepted_fact", producer_type="model")


def test_versioned_create_and_new_version(session) -> None:
    repo = KnowledgeRepository(session)
    project = new_id("proj_")
    item = repo.create_item(
        KnowledgeItem(
            project_id=project,
            class_="observation",
            topic="api_limit",
            body="rate limit is 60 rpm",
            producer_type="model",
            permission_labels=["project_reader"],
            provenance_refs=["src:doc1"],
            source_digests=["sha256:abc"],
        )
    )
    assert item.version == 1
    assert item.content_digest
    assert item.acceptance_state == "unreviewed"
    v2 = repo.new_version(
        project_id=project,
        item_id=item.item_id,
        body="rate limit is 120 rpm",
        producer_type="model",
    )
    assert v2.version == 2
    assert v2.body.startswith("rate limit is 120")
    latest = repo.get_latest(project_id=project, item_id=item.item_id)
    assert latest is not None and latest.version == 2


def test_accept_fact_requires_reviewer(session) -> None:
    repo = KnowledgeRepository(session)
    project = new_id("proj_")
    obs = repo.create_item(
        KnowledgeItem(
            project_id=project,
            class_="hypothesis",
            topic="cache",
            body="cache TTL should be 5m",
            producer_type="llm",
        )
    )
    with pytest.raises(KnowledgeWriteError, match="model_output_cannot_be_accepted_fact|model_cannot_self_accept"):
        repo.create_item(
            KnowledgeItem(
                project_id=project,
                class_="accepted_fact",
                topic="cache",
                body="cache TTL is 5m",
                producer_type="model",
                acceptance_state="accepted",
            )
        )
    accepted = repo.accept_fact(
        project_id=project,
        item_id=obs.item_id,
        version=obs.version,
        reviewer_ref="reviewer:lead",
    )
    assert accepted.acceptance_state == "accepted"
    assert accepted.class_ == "accepted_fact"
    assert accepted.producer_type == "reviewer"


def test_project_scope_isolation(session) -> None:
    repo = KnowledgeRepository(session)
    a = new_id("proj_")
    b = new_id("proj_")
    item = repo.create_item(
        KnowledgeItem(
            project_id=a,
            class_="observation",
            topic="secret_a",
            body="project A only",
            producer_type="system",
            permission_labels=["team_a"],
        )
    )
    assert repo.get_item(project_id=b, item_id=item.item_id, version=1) is None
    visible_b = repo.list_visible(project_id=b, permission_labels=["team_a"])
    assert all(row.project_id == b for row in visible_b)
    assert item.item_id not in {row.item_id for row in visible_b}
    visible_a = repo.list_visible(project_id=a, permission_labels=["team_a"])
    assert any(row.item_id == item.item_id for row in visible_a)


def test_cross_project_link_forbidden(session) -> None:
    repo = KnowledgeRepository(session)
    a = new_id("proj_")
    b = new_id("proj_")
    left = repo.create_item(
        KnowledgeItem(
            project_id=a, class_="observation", topic="t", body="a", producer_type="system"
        )
    )
    right = repo.create_item(
        KnowledgeItem(
            project_id=b, class_="observation", topic="t", body="b", producer_type="system"
        )
    )
    with pytest.raises((KnowledgeScopeError, KnowledgeWriteError)):
        repo.add_link(
            KnowledgeLink(
                project_id=a,
                from_item_id=left.item_id,
                from_version=1,
                relation="supports",
                to_item_id=right.item_id,
                to_version=1,
            )
        )


def test_contradiction_link_same_project(session) -> None:
    repo = KnowledgeRepository(session)
    project = new_id("proj_")
    x = repo.create_item(
        KnowledgeItem(
            project_id=project, class_="observation", topic="t", body="x", producer_type="system"
        )
    )
    y = repo.create_item(
        KnowledgeItem(
            project_id=project, class_="observation", topic="t", body="y", producer_type="system"
        )
    )
    link = repo.add_link(
        KnowledgeLink(
            project_id=project,
            from_item_id=x.item_id,
            from_version=1,
            relation="contradicts",
            to_item_id=y.item_id,
            to_version=1,
        )
    )
    assert link.relation == "contradicts"


def test_tombstone_hides_from_default_list(session) -> None:
    repo = KnowledgeRepository(session)
    project = new_id("proj_")
    item = repo.create_item(
        KnowledgeItem(
            project_id=project,
            class_="observation",
            topic="temp",
            body="will delete",
            producer_type="system",
        )
    )
    stone = repo.tombstone(project_id=project, item_id=item.item_id, reason_class="test_delete")
    assert stone.deleted_version == 1
    assert repo.get_latest(project_id=project, item_id=item.item_id) is None
    visible = repo.list_visible(project_id=project)
    assert item.item_id not in {row.item_id for row in visible}
    stored = repo.get_tombstone(
        project_id=project, item_id=item.item_id, deleted_version=1
    )
    assert stored is not None
