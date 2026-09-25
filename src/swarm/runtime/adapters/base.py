"""Optional agent runtime adapters — qualification, not kernel ownership.

SwarmAI retains mission ownership, permissions, budgets, verification, and
succession. Framework configuration alone does **not** enforce SwarmAI
contracts. An adapter is only mission-available after capability-by-capability
qualification evidence; otherwise capabilities must be marked unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from swarm.contracts.common import utc_now

PUBLIC_HOSTNAME = "swarm.splitsignal.ai"

# Capabilities required by the two-host architecture update §6.
REQUIRED_CAPABILITIES: tuple[str, ...] = (
    "dispatch_events",
    "cancel_termination",
    "permission_tool_observability",
    "model_routing_usage",
    "context_occupancy_xy_succession",
    "knowledge_transfer_artifacts",
    "restart_recovery_cleanup",
    "nested_delegation_accounting",
)


class RuntimeAvailability(StrEnum):
    """Coarse adapter availability for mission admission."""

    AVAILABLE = "available"
    DISCOVERED_UNQUALIFIED = "discovered_unqualified"
    UNAVAILABLE = "unavailable"


class CapabilityStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNPROVEN = "unproven"


@dataclass(frozen=True)
class CapabilityQualification:
    capability: str
    status: CapabilityStatus
    reason: str
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "status": self.status.value,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass
class RuntimeQualification:
    runtime_id: str
    display_name: str
    availability: RuntimeAvailability
    pinned_version: str | None
    discovered_version: str | None
    install_path: str | None
    summary: str
    capabilities: list[CapabilityQualification] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    # Explicit honesty flags — never invent enforcement from vendor config.
    config_alone_enforces_swarm_contracts: bool = False
    kernel_mediation_proven: bool = False
    live_inference_authorized: bool = False
    hostname_public: str = PUBLIC_HOSTNAME
    qualified_at: str = field(default_factory=lambda: utc_now().isoformat())
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "display_name": self.display_name,
            "availability": self.availability.value,
            "pinned_version": self.pinned_version,
            "discovered_version": self.discovered_version,
            "install_path": self.install_path,
            "summary": self.summary,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "blockers": list(self.blockers),
            "config_alone_enforces_swarm_contracts": (
                self.config_alone_enforces_swarm_contracts
            ),
            "kernel_mediation_proven": self.kernel_mediation_proven,
            "live_inference_authorized": self.live_inference_authorized,
            "hostname_public": self.hostname_public,
            "qualified_at": self.qualified_at,
            "notes": list(self.notes),
        }


class AgentRuntimeAdapter(Protocol):
    """Bounded SwarmAI-facing runtime adapter contract."""

    runtime_id: str

    def qualify(self) -> RuntimeQualification:
        """Probe and return honest qualification — never self-certify live use."""
        ...


def all_capabilities(
    status: CapabilityStatus,
    reason: str,
    *,
    evidence_refs: tuple[str, ...] = (),
) -> list[CapabilityQualification]:
    return [
        CapabilityQualification(
            capability=cap,
            status=status,
            reason=reason,
            evidence_refs=evidence_refs,
        )
        for cap in REQUIRED_CAPABILITIES
    ]


def merge_capability_map(
    overrides: dict[str, CapabilityQualification],
    *,
    default_status: CapabilityStatus,
    default_reason: str,
) -> list[CapabilityQualification]:
    rows: list[CapabilityQualification] = []
    for cap in REQUIRED_CAPABILITIES:
        if cap in overrides:
            rows.append(overrides[cap])
        else:
            rows.append(
                CapabilityQualification(
                    capability=cap,
                    status=default_status,
                    reason=default_reason,
                )
            )
    return rows
