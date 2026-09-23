"""Explicit OpenRouter free-route allowlist (route-level zero-charge only).

Provider-level ``paid=false`` never implies free eligibility. Only exact model
IDs on this allowlist may be treated as known-zero under spend=zero, and only
when invoked with a pinned backend + ``max_price`` ceilings of 0.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Exact free models verified via anonymous OpenRouter public metadata
# (prompt+completion price 0) with a single zero-price backend slug.
# Recheck before live use; membership here is not account entitlement.
_OPENROUTER_FREE_MODEL_RE = re.compile(
    r"^[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*:free$"
)
_BACKEND_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


@dataclass(frozen=True)
class OpenRouterFreeRoute:
    """One exact free model and hosting backend, selected before admission."""

    model_id: str
    provider_slug: str

    def __post_init__(self) -> None:
        if not _OPENROUTER_FREE_MODEL_RE.fullmatch(self.model_id):
            raise ValueError("OpenRouter route requires an exact :free model slug")
        if not _BACKEND_SLUG_RE.fullmatch(self.provider_slug):
            raise ValueError("OpenRouter route requires one exact backend slug")

    @property
    def route_id(self) -> str:
        return f"rt_openrouter_{self.model_id}"


# Allowlist: route_id / model_id → pinned free route.
# Source: public GET /api/v1/models + endpoints (2026-09-22 candidate; rechecked).
OPENROUTER_FREE_ROUTE_ALLOWLIST: dict[str, OpenRouterFreeRoute] = {
    "qwen/qwen3.8-27b:free": OpenRouterFreeRoute(
        model_id="qwen/qwen3.8-27b:free",
        provider_slug="modelrun",
    ),
}

# Route-id aliases that resolve to an allowlisted free model (never paid defaults).
OPENROUTER_FREE_ROUTE_IDS: frozenset[str] = frozenset(
    {spec.route_id for spec in OPENROUTER_FREE_ROUTE_ALLOWLIST.values()}
)


def is_openrouter_free_model_id(model_id: str) -> bool:
    """True only when model_id is on the explicit free allowlist (not merely :free)."""
    return model_id in OPENROUTER_FREE_ROUTE_ALLOWLIST


def resolve_openrouter_free_route(route_id: str) -> OpenRouterFreeRoute | None:
    """Resolve an allowlisted free route from a canary/broker route id.

    Fail-closed: unknown routes, non-openrouter prefixes, and non-allowlisted
    ``:free`` model ids all return None.
    """
    if not route_id.startswith("rt_openrouter_"):
        return None
    model_id = route_id[len("rt_openrouter_") :]
    if not model_id or model_id == "default":
        return None
    return OPENROUTER_FREE_ROUTE_ALLOWLIST.get(model_id)


def openrouter_free_route_ids() -> list[str]:
    """Sorted allowlisted route ids for docs/tests."""
    return sorted(OPENROUTER_FREE_ROUTE_IDS)
