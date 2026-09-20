"""Contract serialization and invariant tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from swarm.contracts.fixtures import (
    all_required_type_instances,
    sample_inference_request,
    sample_provider_account,
    sample_unknown_quota,
)
from swarm.contracts.mission import Mission
from swarm.contracts.provider import ProviderAccount

REQUIRED_TYPES = [
    "Mission",
    "TaskSpec",
    "TaskAttempt",
    "SizeFeatures",
    "AgentProfile",
    "AgentSession",
    "GraphProposal",
    "ProviderAccount",
    "RouteSnapshot",
    "QuotaBucket",
    "Reservation",
    "AttemptReceipt",
    "CapabilityProfile",
    "EvalResult",
    "Finding",
    "ArtifactRef",
    "ContextBundle",
    "WorkerLease",
    "ToolCall",
    "Approval",
    "ActionReceipt",
    "EventEnvelope",
]


def test_all_required_types_round_trip() -> None:
    instances = all_required_type_instances()
    for name in REQUIRED_TYPES:
        obj = instances[name]
        data = obj.model_dump(mode="json")
        restored = type(obj).model_validate(data)
        assert restored.model_dump(mode="json") == data


def test_secret_fields_absent_from_envelopes() -> None:
    account = sample_provider_account()
    dumped = json.dumps(account.model_dump(mode="json"))
    assert "sk-" not in dumped
    assert "OPENROUTER_API_KEY" in dumped  # ref name only
    req = sample_inference_request()
    req_dump = json.dumps(req.model_dump(mode="json"))
    assert "sk-" not in req_dump
    assert req.secret_ref_names == ["OPENROUTER_API_KEY"]


def test_provider_account_rejects_secret_values_as_refs() -> None:
    with pytest.raises(ValidationError):
        ProviderAccount(
            service_id="x",
            account_alias="y",
            secret_ref_names=["sk-live-please-no"],
            owner="op",
        )


def test_unknown_fields_rejected() -> None:
    mission = all_required_type_instances()["Mission"]
    data = mission.model_dump(mode="json")
    data["unexpected_admin_flag"] = True
    with pytest.raises(ValidationError):
        Mission.model_validate(data)


def test_unknown_quota_remains_null() -> None:
    bucket = sample_unknown_quota()
    assert bucket.limit is None
    assert bucket.remaining is None
    dumped = bucket.model_dump(mode="json")
    assert dumped["limit"] is None
    assert dumped["remaining"] is None


def test_json_schema_export(tmp_path: Path) -> None:
    mission = all_required_type_instances()["Mission"]
    schema = type(mission).model_json_schema()
    out = tmp_path / "mission.schema.json"
    out.write_text(json.dumps(schema, indent=2))
    assert "objective" in schema["properties"]
    assert schema.get("additionalProperties") is False
