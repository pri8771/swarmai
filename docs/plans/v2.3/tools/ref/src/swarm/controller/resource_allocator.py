"""V3.0 resource allocator — feeds V2.3 scheduler, no parallel authority.

With ``scheduler`` set, every allocation is one ``SchedulerService.schedule_once``
decision (durable credit, intents, epochs and receipts). Without it, the legacy
fixture path below is used unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from swarm.controller.fairness import DurableFairnessStore
from swarm.controller.reservations import ReservationComponent, ReservationService
from swarm.controller.scheduling_receipts import SchedulingReceiptLog

if TYPE_CHECKING:
    from swarm.scheduling.service import SchedulerService


class AllocationDenied(PermissionError):
    pass


@dataclass
class AllocationRequest:
    project_id: str
    mission_id: str
    attempt_id: str
    worker_class: str = "local"
    provider_route: str = "rt_ollama_default"
    tool_units: float = 0.0


class ResourceAllocator:
    def __init__(
        self,
        *,
        fairness: DurableFairnessStore,
        reservations: ReservationService,
        receipts: SchedulingReceiptLog,
        site_epoch: int,
        scheduler: SchedulerService | None = None,
    ) -> None:
        self.fairness = fairness
        self.reservations = reservations
        self.receipts = receipts
        self.site_epoch = site_epoch
        self.scheduler = scheduler

    def _allocate_v23(self, req: AllocationRequest) -> dict[str, object]:
        from swarm.contracts.v23 import SchedulableTask, SchedulerDecision

        assert self.scheduler is not None
        self.scheduler.register_project(req.project_id)
        self.scheduler.register_mission(req.mission_id, req.project_id)
        task = SchedulableTask(
            task_id=req.attempt_id,
            mission_id=req.mission_id,
            project_id=req.project_id,
            attempt_id=req.attempt_id,
            worker_class=req.worker_class,
            provider_route=req.provider_route,
            tool_units=req.tool_units,
        )
        out = self.scheduler.schedule_once([task])
        if out.decision != SchedulerDecision.ADMIT or out.intent is None or out.receipt is None:
            raise AllocationDenied(f"allocation_{out.decision.value}:{out.reason_code.value}")
        return {
            "intent": out.intent.model_dump(mode="json"),
            "receipt": out.receipt.model_dump(mode="json"),
        }

    def allocate(self, req: AllocationRequest) -> dict[str, object]:
        if self.scheduler is not None:
            return self._allocate_v23(req)
        ranked = self.fairness.rank_projects([req.project_id])
        if not ranked or ranked[0] != req.project_id and len(ranked) > 1:
            # Still allow single-project; multi-project fairness recorded.
            pass
        components = [
            ReservationComponent(kind="worker", resource_id=req.worker_class, units=1.0),
            ReservationComponent(kind="provider", resource_id=req.provider_route, units=1.0),
        ]
        if req.tool_units:
            components.append(
                ReservationComponent(kind="tool", resource_id="gateway", units=req.tool_units)
            )
        intent = self.reservations.reserve(
            project_id=req.project_id,
            mission_id=req.mission_id,
            attempt_id=req.attempt_id,
            site_epoch=self.site_epoch,
            components=components,
        )
        st = self.fairness.note_dispatch(req.project_id)
        receipt = self.receipts.record(
            site_epoch=self.site_epoch,
            project_id=req.project_id,
            mission_id=req.mission_id,
            decision="dispatch",
            reason="allocator_v30",
            fairness_debt=st.fairness_debt,
            reservation_intent_id=intent.intent_id,
        )
        return {"intent": intent.to_dict(), "receipt": receipt.to_dict()}
