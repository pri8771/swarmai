"""R27d / ART-V17-APPROVAL-BINDING — approval integrity (Postgres).

Approvals are insert-only, revocation is monotonic, reads are project-filtered,
and legacy rows with NULL V1.7 binding columns are non-operational.
"""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import text

from swarm.contracts.common import new_id, utc_now
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import ApprovalRow, Base
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import DurableEffectRepository, EffectConflictError, EffectStoreError
from swarm.tools.v17_gateway import ApprovalInvalidError, ConsequentialToolGateway
from tests.integration.db.effect_fixtures import bind_lease

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
SCOPES = {"network.https", "mcp.call"}


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
def factory(engine):
    fac = make_session_factory(engine)
    yield fac
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE action_receipts, action_effects, approvals, missions, worker_leases "
                "RESTART IDENTITY CASCADE"
            )
        )


def _gateway(adapter: ApiMcpAdapter, factory, project: str = "proj_a") -> ConsequentialToolGateway:
    return ConsequentialToolGateway(
        adapter,
        project_id=project,
        allowed_scopes=SCOPES,
        current_lease_generation=1,
        store=DurableEffectRepository(factory),
    )


def _row(factory, approval_id: str) -> dict[str, Any]:
    sess = factory()
    try:
        row = sess.get(ApprovalRow, approval_id)
        assert row is not None
        return {
            "used_count": row.used_count,
            "revoked_at": row.revoked_at,
            "max_effect_count": row.max_effect_count,
            "constraints": dict(row.constraints or {}),
            "grantor": row.grantor,
        }
    finally:
        sess.close()


def test_put_approval_twice_rejected_and_row_unchanged(factory) -> None:
    adapter = ApiMcpAdapter()
    gw = _gateway(adapter, factory)
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "insert-only"}
    )
    env = bind_lease(factory, env)
    grant = gw.make_approval(env, max_effect_count=1)
    before = _row(factory, grant.approval_id)
    tampered = grant.model_copy(update={"max_effect_count": 99, "grantor": "attacker"})
    with pytest.raises(EffectConflictError, match="approval_already_exists"):
        gw.store.put_approval(tampered)
    assert _row(factory, grant.approval_id) == before
    # A grant object that is already revoked can never be inserted as active history.
    revoked_obj = grant.model_copy(update={"approval_id": new_id("apr_"), "revoked_at": utc_now()})
    with pytest.raises(EffectStoreError, match="approval_insert_revoked"):
        gw.store.put_approval(revoked_obj)


@pytest.mark.asyncio
async def test_put_cannot_reset_used_count(factory) -> None:
    adapter = ApiMcpAdapter()
    gw = _gateway(adapter, factory)
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "consume-once"}
    )
    env = bind_lease(factory, env)
    grant = gw.make_approval(env, max_effect_count=1)
    env.approval_id = grant.approval_id
    assert (await gw.execute_envelope(env)).outcome == "succeeded"
    assert _row(factory, grant.approval_id)["used_count"] == 1
    with pytest.raises(EffectConflictError, match="approval_already_exists"):
        gw.store.put_approval(grant.model_copy(update={"used_count": 0}))
    assert _row(factory, grant.approval_id)["used_count"] == 1
    # put_approval never trusts the object's used_count either: a fresh insert starts at 0.
    fresh = gw.store.put_approval(
        grant.model_copy(update={"approval_id": new_id("apr_"), "used_count": 7})
    )
    assert fresh.used_count == 0
    assert _row(factory, fresh.approval_id)["used_count"] == 0


