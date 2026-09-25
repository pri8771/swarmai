"""Native SwarmAI runtime — Mac loopback path already exercised by TH-02/TH-04."""

from __future__ import annotations

from swarm.runtime.adapters.base import (
    AgentRuntimeAdapter,
    CapabilityQualification,
    CapabilityStatus,
    RuntimeAvailability,
    RuntimeQualification,
    merge_capability_map,
)


class NativeRuntimeAdapter:
    """In-process native worker/runtime under SwarmAI kernel ownership."""

    runtime_id = "native"

    def qualify(self) -> RuntimeQualification:
        # Only mark capabilities available when Mac eng evidence already exists.
        # Remaining controls stay unproven rather than silently claimed.
        overrides = {
            "dispatch_events": CapabilityQualification(
                capability="dispatch_events",
                status=CapabilityStatus.AVAILABLE,
                reason="TH-02 native worker enroll/claim/submit/accept on loopback API",
                evidence_refs=("docs/evidence/two-host/TH-02/",),
            ),
            "knowledge_transfer_artifacts": CapabilityQualification(
                capability="knowledge_transfer_artifacts",
                status=CapabilityStatus.AVAILABLE,
                reason="TH-04 durable CAS publish/reopen with identical sha256 after restart",
                evidence_refs=("docs/evidence/two-host/TH-04/",),
            ),
            "restart_recovery_cleanup": CapabilityQualification(
                capability="restart_recovery_cleanup",
                status=CapabilityStatus.AVAILABLE,
                reason="TH-02 mission hydrate + TH-04 artifact reopen after API restart",
                evidence_refs=(
                    "docs/evidence/two-host/TH-02/",
                    "docs/evidence/two-host/TH-04/",
                ),
            ),
            "permission_tool_observability": CapabilityQualification(
                capability="permission_tool_observability",
                status=CapabilityStatus.UNPROVEN,
                reason="Gateway exists; full native permission matrix not re-proven in TH-06",
            ),
            "cancel_termination": CapabilityQualification(
                capability="cancel_termination",
                status=CapabilityStatus.UNPROVEN,
                reason="Cancel routes exist; dedicated cancel-during-tool proof not in TH-06 scope",
            ),
            "model_routing_usage": CapabilityQualification(
                capability="model_routing_usage",
                status=CapabilityStatus.UNPROVEN,
                reason="Free-only default; live route qualification not authorized this packet",
            ),
            "context_occupancy_xy_succession": CapabilityQualification(
                capability="context_occupancy_xy_succession",
                status=CapabilityStatus.UNPROVEN,
                reason="X/Y succession not exercised in two-host TH packets yet",
            ),
            "nested_delegation_accounting": CapabilityQualification(
                capability="nested_delegation_accounting",
                status=CapabilityStatus.UNPROVEN,
                reason="Nested delegation accounting not proven on Mac loopback TH path",
            ),
        }
        return RuntimeQualification(
            runtime_id=self.runtime_id,
            display_name="Native SwarmAI runtime",
            availability=RuntimeAvailability.AVAILABLE,
            pinned_version="swarm-native",
            discovered_version="swarm-native",
            install_path="src/swarm",
            summary=(
                "Native runtime remains the default mission path. TH-02/TH-04 prove "
                "dispatch and durable artifacts on Mac loopback; other controls stay "
                "unproven rather than silently claimed."
            ),
            capabilities=merge_capability_map(
                overrides,
                default_status=CapabilityStatus.UNPROVEN,
                default_reason="not assessed in TH-06",
            ),
            blockers=[],
            config_alone_enforces_swarm_contracts=False,
            kernel_mediation_proven=False,
            live_inference_authorized=False,
            notes=[
                "Native availability is partial: only narrowly proven capabilities may dispatch.",
                (
                    "kernel_mediation_proven remains false until "
                    "cancel/permissions/succession evidence exists."
                ),
                "CAS persistence is not knowledge-transfer qualification.",
                "SwarmAI kernel owns admission; native code is not a third-party framework.",
            ],
        )


_: type[AgentRuntimeAdapter] = NativeRuntimeAdapter
