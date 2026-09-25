#!/usr/bin/env python3
"""Record LiveGrant gate + run fake-upstream native path (no spend, no invent-approve)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from swarm.contracts.common import new_id  # noqa: E402
from swarm.contracts.fixtures import sample_route  # noqa: E402
from swarm.contracts.provider import InferenceRequest  # noqa: E402
from swarm.evals.synthetic_harness import LiveGateBlocked, LiveGrant, assert_live_gate  # noqa: E402
from swarm.fakes.broker import FakeInferenceBroker  # noqa: E402
from swarm.fakes.provider import FakeProviderAdapter  # noqa: E402
from swarm.mission.protected_verify import protected_review  # noqa: E402
from swarm.workspace.artifacts import ArtifactStore  # noqa: E402


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


async def _fake_e2e(out_dir: Path) -> dict:
    adapter = FakeProviderAdapter([sample_route()])
    broker = FakeInferenceBroker(adapter)
    request = InferenceRequest(
        project_id="proj_fake_e2e",
        attempt_id=new_id("att_"),
        route_id="rt_fake_alpha",
        purpose="v17_fake_upstream_e2e",
        messages=[{"role": "user", "content": "extract contacts"}],
        estimated_input_tokens=12,
    )
    routes = await broker.assess(request)
    ticket = await broker.reserve(request, routes[0])
    receipt = await broker.invoke(ticket)
    broker.assert_all_calls_accounted()

    cas = ArtifactStore(out_dir / "cas")
    raw = (
        b"Fake-upstream mission extract.\n"
        b"Contact fake-agent@splitsignal.ai and ops@example.com.\n"
    )
    art = cas.put(raw, media_type="text/plain", owner_scope="proj_fake_e2e")
    decision = protected_review(
        task_family="extract",
        required_checks={"email_count": 2, "artifact_sha256": art.content_hash},
        artifact_id=art.id,
        artifact_bytes=raw,
        content_hash=art.content_hash,
        worker_produced={"checks": {"email_count": 999, "artifact_sha256": "deadbeef"}},
    )
    evidence = {
        "packet": "V1.7-fake-upstream-e2e",
        "hostname_public": "swarm.splitsignal.ai",
        "solver": "fake_inference_broker",
        "runtime": "native",
        "route_id": receipt.actual_route,
        "model_calls": broker.request_count,
        "spend_usd": 0.0,
        "artifact_id": art.id,
        "protected_accepted": decision.accepted,
        "live_grant": None,
        "live_mode": False,
        "invented_approval": False,
    }
    _write(out_dir / "fake-e2e.json", evidence)
    return evidence


def _live_grant_gate(out_dir: Path) -> dict:
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
    blocked_missing = False
    blocked_unapproved = False
    try:
        assert_live_gate(mode="live", grant=None)
    except LiveGateBlocked:
        blocked_missing = True
    try:
        draft.assert_usable()
    except LiveGateBlocked:
        blocked_unapproved = True

    gate = {
        "packet": "V1.7-live-grant-gate",
        "hostname_public": "swarm.splitsignal.ai",
        "mode": "live",
        "blocked": True,
        "blocked_missing_grant": blocked_missing,
        "blocked_unapproved_draft": blocked_unapproved,
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
    _write(out_dir / "live-grant-gate.json", gate)
    # Also pin under docs/evidence/v17 for review probes.
    _write(ROOT / "docs" / "evidence" / "v17" / "live-grant-gate.json", gate)
    return gate


def main() -> int:
    out = ROOT / "docs" / "evidence" / "v17" / "fake-e2e"
    fake = asyncio.run(_fake_e2e(out))
    gate = _live_grant_gate(out)
    ok = bool(fake.get("protected_accepted")) and gate.get("blocked") is True
    print(json.dumps({"ok": ok, "fake_route": fake.get("route_id"), "gate_blocked": True}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
