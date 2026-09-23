"""G12 INF-121 — local brokered concurrent inference pool (zero-spend)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from swarm.mission.brokered_inference import (
    brokered_local_chat,
    build_local_mission_broker,
)


@pytest.mark.asyncio
async def test_brokered_local_reserve_without_bypass(tmp_path: Path) -> None:
    broker = build_local_mission_broker(repo_root=tmp_path, request_limit=10)
    # Force adapter to skip network: replace execute_one with stub text.
    async def _stub(request, ticket):  # type: ignore[no-untyped-def]
        from swarm.contracts.common import new_id, utc_now
        from swarm.contracts.enums import ReservationPhase, SettlementState
        from swarm.contracts.provider import AttemptReceipt, NormalizedUsage

        broker.adapter.calls.append({"route_id": ticket.route_id})
        return AttemptReceipt(
            logical_call_id=ticket.logical_call_id,
            send_phase=ReservationPhase.SETTLED,
            finished_at=utc_now(),
            provider_request_id=new_id("prv_"),
            normalized_usage=NormalizedUsage(
                requests=1,
                input_tokens=3,
                output_tokens=2,
                extras={"text": "ok", "ok": True, "error": None, "cost_usd": 0.0},
            ),
            actual_route=ticket.route_id,
            settlement_state=SettlementState.SETTLED,
        )

    broker.adapter.execute_one = _stub  # type: ignore[method-assign]
    result = await brokered_local_chat(
        broker=broker,
        messages=[{"role": "user", "content": "ping"}],
        model="gemma3:4b",
        max_tokens=16,
    )
    assert result.ok is True
    assert result.cost_usd == 0.0
    assert result.route_id.startswith("rt_ollama_")
    assert len(broker.adapter.calls) == 1
    broker.assert_all_calls_accounted()


@pytest.mark.asyncio
async def test_concurrent_brokered_calls_share_quota(tmp_path: Path) -> None:
    broker = build_local_mission_broker(repo_root=tmp_path, request_limit=4)

    async def _stub(request, ticket):  # type: ignore[no-untyped-def]
        from swarm.contracts.common import new_id, utc_now
        from swarm.contracts.enums import ReservationPhase, SettlementState
        from swarm.contracts.provider import AttemptReceipt, NormalizedUsage

        await asyncio.sleep(0.02)
        broker.adapter.calls.append(
            {"route_id": ticket.route_id, "reservation_id": ticket.reservation_id}
        )
        return AttemptReceipt(
            logical_call_id=ticket.logical_call_id,
            send_phase=ReservationPhase.SETTLED,
            finished_at=utc_now(),
            provider_request_id=new_id("prv_"),
            normalized_usage=NormalizedUsage(
                requests=1,
                input_tokens=1,
                output_tokens=1,
                extras={"text": f"resp-{ticket.reservation_id[-6:]}", "ok": True, "cost_usd": 0.0},
            ),
            actual_route=ticket.route_id,
            settlement_state=SettlementState.SETTLED,
        )

    broker.adapter.execute_one = _stub  # type: ignore[method-assign]

    async def one(model: str) -> str:
        r = await brokered_local_chat(
            broker=broker,
            messages=[{"role": "user", "content": f"hello {model}"}],
            model=model,
            max_tokens=8,
        )
        assert r.ok
        return r.route_id

    routes = await asyncio.gather(
        one("gemma3:4b"),
        one("qwen3.5:4b"),
        one("gemma3:4b"),
    )
    assert set(routes) == {"rt_ollama_gemma3:4b", "rt_ollama_qwen3.5:4b"}
    assert len(broker.adapter.calls) == 3
    # Overlapping reservations must not double-count beyond accounted invokes.
    broker.assert_all_calls_accounted()
    live = broker.ledger._buckets["qb_local_ollama_requests"]
    assert live.model.remaining == 1
    assert live.settled == 3
