"""Broker-gated inference for mission workers — no direct model bypass."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

from swarm.broker.broker import SharedInferenceBroker
from swarm.broker.errors import BrokerBypassError, PolicyDeniedError, QuotaExhaustedError
from swarm.broker.ledger import LedgerConfig
from swarm.broker.policy import AdmissionPolicy, RoutePolicyContext
from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import (
    AvailabilityStatus,
    BillingMode,
    PurposeEligibility,
    QuotaDimension,
    ReservationPhase,
    SettlementState,
    WindowType,
)
from swarm.contracts.provider import (
    AttemptReceipt,
    InferenceRequest,
    NormalizedUsage,
    QuotaBucket,
    Reservation,
    RouteSnapshot,
)
from swarm.mission.inference import InferenceResult, local_chat


def _model_from_route_id(route_id: str) -> str:
    """Parse model from ``rt_ollama_{model}`` route ids (no metadata field)."""
    prefix = "rt_ollama_"
    if route_id.startswith(prefix) and len(route_id) > len(prefix):
        return route_id[len(prefix) :]
    return "gemma3:4b"


@dataclass
class _LocalAdapter:
    """Adapter that executes only via local_chat after broker admission."""

    repo_root: Path | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    async def execute_one(
        self, request: InferenceRequest, ticket: Reservation
    ) -> AttemptReceipt:
        model = _model_from_route_id(ticket.route_id)
        result = local_chat(
            messages=list(request.messages),
            model=model,
            max_tokens=int(request.max_output_tokens or 800),
            repo_root=self.repo_root,
        )
        self.calls.append(
            {
                "route_id": ticket.route_id,
                "model": model,
                "ok": result.ok,
                "reservation_id": ticket.reservation_id,
            }
        )
        usage = NormalizedUsage(
            requests=1,
            input_tokens=result.prompt_tokens or 0,
            output_tokens=result.completion_tokens or 0,
            total_tokens=(result.prompt_tokens or 0) + (result.completion_tokens or 0),
            extras={
                "text": (result.text or "")[:2000],
                "ok": result.ok,
                "error": result.error,
                "cost_usd": 0.0,
                "model": model,
            },
        )
        return AttemptReceipt(
            logical_call_id=ticket.logical_call_id,
            send_phase=ReservationPhase.SETTLED,
            finished_at=utc_now(),
            provider_request_id=new_id("prv_"),
            normalized_usage=usage,
            actual_route=ticket.route_id,
            settlement_state=SettlementState.SETTLED,
        )

    async def classify_error(self, exc: Exception) -> str:
        return type(exc).__name__


def build_local_mission_broker(
    *,
    repo_root: Path | None = None,
    models: list[str] | None = None,
    request_limit: int = 50,
) -> SharedInferenceBroker:
    models = models or ["gemma3:4b", "qwen3.5:4b"]
    routes: list[RouteSnapshot] = []
    contexts: dict[str, RoutePolicyContext] = {}
    for model in models:
        route_id = f"rt_ollama_{model}"
        route = RouteSnapshot(
            route_id=route_id,
            provider="ollama",
            account_id="pa_local_ollama",
            model_id=model,
            endpoint="http://127.0.0.1:11434",
            billing_origin="local_none",
            capability_claims=["chat"],
            observed_capabilities=["chat"],
            availability_status=AvailabilityStatus.AVAILABLE,
            quota_bucket_ids=["qb_local_ollama_requests"],
            status="local_enabled",
            observed_at=utc_now(),
        )
        routes.append(route)
        contexts[route_id] = RoutePolicyContext(
            route=route,
            qualified=True,
            qualification_rationale="local_zero_spend_loopback",
            billing_mode=BillingMode.NONE,
            purpose_eligibility=PurposeEligibility.PROTOTYPE,
            charge_verified_free=True,
            deprecated=False,
            shared_upstream_group="local_ollama",
        )
    bucket = QuotaBucket(
        bucket_id="qb_local_ollama_requests",
        scope_type="account",
        scope_id="pa_local_ollama",
        dimension=QuotaDimension.REQUESTS,
        limit=request_limit,
        remaining=request_limit,
        window_type=WindowType.ROLLING,
        reset_at=utc_now() + timedelta(hours=24),
        observed_at=utc_now(),
        source="local_loopback",
        confidence="exact",
    )
    adapter = _LocalAdapter(repo_root=repo_root)
    return SharedInferenceBroker(
        adapter,
        buckets=[bucket],
        route_contexts=contexts,
        policy=AdmissionPolicy(),
        ledger_config=LedgerConfig(),
    )


async def brokered_local_chat(
    *,
    broker: SharedInferenceBroker,
    messages: list[dict[str, str]],
    model: str = "gemma3:4b",
    max_tokens: int = 800,
    project_id: str = "proj_demo",
    purpose: str = "mission",
) -> InferenceResult:
    """Reserve → invoke through broker; never call the adapter directly."""
    route_id = f"rt_ollama_{model}"
    ctx = getattr(broker, "_contexts", {}).get(route_id)
    if ctx is None:
        return InferenceResult(
            ok=False,
            text="",
            model=model,
            route_id=route_id,
            error="route_not_registered_for_broker",
        )
    route = ctx.route
    request = InferenceRequest(
        project_id=project_id,
        attempt_id=new_id("att_"),
        route_id=route_id,
        purpose=purpose,
        messages=list(messages),
        estimated_input_tokens=sum(len(m.get("content", "")) // 4 for m in messages),
        max_output_tokens=max_tokens,
        secret_ref_names=[],
    )
    try:
        ticket = await broker.reserve(request, route)
        receipt = await broker.invoke(ticket)
    except (BrokerBypassError, PolicyDeniedError, QuotaExhaustedError) as exc:
        return InferenceResult(
            ok=False,
            text="",
            model=model,
            route_id=route_id,
            error=f"broker_denied:{type(exc).__name__}:{exc}",
        )
    usage = receipt.normalized_usage
    extras = (usage.extras if usage else {}) or {}
    text = str(extras.get("text") or "")
    ok = bool(extras.get("ok")) and bool(text)
    return InferenceResult(
        ok=ok,
        text=text,
        model=model,
        route_id=receipt.actual_route or route_id,
        prompt_tokens=usage.input_tokens if usage else None,
        completion_tokens=usage.output_tokens if usage else None,
        cost_usd=float(extras.get("cost_usd") or 0.0),
        error=None if ok else str(extras.get("error") or "empty_or_failed"),
    )


def brokered_local_chat_sync(**kwargs: Any) -> InferenceResult:
    return asyncio.run(brokered_local_chat(**kwargs))
