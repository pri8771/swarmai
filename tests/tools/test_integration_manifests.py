"""R29a versioned integration manifests and receipt binding."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from tests.integration.db.effect_fixtures import bind_lease
from tests.integration.db.test_effect_transactions import engine as engine
from tests.integration.db.test_effect_transactions import factory as factory

from swarm.contracts.actions import ActionReceiptV17, AdapterManifest
from swarm.db.models import ActionReceiptRow
from swarm.tools.adapter_registry import AdapterRegistry
from swarm.tools.adapters import ApiMcpAdapter, BrowserSessionAdapter, LocalSandboxAdapter
from swarm.tools.effects import DurableEffectRepository
from swarm.tools.fences import ActorContext, LeaseFenceProvider, StaticPolicyProvider
from swarm.tools.manifests import MANIFEST_DIR, load_all, load_manifest, manifest_digest
from swarm.tools.v17_gateway import ConsequentialToolGateway

EXPECTED_FIELDS = {
    "integration_id",
    "integration_version",
    "adapter_class",
    "read_data_classes",
    "write_data_classes",
    "operations",
    "network_scopes",
    "filesystem_scopes",
    "secrets_refs_required",
    "risk_class",
    "sandbox_required",
    "host_requirements",
    "user_interaction_consequential",
    "schema_version",
}


def _payload(*, integration_id="fixture.echo", version="1", adapter_class="api_mcp"):
    return {
        "schema_version": "1.0",
        "integration_id": integration_id,
        "integration_version": version,
        "adapter_class": adapter_class,
        "read_data_classes": ["fixture_read"],
        "write_data_classes": ["fixture_write"],
        "operations": {
            "echo": {
                "side_effect_class": "consequential",
                "risk_class": "medium",
                "scopes": ["fixture.scope"],
                "read_data_classes": ["fixture_read"],
                "write_data_classes": ["fixture_write"],
            }
        },
        "network_scopes": ["https://example.invalid"],
        "filesystem_scopes": [],
        "secrets_refs_required": ["fixture_ref"],
        "risk_class": "medium",
        "sandbox_required": False,
        "host_requirements": [],
        "user_interaction_consequential": False,
    }


def _write(directory: Path, payload: dict, *, name: str | None = None) -> Path:
    path = directory / (
        name or f"{payload['integration_id']}@{payload['integration_version']}.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_unknown_field_rejected(tmp_path: Path) -> None:
    payload = {**_payload(), "publisher": "not-r29a"}
    with pytest.raises(ValidationError, match="publisher"):
        load_manifest(_write(tmp_path, payload))


def test_name_content_mismatch_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manifest_name_mismatch"):
        load_manifest(_write(tmp_path, _payload(), name="other@1.json"))


def test_duplicate_manifest_rejected_across_subdirectories(tmp_path: Path) -> None:
    payload = _payload()
    _write(tmp_path / "a", payload)
    _write(tmp_path / "b", payload)
    with pytest.raises(ValueError, match="duplicate_manifest"):
        load_all(tmp_path)


@pytest.mark.parametrize(
    "secret",
    [
        "sk-abcdefgh",
        "ghp_abcdefgh",
        "AKIA123456789012",
        "-----BEGIN PRIVATE KEY-----",
        "password = fixture",
    ],
)
@pytest.mark.parametrize("location", ["key", "value"])
def test_secret_like_values_and_keys_rejected(tmp_path: Path, secret: str, location: str) -> None:
    payload = _payload()
    payload["host_requirements"] = [{secret: "safe"}] if location == "key" else [{"safe": secret}]
    with pytest.raises(ValueError, match="manifest_contains_secret_like_value"):
        load_manifest(_write(tmp_path, payload))


def test_each_adapter_refuses_a_foreign_manifest(tmp_path: Path) -> None:
    local = load_manifest(MANIFEST_DIR / "local.sandbox@1.json")
    api = load_manifest(MANIFEST_DIR / "mcp.echo@1.json")
    browser = load_manifest(MANIFEST_DIR / "browser.session@1.json")
    cases = (
        (LocalSandboxAdapter, api, {"root": tmp_path}),
        (ApiMcpAdapter, browser, {}),
        (BrowserSessionAdapter, local, {}),
    )
    for constructor, foreign, kwargs in cases:
        with pytest.raises(ValueError, match="adapter_class_mismatch"):
            constructor(foreign, **kwargs)


def test_manifest_digest_is_canonical_and_stable(tmp_path: Path) -> None:
    payload = _payload()
    compact = _write(tmp_path / "a", payload)
    reordered = {key: payload[key] for key in reversed(payload)}
    pretty = _write(tmp_path / "b", reordered)
    first, second = load_manifest(compact), load_manifest(pretty)
    expected = hashlib.sha256(
        json.dumps(first.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    assert manifest_digest(first) == manifest_digest(second) == expected


def test_new_receipt_without_manifest_digest_is_rejected() -> None:
    payload = {
        "action_id": "act_fixture",
        "effect_key": "proj:fixture",
        "project_id": "proj_fixture",
        "integration_id": "fixture.echo",
        "integration_version": "1",
        "operation": "echo",
        "destination": "mcp://fixture",
        "outcome": "succeeded",
    }
    with pytest.raises(ValidationError, match="manifest_digest"):
        ActionReceiptV17.model_validate(payload)


def test_operation_risk_cannot_exceed_manifest_ceiling() -> None:
    payload = _payload()
    payload["risk_class"] = "low"
    with pytest.raises(ValidationError, match="operation_risk_exceeds_manifest"):
        AdapterManifest.model_validate(payload)


def test_manifest_vocabulary_is_exact_frozen_subset() -> None:
    assert set(AdapterManifest.model_fields) == EXPECTED_FIELDS


@pytest.mark.integration
@pytest.mark.asyncio
async def test_postgres_receipt_binds_manifest_and_historical_read_is_nonmutating(factory) -> None:
    manifest = load_manifest(MANIFEST_DIR / "mcp.echo@1.json")
    adapter = ApiMcpAdapter(
        manifest,
        transport=lambda operation, payload: {
            "outcome": "succeeded",
            "external_id": "ext_r29a_fixture",
        },
    )
    registry = AdapterRegistry()
    registry.register(adapter)
    store = DurableEffectRepository(factory)
    gateway = ConsequentialToolGateway(
        registry=registry,
        store=store,
        fences=LeaseFenceProvider(factory),
        policy=StaticPolicyProvider({"network.https", "mcp.call"}, "v17-policy-1"),
    )
    context = ActorContext(actor="worker", project_id="proj_r29a")
    envelope = adapter.normalize(
        {
            "project_id": context.project_id,
            "destination": "mcp://echo/default",
            "body": "synthetic-r29a",
        }
    )
    envelope = bind_lease(factory, envelope)
    envelope.approval_id = gateway.make_approval(envelope, context=context).approval_id
    receipt = await gateway.execute_envelope(envelope, context=context)
    expected = manifest_digest(manifest)
    assert receipt.manifest_digest == expected

    with factory() as session:
        row = session.scalar(
            select(ActionReceiptRow).where(ActionReceiptRow.receipt_id == receipt.receipt_id)
        )
        assert row is not None and row.receipt["manifest_digest"] == expected
        historical = dict(row.receipt)
        historical.pop("manifest_digest")
        row.receipt = historical
        session.commit()

    readback = DurableEffectRepository(factory).get_receipt(envelope.action_id)
    assert readback is not None and readback.manifest_digest == "historical-unbound"
    with factory() as session:
        stored = session.scalar(
            select(ActionReceiptRow.receipt).where(
                ActionReceiptRow.receipt_id == receipt.receipt_id
            )
        )
        assert stored is not None and "manifest_digest" not in stored
