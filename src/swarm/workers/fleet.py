"""V2.3 fleet placement (ART-V23-FLEET-POLICY) — extends worker registry, no second registry.

Trust classes use the ART names (``observe_only`` < ``sandbox_compute`` <
``model_worker`` < ``tool_worker`` < ``integration_worker``). Legacy names are
accepted as aliases. Placement is deterministic and least-privilege: among
eligible workers pick the lowest sufficient trust class, then ``worker_id``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import WorkerStatus
from swarm.contracts.v23 import TRUST_RANK, TrustClass, WorkerDrainState
from swarm.workers.registry import WorkerRegistryService

LEGACY_TRUST_ALIASES: dict[str, TrustClass] = {
    "compute_only": TrustClass.SANDBOX_COMPUTE,
    "code_write": TrustClass.TOOL_WORKER,
    "browser_session": TrustClass.INTEGRATION_WORKER,
    "operator_local": TrustClass.INTEGRATION_WORKER,
}

_DRAIN_TRANSITIONS: dict[WorkerDrainState, set[WorkerDrainState]] = {
    WorkerDrainState.ACTIVE: {WorkerDrainState.DRAINING, WorkerDrainState.REVOKED},
    WorkerDrainState.DRAINING: {
        WorkerDrainState.DRAINED,
        WorkerDrainState.ACTIVE,
        WorkerDrainState.REVOKED,
    },
    WorkerDrainState.DRAINED: {WorkerDrainState.ACTIVE, WorkerDrainState.REVOKED},
    WorkerDrainState.REVOKED: set(),
}


class FleetError(PermissionError):
    pass


def normalize_trust(value: str | TrustClass) -> TrustClass:
    if isinstance(value, TrustClass):
        return value
    if value in LEGACY_TRUST_ALIASES:
        return LEGACY_TRUST_ALIASES[value]
    try:
        return TrustClass(value)
    except ValueError as exc:
        raise FleetError(f"unknown_trust_class:{value}") from exc


@dataclass
class FleetPlacementDecision:
    decision_id: str
    project_id: str
    tenant_id: str
    worker_id: str
    locality: str
    trust_class: str
    reason: str
    at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "worker_id": self.worker_id,
            "locality": self.locality,
            "trust_class": self.trust_class,
            "reason": self.reason,
            "at": self.at,
        }


@dataclass
class FleetAuditEvent:
    event_id: str
    tenant_id: str
    project_id: str
    action: str
    detail: dict[str, Any]
    at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "action": self.action,
            "detail": dict(self.detail),
            "at": self.at,
        }


class FleetPlacementService:
    """Tenant-aware placement using the existing in-memory WorkerRegistryService."""

    def __init__(self, registry: WorkerRegistryService) -> None:
        self.registry = registry
        self._tenant_of_project: dict[str, str] = {}
        self._project_ceiling: dict[str, TrustClass] = {}
        self._worker_tenant: dict[str, str] = {}
        self._worker_locality: dict[str, str] = {}
        self._worker_trust: dict[str, TrustClass] = {}
        self._worker_drain: dict[str, WorkerDrainState] = {}
        self._audit: list[FleetAuditEvent] = []
        self._decisions: list[FleetPlacementDecision] = []

    def _log(self, tenant: str, project: str, action: str, detail: dict[str, Any]) -> None:
        self._audit.append(
            FleetAuditEvent(
                event_id=new_id("faud_"),
                tenant_id=tenant,
                project_id=project,
                action=action,
                detail=detail,
            )
        )

    def bind_project_tenant(self, project_id: str, tenant_id: str) -> None:
        self._tenant_of_project[project_id] = tenant_id

    def set_project_trust_ceiling(self, project_id: str, ceiling: str | TrustClass) -> None:
        self._project_ceiling[project_id] = normalize_trust(ceiling)

    def annotate_worker(
        self,
        worker_id: str,
        *,
        tenant_id: str,
        locality: str = "local",
        trust_class: str = "compute_only",
    ) -> None:
        self._worker_tenant[worker_id] = tenant_id
        self._worker_locality[worker_id] = locality
        self._worker_trust[worker_id] = normalize_trust(trust_class)
        self._worker_drain.setdefault(worker_id, WorkerDrainState.ACTIVE)

    def sync_project_workers(self, project_id: str, tenant_id: str) -> None:
        """Bind trusted registry facts into placement without worker self-assertion.

        The product API already authorizes worker enrollment to a project. This
        adapter uses that server-owned project binding and the normalized
        locality on the registered lease. Trust defaults to sandbox compute;
        higher trust still requires an explicit control-plane annotation.
        """
        self.bind_project_tenant(project_id, tenant_id)
        for worker_id, rec in self.registry._workers.items():  # noqa: SLF001
            if rec.project_id != project_id or worker_id in self._worker_tenant:
                continue
            locality = "local"
            if isinstance(rec.lease.data_locality, dict):
                locality = str(rec.lease.data_locality.get("primary") or locality)
            self.annotate_worker(
                worker_id,
                tenant_id=tenant_id,
                locality=locality,
                trust_class=TrustClass.SANDBOX_COMPUTE.value,
            )

    def drain_state(self, worker_id: str) -> WorkerDrainState:
        return self._worker_drain.get(worker_id, WorkerDrainState.ACTIVE)

    def set_drain_state(self, worker_id: str, state: WorkerDrainState) -> WorkerDrainState:
        current = self.drain_state(worker_id)
        if state == current:
            return current
        if state not in _DRAIN_TRANSITIONS[current]:
            raise FleetError(f"drain_transition_illegal:{current.value}->{state.value}")
        self._worker_drain[worker_id] = state
        tenant = self._worker_tenant.get(worker_id, "")
        self._log(tenant, "", "drain_state", {"worker_id": worker_id, "state": state.value})
        return state

    def _registry_blocks(self, worker_id: str) -> str | None:
        rec = self.registry._workers.get(worker_id)  # noqa: SLF001 — shared registry
        if rec is None:
            return "worker_not_registered"
        if rec.revoked:
            return "worker_revoked"
        if rec.lease.status in {
            WorkerStatus.DRAINING,
            WorkerStatus.QUARANTINED,
            WorkerStatus.OFFLINE,
        }:
            return f"worker_{rec.lease.status.value}"
        return None

    def place(
        self,
        *,
        project_id: str,
        preferred_locality: str | None = None,
        min_trust: str = "compute_only",
    ) -> FleetPlacementDecision:
        tenant = self._tenant_of_project.get(project_id)
        if tenant is None:
            raise FleetError("project_tenant_unbound")
        needed = normalize_trust(min_trust)
        ceiling = self._project_ceiling.get(project_id)
        if ceiling is not None and TRUST_RANK[needed] > TRUST_RANK[ceiling]:
            self._log(tenant, project_id, "trust_ceiling_reject", {"needed": needed.value})
            raise FleetError("trust_above_project_ceiling")
        candidates: list[tuple[int, str, str, TrustClass]] = []
        for worker_id in sorted(self.registry._workers):  # noqa: SLF001 — shared registry
            rec = self.registry._workers[worker_id]  # noqa: SLF001
            w_tenant = self._worker_tenant.get(worker_id)
            if w_tenant is None:
                continue
            if w_tenant != tenant:
                self._log(
                    tenant,
                    project_id,
                    "cross_tenant_reject",
                    {"worker_id": worker_id, "worker_tenant": w_tenant},
                )
                continue
            if rec.project_id and rec.project_id != project_id:
                self._log(
                    tenant,
                    project_id,
                    "cross_project_reject",
                    {"worker_id": worker_id, "worker_project": rec.project_id},
                )
                continue
            if self.drain_state(worker_id) != WorkerDrainState.ACTIVE:
                continue
            if self._registry_blocks(worker_id) is not None:
                continue
            locality = self._worker_locality.get(worker_id, "local")
            trust = self._worker_trust.get(worker_id, TrustClass.SANDBOX_COMPUTE)
            if TRUST_RANK[trust] < TRUST_RANK[needed]:
                continue
            if ceiling is not None and TRUST_RANK[trust] > TRUST_RANK[ceiling]:
                continue
            if preferred_locality and locality != preferred_locality:
                continue
            candidates.append((TRUST_RANK[trust], worker_id, locality, trust))
        if not candidates:
            raise FleetError("no_eligible_worker")
        _rank, worker_id, locality, trust = min(candidates)
        decision = FleetPlacementDecision(
            decision_id=new_id("fpl_"),
            project_id=project_id,
            tenant_id=tenant,
            worker_id=worker_id,
            locality=locality,
            trust_class=trust.value,
            reason="tenant_locality_least_privilege",
        )
        self._decisions.append(decision)
        self._log(tenant, project_id, "place", decision.to_dict())
        return decision

    def assert_same_tenant(self, *, actor_tenant: str, resource_tenant: str, action: str) -> None:
        if actor_tenant != resource_tenant:
            self._log(
                actor_tenant,
                "",
                "cross_tenant_denied",
                {"resource_tenant": resource_tenant, "denied_action": action},
            )
            raise FleetError(f"cross_tenant_denied:{action}")

    def audit_log(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._audit]
