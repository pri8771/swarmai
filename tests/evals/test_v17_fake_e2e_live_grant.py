"""Model-backed E2E via fake upstream + LiveGrant gate record (no spend)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from swarm.contracts.common import new_id
from swarm.contracts.fixtures import sample_route, sample_task
from swarm.contracts.provider import InferenceRequest
from swarm.evals.synthetic_harness import LiveGateBlocked, LiveGrant, assert_live_gate
from swarm.fakes.broker import FakeInferenceBroker
from swarm.fakes.provider import FakeProviderAdapter
from swarm.mission.protected_verify import protected_review
from swarm.workspace.artifacts import ArtifactStore


def _request(**kwargs: object) -> InferenceRequest:
    base: dict[str, object] = {
        "project_id": "proj_fake_e2e",
        "attempt_id": new_id("att_"),
        "purpose": "v17_fake_upstream_e2e",
        "messages": [{"role": "user", "content": "extract contacts"}],
        "estimated_input_tokens": 12,
    }
    base.update(kwargs)
    return InferenceRequest(**base)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_fake_upstream_model_backed_mission_e2e(tmp_path: Path) -> None:
    adapter = FakeProviderAdapter([sample_route()])
    broker = FakeInferenceBroker(adapter)
    routes = await broker.assess(_request(route_id="rt_fake_alpha"))
    assert routes and routes[0].route_id == "rt_fake_alpha"
    request = _request(route_id=routes[0].route_id)
    ticket = await broker.reserve(request, routes[0])
    receipt = await broker.invoke(ticket)
    assert receipt.actual_route == "rt_fake_alpha"
    assert broker.request_count >= 1
    assert adapter.calls == ["rt_fake_alpha"]
    broker.assert_all_calls_accounted()

    # Produce artifact and protected-verify (worker checks ignored).
    store = ArtifactStore(tmp_path / "cas")
    payload = (
        "Fake-upstream mission extract.\n"
        "Contact fake-agent@splitsignal.ai and ops@example.com.\n"
    )
    raw = payload.encode("utf-8")
    art = store.put(
        raw,
        media_type="text/plain",
        owner_scope="proj_fake_e2e",
    )
    forged = protected_review(
        task_family="extract",
        required_checks={"email_count": 2, "artifact_sha256": art.content_hash},
        artifact_id=art.id,
        artifact_bytes=raw,
        content_hash=art.content_hash,
        worker_produced={"checks": {"email_count": 999, "artifact_sha256": "deadbeef"}},
    )
    # Server recomputes — forged worker checks do not drive acceptance alone.
    assert forged.computed.get("email_count") == 2
    assert forged.accepted is True

    evidence = {
        "packet": "V1.7-fake-upstream-e2e",
        "hostname_public": "swarm.splitsignal.ai",
        "solver": "fake_inference_broker",
        "route_id": receipt.actual_route,
        "model_calls": broker.request_count,
        "spend_usd": 0.0,
        "artifact_id": art.id,
        "protected_accepted": forged.accepted,
        "live_grant": None,
        "live_mode": False,
    }
    out = tmp_path / "fake-e2e.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    assert out.is_file()


def test_live_grant_gate_prepared_not_spent(tmp_path: Path) -> None:
    with pytest.raises(LiveGateBlocked, match="missing approved LiveGrant"):
        assert_live_gate(mode="live", grant=None)

    draft = LiveGrant(
        grant_id="lg_prepared_v17_not_approved",
        routes=("rt_free_qualified_only",),
        budget_usd=0.0,
        purpose="v17_native_model_mission",
        approved=False,
        free_routes_only=True,
        max_calls=3,
        max_tokens=4000,
        max_wall_seconds=120,
    )
    with pytest.raises(LiveGateBlocked, match="not approved"):
        draft.assert_usable()

    gate_record = {
        "packet": "V1.7-live-grant-gate",
        "hostname_public": "swarm.splitsignal.ai",
        "mode": "live",
        "blocked": True,
        "reason": "grant_prepared_but_not_approved",
        "grant": {
            "grant_id": draft.grant_id,
            "routes": list(draft.routes),
            "budget_usd": draft.budget_usd,
            "approved": draft.approved,
            "free_routes_only": draft.free_routes_only,
            "max_calls": draft.max_calls,
            "max_tokens": draft.max_tokens,
            "max_wall_seconds": draft.max_wall_seconds,
            "purpose": draft.purpose,
        },
        "spend_usd": 0,
        "invented_approval": False,
        "note": (
            "Operator must approve before live dispatch; "
            "fake upstream E2E covers mechanics."
        ),
    }
    out = tmp_path / "live-grant-gate.json"
    out.write_text(json.dumps(gate_record, indent=2) + "\n", encoding="utf-8")

    fixture_gate = assert_live_gate(mode="oracle", grant=None)
    assert fixture_gate["blocked"] is False


def test_sample_task_available_for_e2e_wiring() -> None:
    task = sample_task()
    assert task.task_family
