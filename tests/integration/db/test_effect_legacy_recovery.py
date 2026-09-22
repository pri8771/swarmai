"""Legacy recovery through the authenticated service and locked PostgreSQL store."""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text

from swarm.api.auth import AuthRegistry
from swarm.api.errors import ApiError
from swarm.tools.effect_recovery import disposition_legacy_effect
from swarm.tools.effects import EffectConflictError, EffectStoreError
from swarm.tools.v17_gateway import ReconciliationRequiredError
from tests.integration.db.test_effect_crash_window import (
    CRASH_CONTEXT,
    age,
    begin,
    row,
    setup_effect,
)
from tests.integration.db.test_effect_crash_window import (
    engine as engine,
)
from tests.integration.db.test_effect_crash_window import (
    factory as factory,
)


def _make_legacy_executing(factory, env) -> None:
    with factory.begin() as session:
        session.execute(
            text(
                "UPDATE action_effects SET payload='{}'::jsonb WHERE project_id=:p AND effect_key=:k"
            ),
            {"p": env.project_id, "k": env.effect_key},
        )


def _operator_auth(project_id):
    auth = AuthRegistry()
    token = auth.issue(
        subject="operator-17", project_ids={project_id}, roles={"operator"}, token="atk_r27e_op"
    )
    return auth, token


@pytest.mark.parametrize(
    ("roles", "projects", "authorization", "code"),
    [
        ({"operator"}, {"crash_project"}, "", "unauthorized"),
        ({"operator"}, {"crash_project"}, None, "unauthorized"),
        ({"operator"}, {"crash_project"}, "Bearer unregistered", "unauthorized"),
        ({"viewer"}, {"crash_project"}, "bearer atk_r27e_auth", "operator_required"),
        ({"operator"}, {"other_project"}, "bearer atk_r27e_auth", "forbidden_project"),
    ],
)
def test_legacy_disposition_service_auth(factory, tmp_path, roles, projects, authorization, code):
    _, _, store, _, env = setup_effect(factory, tmp_path)
    observed = begin(store, env)
    _make_legacy_executing(factory, env)
    auth = AuthRegistry()
    auth.issue(subject="caller", project_ids=projects, roles=roles, token="atk_r27e_auth")
    with pytest.raises(ApiError) as raised:
        disposition_legacy_effect(
            store=store,
            auth=auth,
            authorization=authorization,
            client_host="127.0.0.1",
            project_id=env.project_id,
            effect_key=env.effect_key,
            expected_execution=(observed["executor_id"], observed["attempt_count"], "executing"),
            reason="reviewed crash evidence",
            evidence_ref="evidence://r27e/legacy/1",
        )
    assert raised.value.code == code
    assert row(store, env)["state"] == "executing"


def test_legacy_disposition_exact_token_and_audit(factory, tmp_path):
    _, _, store, _, env = setup_effect(factory, tmp_path)
    observed = begin(store, env)
    _make_legacy_executing(factory, env)
    auth, token = _operator_auth(env.project_id)
    common = dict(
        store=store,
        auth=auth,
        authorization=f"Bearer {token}",
        client_host="203.0.113.8",
        project_id=env.project_id,
        effect_key=env.effect_key,
        reason="reviewed crash evidence",
        evidence_ref="evidence://r27e/legacy/1",
    )
    with pytest.raises(EffectConflictError, match="legacy_disposition_state_conflict"):
        disposition_legacy_effect(
            **common,
            expected_execution=(
                observed["executor_id"],
                observed["attempt_count"] + 1,
                "executing",
            ),
        )
    result = disposition_legacy_effect(
        **common,
        expected_execution=(observed["executor_id"], observed["attempt_count"], "executing"),
    )
    assert result["state"] == "unknown" and result["state_reason"] == "legacy_operator_disposition"
    assert result["attempt_count"] == observed["attempt_count"]
    assert result["legacy_disposition"]["operator"] == "operator-17"
    assert result["legacy_disposition"]["reason"] == "reviewed crash evidence"
    assert result["legacy_disposition"]["evidence_ref"] == "evidence://r27e/legacy/1"
    assert store.list_receipts(project_id=env.project_id, effect_key=env.effect_key) == []


