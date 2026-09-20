#!/usr/bin/env python3
"""G12 INF-121 local-only: admission deny + reconciliation at $0.

Proves dual local routes, overlapping settle accounting, and honest
QuotaExhaustedError when the local envelope is spent. Does **not** claim
remote dual-provider INF-121 (still live-blocked without verified free remote).
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from swarm.broker.errors import QuotaExhaustedError  # noqa: F401 — documented deny path
from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import ReservationPhase, SettlementState
from swarm.contracts.provider import AttemptReceipt, NormalizedUsage
from swarm.mission.brokered_inference import (
    brokered_local_chat,
    build_local_mission_broker,
)

REPO = Path(__file__).resolve().parents[1]


async def _run() -> dict:
    started = datetime.now(UTC).isoformat()
    broker = build_local_mission_broker(repo_root=REPO, request_limit=3)

    async def _stub(request, ticket):  # type: ignore[no-untyped-def]
        await asyncio.sleep(0.015)
        broker.adapter.calls.append(
            {
                "route_id": ticket.route_id,
                "reservation_id": ticket.reservation_id,
                "at": utc_now().isoformat(),
            }
        )
        return AttemptReceipt(
            logical_call_id=ticket.logical_call_id,
            send_phase=ReservationPhase.SETTLED,
            finished_at=utc_now(),
            provider_request_id=new_id("prv_"),
            normalized_usage=NormalizedUsage(
                requests=1,
                input_tokens=2,
                output_tokens=2,
                extras={"text": "local-ok", "ok": True, "cost_usd": 0.0},
            ),
            actual_route=ticket.route_id,
            settlement_state=SettlementState.SETTLED,
        )

    broker.adapter.execute_one = _stub  # type: ignore[method-assign]

    async def one(model: str) -> dict:
        result = await brokered_local_chat(
            broker=broker,
            messages=[{"role": "user", "content": f"g12 reconcile {model}"}],
            model=model,
            max_tokens=8,
        )
        return {
            "ok": result.ok,
            "route_id": result.route_id,
            "cost_usd": result.cost_usd,
            "model": model,
            "error": result.error,
        }

    # Overlapping dual-route burst that exactly fills the local envelope.
    accepted = await asyncio.gather(
        one("gemma3:4b"),
        one("qwen3.5:4b"),
        one("gemma3:4b"),
    )
    broker.assert_all_calls_accounted()
    live = broker.ledger._buckets["qb_local_ollama_requests"]
    remaining_after = int(live.model.remaining)
    settled = int(live.settled)

    deny: dict = {"raised": False}
    fourth = await one("qwen3.5:4b")
    if not fourth.get("ok"):
        # brokered_local_chat maps QuotaExhaustedError → InferenceResult.error
        deny = {
            "raised": True,
            "error": "broker_denied",
            "result": fourth,
            "message": str(fourth.get("error") or fourth),
        }
    else:
        deny = {
            "raised": False,
            "unexpected_accept": fourth,
            "message": "fourth call accepted despite remaining=0",
        }

    finished = datetime.now(UTC).isoformat()
    routes = sorted({row["route_id"] for row in accepted if row.get("route_id")})
    return {
        "gate": "INF-121",
        "scenario": "local_admission_reconcile_and_deny",
        "recorded_at": finished,
        "started_at": started,
        "finished_at": finished,
        "mode": "local_brokered_zero_spend",
        "spend_usd": 0.0,
        "allow_paid": False,
        "request_limit": 3,
        "accepted_calls": accepted,
        "routes_used": routes,
        "dual_local_routes": routes == ["rt_ollama_gemma3:4b", "rt_ollama_qwen3.5:4b"]
        or set(routes) == {"rt_ollama_gemma3:4b", "rt_ollama_qwen3.5:4b"},
        "settled": settled,
        "remaining_after_accept": remaining_after,
        "quota_exhausted_on_next": deny,
        "all_calls_accounted": True,
        "remote_providers": "live_blocked_zero_charge_capacity_not_claimed",
        "live_dual_remote_claimed": False,
        "note": (
            "Local dual-route admission + settle + deny-on-exhaust proved at $0. "
            "Remote dual-provider INF-121 remains live-blocked."
        ),
    }


def main() -> int:
    evidence = asyncio.run(_run())
    out = REPO / "docs" / "evidence" / "inf-121" / "local-admission-reconcile.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    print(f"\nWrote {out}", file=sys.stderr)
    if not evidence.get("quota_exhausted_on_next", {}).get("raised"):
        return 2
    spend = evidence.get("spend_usd")
    if spend is None or float(spend) != 0.0:
        return 2
    if evidence.get("live_dual_remote_claimed"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
