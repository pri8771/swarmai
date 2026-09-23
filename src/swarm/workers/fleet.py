"""V2.3/V3.0 fleet placement — extends worker registry, no second registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.workers.registry import WorkerRegistryService


class FleetError(PermissionError):
    pass


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
        self._worker_tenant: dict[str, str] = {}
        self._worker_locality: dict[str, str] = {}
        self._worker_trust: dict[str, str] = {}
        self._audit: list[FleetAuditEvent] = []
        self._decisions: list[FleetPlacementDecision] = []

    def bind_project_tenant(self, project_id: str, tenant_id: str) -> None:
        self._tenant_of_project[project_id] = tenant_id

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
        self._worker_trust[worker_id] = trust_class

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
        trust_rank = {"compute_only": 0, "code_write": 1, "browser_session": 2, "operator_local": 3}
        min_rank = trust_rank.get(min_trust, 0)
        candidates: list[tuple[str, str, str]] = []
        for worker_id, rec in self.registry._workers.items():  # noqa: SLF001 — shared registry
            w_tenant = self._worker_tenant.get(worker_id)
            if w_tenant is None:
                continue
            if w_tenant != tenant:
                self._audit.append(
                    FleetAuditEvent(
                        event_id=new_id("faud_"),
                        tenant_id=tenant,
                        project_id=project_id,
                        action="cross_tenant_reject",
                        detail={"worker_id": worker_id, "worker_tenant": w_tenant},
                    )
                )
                continue
            if rec.project_id and rec.project_id != project_id:
                # Same tenant but wrong project binding — still reject for isolation.
                self._audit.append(
                    FleetAuditEvent(
                        event_id=new_id("faud_"),
                        tenant_id=tenant,
                        project_id=project_id,
                        action="cross_project_reject",
                        detail={"worker_id": worker_id, "worker_project": rec.project_id},
                    )
                )
                continue
            locality = self._worker_locality.get(worker_id, "local")
            trust = self._worker_trust.get(worker_id, "compute_only")
            if trust_rank.get(trust, 0) < min_rank:
                continue
            if preferred_locality and locality != preferred_locality:
                continue
            candidates.append((worker_id, locality, trust))
        if not candidates:
            raise FleetError("no_eligible_worker")
        worker_id, locality, trust = candidates[0]
        decision = FleetPlacementDecision(
            decision_id=new_id("fpl_"),
            project_id=project_id,
            tenant_id=tenant,
            worker_id=worker_id,
            locality=locality,
            trust_class=trust,
            reason="tenant_locality_trust",
        )
        self._decisions.append(decision)
        self._audit.append(
            FleetAuditEvent(
                event_id=new_id("faud_"),
                tenant_id=tenant,
                project_id=project_id,
                action="place",
                detail=decision.to_dict(),
            )
        )
        return decision

    def assert_same_tenant(self, *, actor_tenant: str, resource_tenant: str, action: str) -> None:
        if actor_tenant != resource_tenant:
            self._audit.append(
                FleetAuditEvent(
                    event_id=new_id("faud_"),
                    tenant_id=actor_tenant,
                    project_id="",
                    action="cross_tenant_denied",
                    detail={"resource_tenant": resource_tenant, "denied_action": action},
                )
            )
            raise FleetError(f"cross_tenant_denied:{action}")

    def audit_log(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._audit]
