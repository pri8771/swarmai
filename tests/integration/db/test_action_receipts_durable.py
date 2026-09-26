"""R27a / ART-V17-APPROVAL-BINDING — durable immutable action receipts (Postgres)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, select, text

from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import ActionReceiptRow, Base
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import DurableEffectRepository, EffectConflictError
from swarm.tools.v17_gateway import ConsequentialToolGateway, ReconciliationRequiredError

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[3]
DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
PREVIOUS_HEAD = "a17effect004a0001"
# Tip after ART-V20 pursuit persistence (must stay a single head).
NEW_HEAD = "a23opsplatform0001"


def _alembic_config(url: str) -> Config:
    cfg = Config(str(REPO / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


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
def factory(engine):
    Base.metadata.create_all(engine)
    fac = make_session_factory(engine)
    yield fac
    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE action_receipts, action_effects, approvals RESTART IDENTITY CASCADE")
        )


def _gateway(adapter: ApiMcpAdapter, store: DurableEffectRepository, project: str):
    return ConsequentialToolGateway(
        adapter,
        project_id=project,
        allowed_scopes={"network.https", "mcp.call"},
        current_lease_generation=1,
        store=store,
    )


async def _execute_once(factory, project: str, body: str):
    """Approve + execute one consequential MCP echo; return (envelope, receipt, adapter)."""
    adapter = ApiMcpAdapter()
    store = DurableEffectRepository(factory)
    gw = _gateway(adapter, store, project)
    env = adapter.normalize(
        {"project_id": project, "destination": "mcp://echo/default", "body": body}
    )
    env.approval_id = gw.make_approval(env).approval_id
    receipt = await gw.execute_envelope(env)
    return env, receipt, adapter


@pytest.mark.asyncio
async def test_receipt_survives_new_repository_instance(factory) -> None:
    env, receipt, _ = await _execute_once(factory, "proj_a", "r27a-durable")
    assert receipt.outcome == "succeeded"
    fresh = DurableEffectRepository(factory)
    again = fresh.get_receipt(env.action_id)
    assert again is not None
    assert again.receipt_id == receipt.receipt_id
    assert again.attempt_number == 1
    listed = fresh.list_receipts(project_id="proj_a", effect_key=env.effect_key)
    assert [r.receipt_id for r in listed] == [receipt.receipt_id]
    terminal = fresh.terminal_receipt(project_id="proj_a", effect_key=env.effect_key)
    assert terminal is not None and terminal.receipt_id == receipt.receipt_id


@pytest.mark.asyncio
async def test_replay_returns_original_receipt_not_reminted(factory) -> None:
    adapter = ApiMcpAdapter()
    store = DurableEffectRepository(factory)
    gw = _gateway(adapter, store, "proj_a")
    req = {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "replay"}
    env = adapter.normalize(req)
    env.approval_id = gw.make_approval(env).approval_id
    first = await gw.execute_envelope(env)
    env2 = adapter.normalize(req)
    env2.approval_id = env.approval_id
    second = await gw.execute_envelope(env2)
    assert second.receipt_id == first.receipt_id
    assert second.finished_at == first.finished_at
    assert second.attempt_refs == first.attempt_refs
    assert adapter.call_count == 1
    sess = factory()
    try:
        rows = sess.scalars(
            select(ActionReceiptRow).where(ActionReceiptRow.effect_key == env.effect_key)
        ).all()
        assert len(rows) == 1
    finally:
        sess.close()


@pytest.mark.asyncio
async def test_duplicate_receipt_attempt_rejected(factory) -> None:
    env, receipt, _ = await _execute_once(factory, "proj_a", "dup-receipt")
    store = DurableEffectRepository(factory)
    with pytest.raises(EffectConflictError, match="receipt_already_recorded"):
        store.store_receipt(receipt)  # same receipt_id
    # A second distinct receipt for the same effect gets attempt_number 2, never 1 again.
    second = store.store_receipt(receipt.model_copy(update={"receipt_id": "arc_manual_2"}))
    assert second.attempt_number == 2
    listed = store.list_receipts(project_id="proj_a", effect_key=env.effect_key)
    assert [r.attempt_number for r in listed] == [1, 2]
    # Forcing a duplicate (effect_id, attempt_number) at the row level is rejected by the
    # unique constraint.
    sess = factory()
    try:
        clash = ActionReceiptRow(
            receipt_id="arc_manual_clash",
            project_id="proj_a",
            effect_id=second.effect_id or "",
            effect_key=env.effect_key,
            action_id=env.action_id,
            attempt_number=2,
            outcome="failed",
            reconciliation_state="none",
            evidence_digest="x",
            receipt={},
        )
        sess.add(clash)
        with pytest.raises(Exception, match="uq_action_receipt_effect_attempt"):
            sess.flush()
        sess.rollback()
    finally:
        sess.close()


@pytest.mark.asyncio
async def test_project_b_cannot_list_project_a_receipts(factory) -> None:
    env, receipt, _ = await _execute_once(factory, "proj_a", "isolation")
    store = DurableEffectRepository(factory)
    assert store.list_receipts(project_id="proj_b", effect_key=env.effect_key) == []
    assert store.terminal_receipt(project_id="proj_b", effect_key=env.effect_key) is None
    assert store.list_receipts(project_id="proj_a", effect_key=env.effect_key) != []


@pytest.mark.asyncio
async def test_succeeded_effect_without_receipt_fails_closed(engine, factory) -> None:
    env, receipt, _ = await _execute_once(factory, "proj_a", "orphan-succeeded")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM action_receipts"))
    adapter = ApiMcpAdapter()
    store = DurableEffectRepository(factory)
    gw = _gateway(adapter, store, "proj_a")
    env2 = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "orphan-succeeded"}
    )
    env2.approval_id = env.approval_id
    with pytest.raises(ReconciliationRequiredError, match="succeeded_effect_missing_receipt"):
        await gw.execute_envelope(env2)
    assert adapter.call_count == 0


def test_single_alembic_head_after_upgrade(engine) -> None:
    cfg = _alembic_config(DATABASE_URL)
    Base.metadata.drop_all(engine)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    heads = ScriptDirectory.from_config(cfg).get_heads()
    assert heads == [NEW_HEAD]
    command.upgrade(cfg, PREVIOUS_HEAD)
    insp = inspect(engine)
    assert "action_receipts" not in set(insp.get_table_names())
    command.upgrade(cfg, "head")
    insp = inspect(engine)
    assert "action_receipts" in set(insp.get_table_names())
    cols = {c["name"] for c in insp.get_columns("action_effects")}
    assert {"state_reason", "attempt_count", "executor_id", "approval_consumed_at"} <= cols
    uniques = {u["name"] for u in insp.get_unique_constraints("action_receipts")}
    assert "uq_action_receipt_effect_attempt" in uniques
    command.downgrade(cfg, PREVIOUS_HEAD)
    insp = inspect(engine)
    assert "action_receipts" not in set(insp.get_table_names())
    assert "state_reason" not in {c["name"] for c in insp.get_columns("action_effects")}
    command.upgrade(cfg, "head")
    with engine.begin() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert version == NEW_HEAD
