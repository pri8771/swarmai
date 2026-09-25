"""Qualify optional runtimes and emit an honest availability report."""

from __future__ import annotations

from typing import Any

from swarm.runtime.adapters.base import (
    PUBLIC_HOSTNAME,
    AgentRuntimeAdapter,
    RuntimeAvailability,
    RuntimeQualification,
)
from swarm.runtime.adapters.hermes import HermesRuntimeAdapter
from swarm.runtime.adapters.native import NativeRuntimeAdapter
from swarm.runtime.adapters.opencode import OpenCodeRuntimeAdapter


def default_adapters() -> list[AgentRuntimeAdapter]:
    return [
        NativeRuntimeAdapter(),
        OpenCodeRuntimeAdapter(),
        HermesRuntimeAdapter(),
    ]


def qualify_runtimes(
    adapters: list[AgentRuntimeAdapter] | None = None,
) -> list[RuntimeQualification]:
    chosen = adapters if adapters is not None else default_adapters()
    return [adapter.qualify() for adapter in chosen]


def qualification_report(
    adapters: list[AgentRuntimeAdapter] | None = None,
) -> dict[str, Any]:
    rows = qualify_runtimes(adapters)
    available = [r.runtime_id for r in rows if r.availability == RuntimeAvailability.AVAILABLE]
    discovered = [
        r.runtime_id
        for r in rows
        if r.availability == RuntimeAvailability.DISCOVERED_UNQUALIFIED
    ]
    unavailable = [
        r.runtime_id for r in rows if r.availability == RuntimeAvailability.UNAVAILABLE
    ]
    # Admission rule: only AVAILABLE runtimes may be offered for mission work.
    mission_admissible = list(available)
    return {
        "schema_version": "1.0",
        "packet": "TH-06",
        "hostname_public": PUBLIC_HOSTNAME,
        "config_alone_enforces_swarm_contracts": False,
        "policy": {
            "mission_admissible_runtimes": mission_admissible,
            "note": (
                "Framework configuration alone never admits a runtime. "
                "Only availability=available with SwarmAI kernel mediation may run missions."
            ),
        },
        "summary": {
            "available": available,
            "discovered_unqualified": discovered,
            "unavailable": unavailable,
        },
        "runtimes": [r.to_dict() for r in rows],
        "mock_vs_live": "qualification_probe_not_live_inference",
    }