@pytest.mark.asyncio
async def test_legacy_not_applied_keeps_audit_and_cannot_rearm(factory, tmp_path):
    path, adapter, store, gateway, env = setup_effect(factory, tmp_path)
    observed = begin(store, env)
    _make_legacy_executing(factory, env)
    auth, token = _operator_auth(env.project_id)
    disposition_legacy_effect(
        store=store,
        auth=auth,
        authorization=f"Bearer {token}",
        client_host="127.0.0.1",
        project_id=env.project_id,
        effect_key=env.effect_key,
        expected_execution=(observed["executor_id"], observed["attempt_count"], "executing"),
        reason="effect absent in provider log",
        evidence_ref="evidence://r27e/legacy/absent",
    )
    with pytest.raises(
        ReconciliationRequiredError, match="irreversible_requires_operator_disposition"
    ):
        await gateway.execute_envelope(env, context=CRASH_CONTEXT)
    reconciled = row(store, env)
    assert reconciled["state"] == "failed"
    assert reconciled["legacy_disposition"]["evidence_ref"] == "evidence://r27e/legacy/absent"
    assert adapter.call_count == 0 and adapter.reconcile_calls == 1 and not path.exists()
    with pytest.raises(EffectConflictError, match="legacy_effect_requires_policy_migration"):
        store.rearm_irreversible(
            project_id=env.project_id,
            effect_key=env.effect_key,
            operator="operator-17",
            reason="still absent",
        )
    assert adapter.call_count == 0 and row(store, env)["attempt_count"] == observed["attempt_count"]


def test_recover_orphaned_binds_stored_timeout_and_rejects_legacy(factory, tmp_path):
    _, _, store, _, env = setup_effect(factory, tmp_path)
    env.timeout_seconds = 3600
    begin(store, env)
    age(factory, env)
    with pytest.raises(EffectConflictError, match="effect_timeout_binding_mismatch"):
        store.recover_orphaned(
            project_id=env.project_id, effect_key=env.effect_key, timeout_seconds=1, grace_seconds=0
        )
    assert row(store, env)["state"] == "executing"

    assert not store.recover_orphaned(
        project_id=env.project_id,
        effect_key=env.effect_key,
        timeout_seconds=3600,
        grace_seconds=30,
    )

    _make_legacy_executing(factory, env)
    with pytest.raises(EffectConflictError, match="effect_recovery_timeout_unavailable"):
        store.recover_orphaned(
            project_id=env.project_id, effect_key=env.effect_key, timeout_seconds=1, grace_seconds=0
        )
    assert row(store, env)["state"] == "executing"


def test_concurrent_legacy_disposition_has_one_winner(factory, tmp_path):
    """Race regression: repository must lock or CAS the exact execution token."""
    _, _, store, _, env = setup_effect(factory, tmp_path)
    observed = begin(store, env)
    _make_legacy_executing(factory, env)
    expected = (observed["executor_id"], observed["attempt_count"], "executing")

    def dispose(index):
        try:
            return (
                "ok",
                store.disposition_legacy_executing(
                    project_id=env.project_id,
                    effect_key=env.effect_key,
                    operator_subject=f"operator-{index}",
                    reason="reviewed",
                    evidence_ref=f"evidence://race/{index}",
                    expected_execution=expected,
                ),
            )
        except EffectConflictError as exc:
            return ("conflict", str(exc))

    with ThreadPoolExecutor(max_workers=2) as pool:
        # Hold the row until both contenders block. Without SELECT FOR UPDATE,
        # both read executing then block only at flush, and both falsely win.
        with factory.begin() as holder:
            holder.execute(
                text("SELECT effect_id FROM action_effects WHERE effect_key=:key FOR UPDATE"),
                {"key": env.effect_key},
            )
            futures = [pool.submit(dispose, i) for i in range(2)]
            deadline = time.monotonic() + 5
            while True:
                with factory.begin() as observer:
                    waiting = observer.scalar(
                        text(
                            "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE '%action_effects%'"
                        )
                    )
                if waiting >= 2:
                    break
                if time.monotonic() > deadline:
                    pytest.fail("both disposition contenders did not reach the locked row")
                time.sleep(0.02)
        outcomes = [future.result(timeout=5) for future in futures]
    assert sorted(item[0] for item in outcomes) == ["conflict", "ok"], outcomes
    winner = next(item[1] for item in outcomes if item[0] == "ok")
    assert row(store, env)["legacy_disposition"] == winner["legacy_disposition"]


@pytest.mark.parametrize("missing", ["operator_subject", "reason", "evidence_ref", None])
def test_legacy_disposition_rejects_missing_audit_or_new_format(factory, tmp_path, missing):
    _, _, store, _, env = setup_effect(factory, tmp_path)
    observed = begin(store, env)
    kwargs = dict(
        project_id=env.project_id,
        effect_key=env.effect_key,
        operator_subject="operator",
        reason="reviewed",
        evidence_ref="evidence://synthetic/1",
        expected_execution=(observed["executor_id"], observed["attempt_count"], "executing"),
    )
    if missing:
        _make_legacy_executing(factory, env)
        kwargs[missing] = " "
        expected = "operator_reason_and_evidence_required"
    else:
        expected = "legacy_disposition_not_allowed"
    with pytest.raises(EffectStoreError, match=expected):
        store.disposition_legacy_executing(**kwargs)
    current = row(store, env)
    assert current["state"] == "executing"
    assert current["attempt_count"] == observed["attempt_count"]
    assert not current["legacy_disposition"]
