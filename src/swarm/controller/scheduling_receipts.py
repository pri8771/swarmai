"""V2.3 scheduler decision receipts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.common import new_id, payload_hash, utc_now


@dataclass
class SchedulerDecisionReceipt:
    receipt_id: str
    site_epoch: int
    project_id: str
    mission_id: str
    task_id: str | None
    decision: str  # dispatch|defer|reject|drain
    reason: str
    fairness_debt: float = 0.0
    reservation_intent_id: str | None = None
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        body = {
            "receipt_id": self.receipt_id,
            "site_epoch": self.site_epoch,
            "project_id": self.project_id,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "decision": self.decision,
            "reason": self.reason,
            "fairness_debt": self.fairness_debt,
            "reservation_intent_id": self.reservation_intent_id,
            "created_at": self.created_at,
            "extras": dict(self.extras),
        }
        body["digest"] = payload_hash(body)
        return body


class SchedulingReceiptLog:
    def __init__(self) -> None:
        self._items: list[SchedulerDecisionReceipt] = []

    def record(
        self,
        *,
        site_epoch: int,
        project_id: str,
        mission_id: str,
        decision: str,
        reason: str,
        task_id: str | None = None,
        fairness_debt: float = 0.0,
        reservation_intent_id: str | None = None,
        **extras: Any,
    ) -> SchedulerDecisionReceipt:
        receipt = SchedulerDecisionReceipt(
            receipt_id=new_id("sdr_"),
            site_epoch=site_epoch,
            project_id=project_id,
            mission_id=mission_id,
            task_id=task_id,
            decision=decision,
            reason=reason,
            fairness_debt=fairness_debt,
            reservation_intent_id=reservation_intent_id,
            extras=dict(extras),
        )
        self._items.append(receipt)
        return receipt

    def all(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._items]
