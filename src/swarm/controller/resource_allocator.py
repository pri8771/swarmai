"""V3.0 resource allocator — feeds V2.3 scheduler, no parallel authority."""

from __future__ import annotations

from dataclasses import dataclass

from swarm.controller.fairness import DurableFairnessStore
from swarm.controller.reservations import ReservationComponent, ReservationService
from swarm.controller.scheduling_receipts import SchedulingReceiptLog


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
    ) -> None:
        self.fairness = fairness
        self.reservations = reservations
        self.receipts = receipts
        self.site_epoch = site_epoch

    def allocate(self, req: AllocationRequest) -> dict[str, object]:
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
