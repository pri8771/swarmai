"""V2B-004a–e / ART-V17 — consequential gateway, adapters, recovery, negatives."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.integration.db.effect_fixtures import bind_lease
from tests.integration.db.test_effect_transactions import engine as engine
from tests.integration.db.test_effect_transactions import factory as factory

from swarm.contracts.actions import BrowserSessionRef
from swarm.tools.adapters import ApiMcpAdapter, BrowserSessionAdapter, LocalSandboxAdapter
from swarm.tools.effects import DurableEffectRepository, InMemoryEffectStore
from swarm.tools.session_recovery import SessionRecoveryService
from swarm.tools.v17_gateway import (
    ApprovalInvalidError,
    CancellationFenceError,
    ConsequentialToolGateway,
    ReconciliationRequiredError,
    StaleLeaseError,
    ToolAuthorizationError,
)


def _gw(adapter, *, project: str, scopes: set[str], store, lease: int = 1, cancel: int = 0):
    return ConsequentialToolGateway(
        adapter,
        project_id=project,
        allowed_scopes=scopes,
        current_lease_generation=lease,
        current_cancellation_generation=cancel,
        store=store,
    )


def _bind(factory, envelope):
    return bind_lease(factory, envelope)


def _reuse_binding(source, replay):
    replay.mission_id = source.mission_id
    replay.task_id = source.task_id
    replay.attempt_id = source.attempt_id
    replay.lease_generation = source.lease_generation
    replay.cancellation_generation = source.cancellation_generation
    replay.actor = source.actor
    return replay


def _explicit_generations(envelope):
    envelope.lease_generation = 1
    envelope.cancellation_generation = 0
    return envelope


@pytest.mark.asyncio
async def test_d3_local_sandbox_adapter(tmp_path: Path) -> None:
    adapter = LocalSandboxAdapter(root=tmp_path)
    gw = _gw(adapter, project="proj_a", scopes={"sandbox.fs"}, store=InMemoryEffectStore())
    env = _explicit_generations(
        adapter.normalize(
            {
                "project_id": "proj_a",
                "text": "hello",
                "path": "note.txt",
                "operation": "write_text",
            }
        )
    )
    # local is idempotent — no approval required at low risk
    receipt = await gw.execute_envelope(env)
    assert receipt.outcome == "succeeded"
    assert (tmp_path / "note.txt").read_text() == "hello"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_d3_api_mcp_requires_approval_and_dedupes(factory) -> None:
    adapter = ApiMcpAdapter()
    store = DurableEffectRepository(factory)
    gw = _gw(
        adapter,
        project="proj_a",
        scopes={"network.https", "mcp.call"},
        store=store,
    )
    req = {
        "project_id": "proj_a",
        "destination": "mcp://echo/default",
        "body": "ping",
        "operation": "echo",
    }
    env = _bind(factory, adapter.normalize(req))
    gw = _gw(adapter, project=env.project_id, scopes={"network.https", "mcp.call"}, store=store)
    approval = gw.make_approval(env)
    env.approval_id = approval.approval_id
    first = await gw.execute_envelope(env)
    assert first.outcome == "succeeded"
    assert adapter.call_count == 1
    # Retry same effect — no second execution
    env2 = _reuse_binding(env, adapter.normalize(req))
    env2.approval_id = approval.approval_id
    # Same payload → same effect_key; reserve returns succeeded
    second = await gw.execute_envelope(env2)
    assert second.outcome == "succeeded"
    assert adapter.call_count == 1


@pytest.mark.asyncio
async def test_wrong_project_denied() -> None:
    adapter = ApiMcpAdapter()
    gw = _gw(
        adapter, project="proj_a", scopes={"network.https", "mcp.call"}, store=InMemoryEffectStore()
    )
    env = adapter.normalize(
        {"project_id": "proj_b", "destination": "mcp://echo/default", "body": "x"}
    )
    with pytest.raises(ToolAuthorizationError, match="wrong_project"):
        await gw.execute_envelope(env)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_altered_payload_after_approval(factory) -> None:
    adapter = ApiMcpAdapter()
    gw = _gw(
        adapter,
        project="proj_a",
        scopes={"network.https", "mcp.call"},
        store=DurableEffectRepository(factory),
    )
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "one"}
    )
    env = _bind(factory, env)
    gw = _gw(
        adapter,
        project=env.project_id,
        scopes={"network.https", "mcp.call"},
        store=DurableEffectRepository(factory),
        lease=env.lease_generation,
        cancel=env.cancellation_generation,
    )
    approval = gw.make_approval(env)
    env.normalized_payload["body"] = "two"
    env.payload_hash = ""
    env.effect_key = ""
    env.idempotency_key = ""
    env.ensure_hashes()
    env.approval_id = approval.approval_id
    with pytest.raises(ApprovalInvalidError, match="payload"):
        await gw.execute_envelope(env)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_changed_destination_denied(factory) -> None:
    adapter = ApiMcpAdapter()
    gw = _gw(
        adapter,
        project="proj_a",
        scopes={"network.https", "mcp.call"},
        store=DurableEffectRepository(factory),
    )
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "one"}
    )
    env = _bind(factory, env)
    gw = _gw(
        adapter,
        project=env.project_id,
        scopes={"network.https", "mcp.call"},
        store=DurableEffectRepository(factory),
        lease=env.lease_generation,
        cancel=env.cancellation_generation,
    )
    approval = gw.make_approval(env)
    env.destination = "mcp://echo/other"
    env.payload_hash = ""
    env.effect_key = ""
    env.idempotency_key = ""
    env.ensure_hashes()
    env.approval_id = approval.approval_id
    with pytest.raises(ApprovalInvalidError, match="destination"):
        await gw.execute_envelope(env)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_expired_and_revoked_approval(factory) -> None:
    adapter = ApiMcpAdapter()
    gw = _gw(
        adapter,
        project="proj_a",
        scopes={"network.https", "mcp.call"},
        store=DurableEffectRepository(factory),
    )
    env = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "x"}
    )
    env = _bind(factory, env)
    gw = _gw(
        adapter,
        project=env.project_id,
        scopes={"network.https", "mcp.call"},
        store=DurableEffectRepository(factory),
        lease=env.lease_generation,
        cancel=env.cancellation_generation,
    )
    expired = gw.make_approval(env, expires_in_seconds=-1)
    env.approval_id = expired.approval_id
    with pytest.raises(ApprovalInvalidError):
        await gw.execute_envelope(env)
    env2 = adapter.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "y"}
    )
    env2 = _reuse_binding(env, env2)
    revoked = gw.make_approval(env2)
    assert gw.revoke_approval(revoked.approval_id, revoked_by="operator", reason="test")
    env2.approval_id = revoked.approval_id
    with pytest.raises(ApprovalInvalidError):
        await gw.execute_envelope(env2)


@pytest.mark.asyncio
async def test_unsafe_redirect_and_denied_scopes(tmp_path: Path) -> None:
    browser = BrowserSessionAdapter()
    gw = _gw(browser, project="proj_a", scopes={"browser.session"}, store=InMemoryEffectStore())
    env = browser.normalize(
        {
            "project_id": "proj_a",
            "operation": "submit",
            "destination": "https://evil.test/phish",
            "site_origin": "https://example.test",
            "session_alias": "s1",
        }
    )
    with pytest.raises(PermissionError, match="unsafe_redirect|destination"):
        await gw.execute_envelope(env)

    local = LocalSandboxAdapter(root=tmp_path)
    gw2 = _gw(local, project="proj_a", scopes=set(), store=InMemoryEffectStore())
    env2 = local.normalize({"project_id": "proj_a", "text": "x", "path": "a.txt"})
    with pytest.raises(ToolAuthorizationError):
        await gw2.execute_envelope(env2)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stale_lease_and_cancel_generation(factory) -> None:
    adapter = ApiMcpAdapter()
    env = adapter.normalize(
        {
            "project_id": "proj_a",
            "destination": "mcp://echo/default",
            "body": "x",
            "lease_generation": 1,
            "cancellation_generation": 3,
        }
    )
    env = _bind(factory, env)
    current_lease = env.lease_generation
    current_cancel = env.cancellation_generation
    gw = _gw(
        adapter,
        project=env.project_id,
        scopes={"network.https", "mcp.call"},
        lease=current_lease + 1,
        cancel=current_cancel + 3,
        store=DurableEffectRepository(factory),
    )
    env.lease_generation = current_lease
    env.cancellation_generation = current_cancel + 3
    approval = gw.make_approval(env)
    env.approval_id = approval.approval_id
    with pytest.raises(StaleLeaseError):
        await gw.execute_envelope(env)

    env2 = adapter.normalize(
        {
            "project_id": "proj_a",
            "destination": "mcp://echo/default",
            "body": "z",
            "lease_generation": 2,
            "cancellation_generation": 0,
        }
    )
    env2 = _reuse_binding(env, env2)
    env2.lease_generation = current_lease + 1
    env2.cancellation_generation = current_cancel
    approval2 = gw.make_approval(env2)
    env2.approval_id = approval2.approval_id
    with pytest.raises(CancellationFenceError):
        await gw.execute_envelope(env2)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unknown_outcome_requires_reconcile_no_blind_retry(factory) -> None:
    adapter = ApiMcpAdapter()
    gw = _gw(
        adapter,
        project="proj_a",
        scopes={"network.https", "mcp.call"},
        store=DurableEffectRepository(factory),
    )
    env = _bind(
        factory,
        adapter.normalize(
            {
                "project_id": "proj_a",
                "destination": "mcp://echo/default",
                "body": "x",
                "force_unknown": True,
            }
        ),
    )
    gw = _gw(
        adapter,
        project=env.project_id,
        scopes={"network.https", "mcp.call"},
        store=DurableEffectRepository(factory),
    )
    approval = gw.make_approval(env)
    env.approval_id = approval.approval_id
    receipt = await gw.execute_envelope(env)
    assert receipt.outcome == "unknown"
    calls_after_unknown = adapter.call_count
    # Blind retry must not execute again
    with pytest.raises(ReconciliationRequiredError):
        await gw.execute_envelope(env)
    assert adapter.call_count == calls_after_unknown


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_recovery_login_does_not_submit(factory) -> None:
    adapter = BrowserSessionAdapter()
    gw = _gw(
        adapter,
        project="proj_a",
        scopes={"browser.session"},
        store=DurableEffectRepository(factory),
    )
    # Approved submit envelope
    submit_env = adapter.normalize(
        {
            "project_id": "proj_a",
            "operation": "submit",
            "destination": "https://example.test/form",
            "site_origin": "https://example.test",
            "session_alias": "s_rec",
            "profile_alias": "p1",
            "form": {"field": "1"},
        }
    )
    submit_env = _bind(factory, submit_env)
    gw = _gw(
        adapter,
        project=submit_env.project_id,
        scopes={"browser.session"},
        lease=submit_env.lease_generation,
        cancel=submit_env.cancellation_generation,
        store=DurableEffectRepository(factory),
    )
    approval = gw.make_approval(submit_env)
    submit_env.approval_id = approval.approval_id

    ref = BrowserSessionRef(
        session_alias="s_rec",
        profile_alias="p1",
        site_origin="https://example.test",
        intended_destination="https://example.test/form",
        signed_out=True,
        approved_action_id=submit_env.action_id,
    )
    recovery = SessionRecoveryService(gw, adapter)
    original_normalize = adapter.normalize

    def normalize_with_authority(request):
        return _reuse_binding(submit_env, original_normalize(request))

    adapter.normalize = normalize_with_authority
    result = await recovery.recover(
        session_ref=ref, approved_envelope=submit_env, perform_human_login=True
    )
    assert result.signed_out_detected is True
    assert result.login_implied_submit is False
    assert result.preserved_destination == "https://example.test/form"
    assert submit_env.effect_key not in adapter._submitted  # noqa: SLF001
    assert result.receipt_outcome == "succeeded"


@pytest.mark.asyncio
async def test_filesystem_escape_denied(tmp_path: Path) -> None:
    adapter = LocalSandboxAdapter(root=tmp_path)
    gw = _gw(adapter, project="proj_a", scopes={"sandbox.fs"}, store=InMemoryEffectStore())
    env = adapter.normalize({"project_id": "proj_a", "text": "x", "path": "../escape.txt"})
    with pytest.raises(PermissionError, match="filesystem_path_escape"):
        await gw.execute_envelope(env)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_three_integration_classes_share_boundary(tmp_path: Path, factory) -> None:
    """V1.7 acceptance: local + API/MCP + browser use same gateway boundary."""
    local = LocalSandboxAdapter(root=tmp_path)
    api = ApiMcpAdapter()
    browser = BrowserSessionAdapter()
    browser.register_session(
        BrowserSessionRef(
            session_alias="s1",
            profile_alias="p1",
            site_origin="https://example.test",
            intended_destination="https://example.test/ok",
            signed_out=False,
        )
    )

    gw_local = _gw(local, project="proj_a", scopes={"sandbox.fs"}, store=InMemoryEffectStore())
    gw_api = _gw(
        api,
        project="proj_a",
        scopes={"network.https", "mcp.call"},
        store=DurableEffectRepository(factory),
    )
    gw_browser = _gw(
        browser, project="proj_a", scopes={"browser.session"}, store=InMemoryEffectStore()
    )

    r1 = await gw_local.execute_request(
        {
            "project_id": "proj_a",
            "text": "a",
            "path": "a.txt",
            "lease_generation": 1,
            "cancellation_generation": 0,
        }
    )
    env_api = api.normalize(
        {"project_id": "proj_a", "destination": "mcp://echo/default", "body": "b"}
    )
    env_api = _bind(factory, env_api)
    gw_api = _gw(
        api,
        project=env_api.project_id,
        scopes={"network.https", "mcp.call"},
        lease=env_api.lease_generation,
        cancel=env_api.cancellation_generation,
        store=DurableEffectRepository(factory),
    )
    env_api.approval_id = gw_api.make_approval(env_api).approval_id
    r2 = await gw_api.execute_envelope(env_api)
    env_br = browser.normalize(
        {
            "project_id": "proj_a",
            "operation": "navigate",
            "destination": "https://example.test/ok",
            "site_origin": "https://example.test",
            "session_alias": "s1",
        }
    )
    env_br.lease_generation = 1
    env_br.cancellation_generation = 0
    r3 = await gw_browser.execute_envelope(env_br)
    assert {r1.outcome, r2.outcome, r3.outcome} == {"succeeded"}
    assert r1.integration_id == "local.sandbox"
    assert r2.integration_id == "api.mcp.echo"
    assert r3.integration_id == "browser.session"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cancel_before_execute(factory) -> None:
    adapter = ApiMcpAdapter()
    store = DurableEffectRepository(factory)
    gw = _gw(
        adapter,
        project="proj_a",
        scopes={"network.https", "mcp.call"},
        cancel=1,
        store=store,
    )
    env = adapter.normalize(
        {
            "project_id": "proj_a",
            "destination": "mcp://echo/default",
            "body": "cancel-me",
            "cancellation_generation": 0,
        }
    )
    env = _bind(factory, env)
    gw = _gw(
        adapter,
        project=env.project_id,
        scopes={"network.https", "mcp.call"},
        lease=env.lease_generation,
        cancel=env.cancellation_generation + 1,
        store=store,
    )
    approval = gw.make_approval(env)
    env.approval_id = approval.approval_id
    with pytest.raises(CancellationFenceError):
        await gw.execute_envelope(env)
    assert adapter.call_count == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_durable_effect_repository_reserve_finalize_idempotent(factory) -> None:
    """Postgres-backed D1 path through the shared isolated fixture."""
    adapter = ApiMcpAdapter()
    store = DurableEffectRepository(factory)
    gw = _gw(
        adapter,
        project="proj_a",
        scopes={"network.https", "mcp.call"},
        store=store,
    )
    req = {
        "project_id": "proj_a",
        "destination": "mcp://echo/default",
        "body": "durable-ping",
    }
    env = _bind(factory, adapter.normalize(req))
    gw = _gw(adapter, project=env.project_id, scopes={"network.https", "mcp.call"}, store=store)
    env.approval_id = gw.make_approval(env).approval_id
    first = await gw.execute_envelope(env)
    assert first.outcome == "succeeded"
    env2 = _reuse_binding(env, adapter.normalize(req))
    env2.approval_id = env.approval_id
    second = await gw.execute_envelope(env2)
    assert second.outcome == "succeeded"
    assert adapter.call_count == 1
    stored = store.get(project_id="proj_a", effect_key=env.effect_key)
    assert stored is not None
    assert stored["state"] == "succeeded"
