"""One broker-facing adapter for multiple exact provider routes."""

from __future__ import annotations

from typing import Any

from swarm.contracts.enums import ErrorClass
from swarm.contracts.provider import AttemptReceipt, InferenceRequest, Reservation, RouteSnapshot
from swarm.providers.transport.openai_compatible import ProviderHttpError


class MultiplexProviderAdapter:
    """Dispatch each admitted ticket to the adapter that discovered its route."""

    def __init__(self, adapters: list[Any]) -> None:
        ids = [getattr(adapter, "provider_id", None) for adapter in adapters]
        if (
            not adapters
            or any(not isinstance(pid, str) for pid in ids)
            or len(set(ids)) != len(ids)
        ):
            raise ValueError("provider adapters require distinct provider IDs")
        self.adapters = adapters
        self._by_route: dict[str, Any] = {}

    async def discover(self) -> list[RouteSnapshot]:
        routes: list[RouteSnapshot] = []
        mapping: dict[str, Any] = {}
        for adapter in self.adapters:
            for route in await adapter.discover():
                if route.provider != adapter.provider_id or route.route_id in mapping:
                    raise ValueError("provider route identity is ambiguous")
                mapping[route.route_id] = adapter
                routes.append(route)
        self._by_route = mapping
        return routes

    def for_route(self, route_id: str) -> Any:
        return self._by_route[route_id]

    async def execute_one(
        self, request: InferenceRequest, admitted_ticket: Reservation
    ) -> AttemptReceipt:
        if request.route_id != admitted_ticket.route_id:
            raise ValueError("multiplex request route differs from admitted ticket")
        receipt: AttemptReceipt = await self.for_route(admitted_ticket.route_id).execute_one(
            request, admitted_ticket
        )
        return receipt

    async def classify_error(self, exc: Exception) -> ErrorClass:
        if isinstance(exc, ProviderHttpError):
            return exc.error_class
        return ErrorClass.UNKNOWN_OUTCOME
