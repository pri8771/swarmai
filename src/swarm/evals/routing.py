"""Routing query helpers over capability profiles."""

from __future__ import annotations

from typing import Any

from swarm.contracts.enums import RoutingState
from swarm.evals.profiles import ProfileStore


def select_routes(
    store: ProfileStore,
    *,
    task_family: str,
    require_qualified: bool = False,
) -> list[dict[str, Any]]:
    min_state = RoutingState.QUALIFIED if require_qualified else RoutingState.PROVISIONAL
    profiles = store.query(task_family=task_family, min_state=min_state)
    # Prefer higher lower_bound, then more distinct samples.
    profiles = sorted(
        profiles,
        key=lambda p: (p.lower_bound or 0.0, p.distinct_case_count),
        reverse=True,
    )
    return [
        {
            "profile_key": p.profile_key,
            "route_fingerprint": p.route_fingerprint,
            "routing_state": p.routing_state.value,
            "distinct_case_count": p.distinct_case_count,
            "pass_count": p.pass_count,
            "lower_bound": p.lower_bound,
            "simulated": False,
        }
        for p in profiles
    ]
