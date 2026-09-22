"""Shared ProviderAdapter base for core providers."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from swarm.contracts.common import utc_now
from swarm.contracts.enums import (
    AvailabilityStatus,
    ErrorClass,
    ReservationPhase,
    SettlementState,
)
from swarm.contracts.provider import (
    AttemptReceipt,
    InferenceRequest,
    NormalizedUsage,
    Reservation,
    RouteSnapshot,
)
from swarm.providers.catalog import DEFAULT_ENDPOINTS
from swarm.providers.secrets import SecretRef
from swarm.providers.transport.openai_compatible import (
    ProviderHttpError,
    RecordingTransport,
    TransportMode,
    normalize_openai_usage,
)


class BaseCoreAdapter:
    """OpenAI-compatible chat completions adapter with fixture replay."""

    provider_id: str = "base"
    default_model: str = "fixture-model"
    api_style: str = "openai_compatible"  # openai_compatible | gemini | cloudflare | cohere

    def __init__(
        self,
        *,
        secret_ref_names: list[str] | None = None,
        base_url: str | None = None,
        mode: TransportMode = "replay",
        fixture_path: Any = None,
        account_id: str = "pa_unverified",
        enabled: bool = False,
    ) -> None:
        if self.provider_id == "github_models":
            raise RuntimeError("GitHub Models is retired and must not be constructed")
        self.secret_refs = [SecretRef(n) for n in (secret_ref_names or [])]
        self.base_url = (base_url or DEFAULT_ENDPOINTS[self.provider_id]).rstrip("/")
        self.mode = mode
        self.enabled = enabled
        self.account_id = account_id
        self.transport = RecordingTransport(
            base_url=self.base_url,
            secret_refs=self.secret_refs,
            mode=mode,
            fixture_path=fixture_path,
        )
        self._routes: dict[str, RouteSnapshot] = {}
        self._seed_default_route()

    def _seed_default_route(self) -> None:
        route = RouteSnapshot(
            route_id=f"rt_{self.provider_id}_default",
            provider=self.provider_id,
            account_id=self.account_id,
            model_id=self.default_model,
            endpoint=self.base_url,
            billing_origin="unknown",
            capability_claims=["chat"],
            observed_capabilities=[],
            availability_status=(
                AvailabilityStatus.DISABLED if not self.enabled else AvailabilityStatus.AVAILABLE
            ),
            status="implemented_offline" if not self.enabled else "enabled",
            observed_at=utc_now(),
        )
        self._routes[route.route_id] = route

    async def discover(self) -> list[RouteSnapshot]:
        if self.provider_id == "github_models":
            return []
        # Discovery may hit /models when live; offline uses seeded route.
        if self.mode != "replay" and self.api_style == "openai_compatible":
            try:
                data = self.transport.request("GET", "/models")
                for item in data.get("data", []):
                    model_id = item.get("id")
                    if not model_id:
                        continue
                    route_id = f"rt_{self.provider_id}_{model_id}"
                    self._routes[route_id] = RouteSnapshot(
                        route_id=route_id,
                        provider=self.provider_id,
                        account_id=self.account_id,
                        model_id=model_id,
                        endpoint=self.base_url,
                        billing_origin="unknown",
                        capability_claims=["chat"],
                        observed_capabilities=["chat"],
                        availability_status=AvailabilityStatus.DISABLED,
                        status="discovered_disabled",
                        observed_at=utc_now(),
                    )
            except ProviderHttpError:
                pass
        return list(self._routes.values())

    async def inspect_account(self, account_id: str) -> dict[str, Any]:
        return {
            "account_id": account_id,
            "provider": self.provider_id,
            "secret_refs_present": {ref.name: ref.present() for ref in self.secret_refs},
            # Never include secret values.
            "quota": None,
            "quota_confidence": "unknown",
            "purpose_eligibility": "unknown",
        }

    async def describe_route(self, route_id: str) -> RouteSnapshot:
        if route_id not in self._routes:
            await self.discover()
        return self._routes[route_id]

    async def execute_one(
        self, request: InferenceRequest, admitted_ticket: Reservation
    ) -> AttemptReceipt:
        route = await self.describe_route(admitted_ticket.route_id)
        try:
            raw = self._invoke(route.model_id, request)
        except ProviderHttpError as exc:
            return AttemptReceipt(
                logical_call_id=admitted_ticket.logical_call_id,
                send_phase=ReservationPhase.SENT,
                finished_at=utc_now(),
                actual_route=route.route_id,
                error_class=exc.error_class,
                settlement_state=SettlementState.UNKNOWN,
                normalized_usage=NormalizedUsage(
                    requests=1,
                    extras={
                        "provider_cost_status": "unknown",
                        "rate_limit_headers": exc.rate_limit_headers,
                    },
                ),
                usage_raw_ref=None,
            )
        rate_limit_headers = raw.pop("_swarm_rate_limit_headers", {})
        usage = normalize_openai_usage(raw.get("usage"))
        raw_usage = raw.get("usage")
        raw_cost = raw_usage.get("cost") if isinstance(raw_usage, dict) else None
        routing: dict[str, Any] = {}
        if self.provider_id == "openrouter":
            metadata = raw.get("openrouter_metadata")
            if isinstance(metadata, dict):
                attempt = metadata.get("attempt")
                if isinstance(attempt, int) and not isinstance(attempt, bool) and attempt > 0:
                    routing["attempt"] = attempt
                if isinstance(metadata.get("is_byok"), bool):
                    routing["is_byok"] = metadata["is_byok"]
                endpoints = metadata.get("endpoints")
                available = endpoints.get("available") if isinstance(endpoints, dict) else None
                if isinstance(available, list):
                    selected = [
                        item
                        for item in available
                        if isinstance(item, dict) and item.get("selected") is True
                    ]
                    if len(selected) == 1:
                        for key, target in (
                            ("provider", "selected_provider"),
                            ("model", "selected_model"),
                        ):
                            value = selected[0].get(key)
                            if isinstance(value, str) and len(value) <= 128 and value.isprintable():
                                routing[target] = value
            if isinstance(raw_usage, dict) and isinstance(raw_usage.get("is_byok"), bool):
                routing["usage_is_byok"] = raw_usage["is_byok"]
            if not routing:
                routing["status"] = "unknown"
        cost_evidence: dict[str, Any] = {"provider_cost_status": "unknown"}
        if raw_cost is not None and not isinstance(raw_cost, bool):
            try:
                value = Decimal(str(raw_cost))
                if value.is_finite() and value >= 0:
                    cost_evidence = {
                        "provider_cost_status": "reported",
                        "provider_cost_usd": format(value, "f"),
                        "provider_cost_source": "response.usage.cost",
                    }
            except (InvalidOperation, ValueError):
                pass
        model_served = raw.get("model") or route.model_id
        # Persist observed upstream identity on the route snapshot.
        route.resolved_model_revision = str(model_served)
        route.observed_capabilities = list(set(route.observed_capabilities + ["chat"]))
        return AttemptReceipt(
            logical_call_id=admitted_ticket.logical_call_id,
            send_phase=ReservationPhase.SETTLED,
            finished_at=utc_now(),
            actual_route=route.route_id,
            provider_request_id=raw.get("id"),
            normalized_usage=NormalizedUsage(
                input_tokens=usage.get("input_tokens"),
                output_tokens=usage.get("output_tokens"),
                total_tokens=usage.get("total_tokens"),
                extras={
                    "upstream_model": model_served,
                    "usage_confidence": usage.get("confidence"),
                    "rate_limit_headers": rate_limit_headers,
                    "upstream_provider": routing.get("selected_provider")
                    if self.provider_id == "openrouter"
                    else raw.get("provider"),
                    **({"openrouter_routing": routing} if self.provider_id == "openrouter" else {}),
                    **cost_evidence,
                },
            ),
            settlement_state=SettlementState.SETTLED,
        )

    def _invoke(self, model_id: str, request: InferenceRequest) -> dict[str, Any]:
        if self.api_style == "gemini":
            return self._invoke_gemini(model_id, request)
        if self.api_style == "cloudflare":
            return self._invoke_cloudflare(model_id, request)
        if self.api_style == "cohere":
            return self._invoke_cohere(model_id, request)
        body: dict[str, Any] = {
            "model": model_id,
            "messages": request.messages,
            "stream": False,
        }
        if request.max_output_tokens is not None:
            token_field = "max_completion_tokens" if self.provider_id == "groq" else "max_tokens"
            body[token_field] = request.max_output_tokens
        response = self.transport.request_with_metadata("POST", "/chat/completions", json_body=body)
        return {**response.body, "_swarm_rate_limit_headers": response.rate_limit_headers}

    def _invoke_gemini(self, model_id: str, request: InferenceRequest) -> dict[str, Any]:
        contents = []
        for message in request.messages:
            contents.append(
                {
                    "role": "user" if message.get("role") == "user" else "model",
                    "parts": [{"text": message.get("content", "")}],
                }
            )
        path = f"/models/{model_id}:generateContent"
        body: dict[str, Any] = {"contents": contents}
        if request.max_output_tokens is not None:
            body["generationConfig"] = {"maxOutputTokens": request.max_output_tokens}
        raw = self.transport.request("POST", path, json_body=body)
        # Normalize to openai-like shape for shared usage handling.
        usage_meta = raw.get("usageMetadata") or {}
        text = ""
        for cand in raw.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                text += part.get("text", "")
        return {
            "id": raw.get("responseId"),
            "model": model_id,
            "choices": [{"message": {"role": "assistant", "content": text}}],
            "usage": {
                "prompt_tokens": usage_meta.get("promptTokenCount"),
                "completion_tokens": usage_meta.get("candidatesTokenCount"),
                "total_tokens": usage_meta.get("totalTokenCount"),
            },
        }

    def _invoke_cloudflare(self, model_id: str, request: InferenceRequest) -> dict[str, Any]:
        # Workers AI OpenAI-compatible path under /ai/v1/chat/completions when configured.
        body: dict[str, Any] = {"model": model_id, "messages": request.messages, "stream": False}
        if request.max_output_tokens is not None:
            body["max_tokens"] = request.max_output_tokens
        return self.transport.request("POST", "/chat/completions", json_body=body)

    def _invoke_cohere(self, model_id: str, request: InferenceRequest) -> dict[str, Any]:
        body: dict[str, Any] = {"model": model_id, "messages": request.messages, "stream": False}
        if request.max_output_tokens is not None:
            body["max_tokens"] = request.max_output_tokens
        raw = self.transport.request("POST", "/chat", json_body=body)
        usage = raw.get("usage") or {}
        tokens = usage.get("tokens") or {}
        text = raw.get("message", {}).get("content", [{}])
        content = ""
        if isinstance(text, list) and text:
            content = text[0].get("text", "")
        return {
            "id": raw.get("id"),
            "model": model_id,
            "choices": [{"message": {"role": "assistant", "content": content}}],
            "usage": {
                "prompt_tokens": tokens.get("input_tokens"),
                "completion_tokens": tokens.get("output_tokens"),
                "total_tokens": (
                    None
                    if tokens.get("input_tokens") is None
                    else (tokens.get("input_tokens") or 0) + (tokens.get("output_tokens") or 0)
                ),
            },
        }

    async def normalize_usage(self, raw: dict[str, Any]) -> dict[str, Any]:
        return normalize_openai_usage(raw)

    async def classify_error(self, exc: Exception) -> str:
        if isinstance(exc, ProviderHttpError):
            return exc.error_class.value
        return ErrorClass.UNKNOWN_OUTCOME.value