@pytest.mark.asyncio
async def test_revocation_is_monotonic_and_blocks_execution(factory) -> None:
    adapter = ApiMcpAdapter()
    gw = _gateway(adapter, factory)
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "revoke-me"}
    )
    env = bind_lease(factory, env)
    grant = gw.make_approval(env, max_effect_count=3)
    env.approval_id = grant.approval_id
    assert gw.revoke_approval(grant.approval_id, revoked_by="operator", reason="changed mind")
    row = _row(factory, grant.approval_id)
    assert row["revoked_at"] is not None
    assert row["constraints"]["revocation"]["revoked_by"] == "operator"
    assert row["constraints"]["revocation"]["reason"] == "changed mind"
    # Second revocation changes nothing and reports False; the timestamp is unchanged.
    assert gw.revoke_approval(grant.approval_id, revoked_by="x", reason="y") is False
    assert _row(factory, grant.approval_id)["revoked_at"] == row["revoked_at"]
    # No public method clears revoked_at; re-put is rejected and leaves it set.
    with pytest.raises(EffectConflictError):
        gw.store.put_approval(grant.model_copy(update={"revoked_at": None}))
    assert _row(factory, grant.approval_id)["revoked_at"] == row["revoked_at"]
    with pytest.raises(ApprovalInvalidError, match="approval_expired_or_revoked_or_exhausted"):
        await gw.execute_envelope(env)
    assert adapter.call_count == 0
    assert gw.store.get(project_id="proj_a", effect_key=env.effect_key) is None


def test_revoke_wrong_project_returns_false_and_leaves_grant_active(factory) -> None:
    adapter = ApiMcpAdapter()
    gw_a = _gateway(adapter, factory, "proj_a")
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "cross-revoke"}
    )
    env = bind_lease(factory, env)
    grant = gw_a.make_approval(env)
    repo = DurableEffectRepository(factory)
    assert (
        repo.revoke_approval(
            project_id="proj_b", approval_id=grant.approval_id, revoked_by="b", reason="steal"
        )
        is False
    )
    assert _row(factory, grant.approval_id)["revoked_at"] is None
    fetched = repo.get_approval(grant.approval_id, project_id="proj_a")
    assert fetched is not None and fetched.is_active()


@pytest.mark.asyncio
async def test_legacy_null_binding_row_is_non_operational(factory) -> None:
    adapter = ApiMcpAdapter()
    gw = _gateway(adapter, factory)
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "legacy"}
    )
    env = bind_lease(factory, env)
    legacy_id = new_id("apr_")
    sess = factory()
    try:
        sess.add(
            ApprovalRow(
                id=legacy_id,
                payload_hash=env.payload_hash,
                permitted_operation="mcp.echo.echo",
                destination=env.destination,
                grantor="legacy",
                expires_at=utc_now() + timedelta(hours=1),
                revoked_at=None,
                payload={},
                project_id="proj_a",
                actor="worker",
                integration_id=env.integration_id,
                integration_version=env.integration_version,
                operation=env.operation,
                effect_key=None,
                max_effect_count=1,
                used_count=0,
                policy_version=None,  # NULL V1.7 binding column
                constraints={},
            )
        )
        sess.commit()
    finally:
        sess.close()
    assert gw.store.get_approval(legacy_id, project_id="proj_a") is None
    env.approval_id = legacy_id
    with pytest.raises(ApprovalInvalidError, match="unknown_approval"):
        await gw.execute_envelope(env)
    assert adapter.call_count == 0
    # The row itself is untouched: no backfill.
    sess = factory()
    try:
        row = sess.get(ApprovalRow, legacy_id)
        assert row is not None and row.policy_version is None
    finally:
        sess.close()


@pytest.mark.asyncio
async def test_project_b_cannot_fetch_project_a_approval(factory) -> None:
    adapter = ApiMcpAdapter()
    gw_a = _gateway(adapter, factory, "proj_a")
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "isolation"}
    )
    env = bind_lease(factory, env)
    grant = gw_a.make_approval(env)
    repo = DurableEffectRepository(factory)
    assert repo.get_approval(grant.approval_id, project_id="proj_b") is None
    assert repo.get_approval(new_id("apr_"), project_id="proj_b") is None  # same answer
    assert repo.get_approval(grant.approval_id, project_id="proj_a") is not None
    # Through the gateway, project B presenting A's approval id sees only unknown_approval.
    gw_b = _gateway(ApiMcpAdapter(), factory, "proj_b")
    env_b = adapter.normalize(
        {"project_id": "proj_b", "destination": "mcp://echo/default", "body": "isolation"}
    )
    env_b = bind_lease(factory, env_b)
    env_b.approval_id = grant.approval_id
    with pytest.raises(ApprovalInvalidError, match="unknown_approval"):
        await gw_b.execute_envelope(env_b)
