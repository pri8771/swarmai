"""X/Y trainee succession with KT1/KT2 and generation fencing (PC-07).

Personality/message text cannot grant authority. Only atomic promote() transfers
ownership after trainee validates packet integrity. Predecessor generation is
retired and cannot issue effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.agent import AgentIncarnation, LogicalAgent
from swarm.contracts.common import utc_now
from swarm.contracts.succession import (
    KT1Packet,
    KT2Packet,
    OccupancyPolicy,
    OccupancySnapshot,
    SuccessionPhase,
    SuccessionRecord,
)


class SuccessionError(RuntimeError):
    """Illegal succession transition or fence violation."""


def _digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass
class LineageState:
    logical: LogicalAgent
    incarnations: dict[str, AgentIncarnation] = field(default_factory=dict)
    active_incarnation_id: str | None = None

    def active(self) -> AgentIncarnation:
        if self.active_incarnation_id is None:
            raise SuccessionError("no_active_incarnation")
        return self.incarnations[self.active_incarnation_id]


class SuccessionService:
    """In-process succession authority. Persist via dump/load; L1 may later back with PG."""

    def __init__(self, *, policy: OccupancyPolicy | None = None) -> None:
        self.policy = policy or OccupancyPolicy()
        self._lineages: dict[str, LineageState] = {}
        self._open: dict[str, SuccessionRecord] = {}  # logical_agent_id -> open succession
        self._history: list[SuccessionRecord] = []

    def register_logical(
        self,
        logical: LogicalAgent,
        *,
        mission_id: str | None = None,
    ) -> AgentIncarnation:
        if logical.logical_agent_id in self._lineages:
            raise SuccessionError("logical_already_registered")
        inc = AgentIncarnation(
            logical_agent_id=logical.logical_agent_id,
            generation=1,
            mission_id=mission_id,
            role="active",
        )
        self._lineages[logical.logical_agent_id] = LineageState(
            logical=logical,
            incarnations={inc.incarnation_id: inc},
            active_incarnation_id=inc.incarnation_id,
        )
        return inc

    def get_lineage(self, logical_agent_id: str) -> LineageState:
        if logical_agent_id not in self._lineages:
            raise SuccessionError("logical_unknown")
        return self._lineages[logical_agent_id]

    def open_succession(self, logical_agent_id: str) -> SuccessionRecord | None:
        return self._open.get(logical_agent_id)

    def observe_occupancy(
        self,
        *,
        mission_id: str,
        project_id: str,
        logical_agent_id: str,
        snapshot: OccupancySnapshot,
    ) -> SuccessionRecord | None:
        """Idempotent X/Y triggers. Returns open succession if created/advanced."""
        lineage = self.get_lineage(logical_agent_id)
        active = lineage.active()
        if active.role != "active":
            return self._open.get(logical_agent_id)

        existing = self._open.get(logical_agent_id)
        if existing is not None and existing.phase == "promoted":
            return existing

        x = self.policy.trainee_at
        y = self.policy.takeover_at
        occ = snapshot.occupancy

        if occ < x and existing is None:
            return None

        if existing is None:
            # Crossing X (or jumping past Y) creates trainee + KT1 path.
            return self._create_trainee(
                mission_id=mission_id,
                project_id=project_id,
                logical_agent_id=logical_agent_id,
                snapshot=snapshot,
                jump_to_final=(occ >= y),
            )

        if occ >= y and existing.phase in {
            "trainee_created",
            "kt1_pending",
            "shadowing",
        }:
            return self.begin_final_kt(existing.succession_id)
        return existing

    def _create_trainee(
        self,
        *,
        mission_id: str,
        project_id: str,
        logical_agent_id: str,
        snapshot: OccupancySnapshot,
        jump_to_final: bool,
    ) -> SuccessionRecord:
        if logical_agent_id in self._open:
            raise SuccessionError("open_succession_exists")
        lineage = self.get_lineage(logical_agent_id)
        pred = lineage.active()
        trainee_gen = pred.generation + 1
        trainee = AgentIncarnation(
            logical_agent_id=logical_agent_id,
            generation=trainee_gen,
            mission_id=mission_id,
            role="trainee",
        )
        lineage.incarnations[trainee.incarnation_id] = trainee
        rec = SuccessionRecord(
            mission_id=mission_id,
            project_id=project_id,
            logical_agent_id=logical_agent_id,
            predecessor_incarnation_id=pred.incarnation_id,
            predecessor_generation=pred.generation,
            trainee_incarnation_id=trainee.incarnation_id,
            trainee_generation=trainee_gen,
            phase="trainee_created",
            policy=self.policy,
            trigger_occupancy=snapshot,
        )
        self._open[logical_agent_id] = rec
        if jump_to_final:
            rec.phase = "final_kt"
            rec.blocked_reason = None
        return rec

    def issue_kt1(
        self,
        succession_id: str,
        *,
        objective: str,
        decisions: list[str],
        evidence_refs: list[str],
        grants_summary: list[str],
        open_commitments: list[str],
        current_task: str,
        memory_refs: list[str],
        event_watermark: str,
        inbox_cursor: int,
    ) -> KT1Packet:
        rec = self._by_id(succession_id)
        if rec.phase not in {"trainee_created", "kt1_pending", "final_kt"}:
            raise SuccessionError(f"kt1_illegal_from:{rec.phase}")
        material = {
            "objective": objective,
            "decisions": decisions,
            "evidence_refs": evidence_refs,
            "grants": grants_summary,
            "commitments": open_commitments,
            "task": current_task,
            "memory_refs": memory_refs,
            "watermark": event_watermark,
            "cursor": inbox_cursor,
        }
        packet = KT1Packet(
            succession_id=succession_id,
            objective=objective,
            decisions=list(decisions),
            evidence_refs=list(evidence_refs),
            grants_summary=list(grants_summary),
            open_commitments=list(open_commitments),
            current_task=current_task,
            memory_refs=list(memory_refs),
            event_watermark=event_watermark,
            inbox_cursor=inbox_cursor,
            content_digest=_digest(material),
        )
        rec.kt1 = packet
        if rec.phase == "final_kt":
            # Abrupt X→Y jump: KT1 recorded; remain quiesced for KT2 (no long shadow).
            rec.phase = "final_kt"
        else:
            rec.phase = "kt1_pending"
        return packet

    def trainee_ack_kt1(self, succession_id: str, *, ack_digest: str) -> SuccessionRecord:
        rec = self._by_id(succession_id)
        if rec.kt1 is None or rec.phase not in {"kt1_pending", "final_kt"}:
            raise SuccessionError("kt1_ack_requires_pending_packet")
        if ack_digest != rec.kt1.content_digest:
            rec.phase = "blocked"
            rec.blocked_reason = "kt1_integrity_mismatch"
            raise SuccessionError("kt1_integrity_mismatch")
        rec.trainee_ack_digest = ack_digest
        if rec.phase == "final_kt":
            # Jump path: stay in final_kt awaiting KT2.
            return rec
        rec.phase = "shadowing"
        return rec

    def begin_final_kt(self, succession_id: str) -> SuccessionRecord:
        rec = self._by_id(succession_id)
        if rec.phase in {"final_kt", "kt2_pending", "ready", "promoted"}:
            return rec
        if rec.phase not in {"shadowing", "trainee_created", "kt1_pending"}:
            raise SuccessionError(f"final_kt_illegal_from:{rec.phase}")
        # Quiesce predecessor: stop new ordinary work.
        lineage = self.get_lineage(rec.logical_agent_id)
        pred = lineage.incarnations[rec.predecessor_incarnation_id]
        if pred.role == "active":
            # Soft fence: still active until promote, but can_effect checks use phase.
            pass
        rec.phase = "final_kt"
        rec.cutover_watermark = rec.cutover_watermark or f"cut_{rec.succession_id}"
        return rec

    def issue_kt2(
        self,
        succession_id: str,
        *,
        deltas: list[str],
        unresolved_issues: list[str],
        final_event_watermark: str,
        final_inbox_cursor: int,
    ) -> KT2Packet:
        rec = self._by_id(succession_id)
        if rec.phase not in {"final_kt", "kt2_pending"}:
            raise SuccessionError(f"kt2_illegal_from:{rec.phase}")
        if rec.kt1 is None:
            raise SuccessionError("kt2_requires_kt1")
        material = {
            "kt1": rec.kt1.packet_id,
            "deltas": deltas,
            "unresolved": unresolved_issues,
            "watermark": final_event_watermark,
            "cursor": final_inbox_cursor,
        }
        packet = KT2Packet(
            succession_id=succession_id,
            kt1_packet_id=rec.kt1.packet_id,
            deltas=list(deltas),
            unresolved_issues=list(unresolved_issues),
            final_event_watermark=final_event_watermark,
            final_inbox_cursor=final_inbox_cursor,
            content_digest=_digest(material),
        )
        rec.kt2 = packet
        rec.phase = "kt2_pending"
        rec.cutover_watermark = final_event_watermark
        return packet

    def trainee_ack_kt2(self, succession_id: str, *, ack_digest: str) -> SuccessionRecord:
        rec = self._by_id(succession_id)
        if rec.phase != "kt2_pending" or rec.kt2 is None:
            raise SuccessionError("kt2_ack_requires_pending_packet")
        if ack_digest != rec.kt2.content_digest:
            rec.phase = "blocked"
            rec.blocked_reason = "kt2_integrity_mismatch"
            raise SuccessionError("kt2_integrity_mismatch")
        if rec.kt2.unresolved_issues:
            # Critical unresolved issues block promotion unless empty list.
            critical = [u for u in rec.kt2.unresolved_issues if u.startswith("critical:")]
            if critical:
                rec.phase = "blocked"
                rec.blocked_reason = "critical_unresolved:" + ",".join(critical)
                raise SuccessionError("critical_unresolved")
        rec.phase = "ready"
        return rec

    def promote(self, succession_id: str) -> SuccessionRecord:
        """Atomic fence: retire predecessor, activate trainee, bump generation."""
        rec = self._by_id(succession_id)
        if rec.phase != "ready":
            raise SuccessionError(f"promote_illegal_from:{rec.phase}")
        if rec.trainee_incarnation_id is None or rec.trainee_generation is None:
            raise SuccessionError("trainee_missing")
        if rec.kt1 is None or rec.kt2 is None:
            raise SuccessionError("packets_incomplete")
        if rec.trainee_ack_digest != rec.kt1.content_digest:
            raise SuccessionError("kt1_ack_missing")

        lineage = self.get_lineage(rec.logical_agent_id)
        pred = lineage.incarnations[rec.predecessor_incarnation_id]
        trainee = lineage.incarnations[rec.trainee_incarnation_id]

        # Fence predecessor — cannot effect after this point.
        pred.role = "retired"
        pred.retired_at = utc_now()
        trainee.role = "active"
        trainee.inbox_cursor = rec.kt2.final_inbox_cursor
        lineage.active_incarnation_id = trainee.incarnation_id

        rec.phase = "promoted"
        rec.promoted_at = utc_now()
        self._history.append(rec.model_copy(deep=True))
        # Clear open slot so a future succession can start on the new generation.
        del self._open[rec.logical_agent_id]
        return rec

    def can_issue_effects(self, logical_agent_id: str, *, generation: int) -> bool:
        """Generation fencing: only the active incarnation may issue effects."""
        lineage = self.get_lineage(logical_agent_id)
        active = lineage.active()
        if active.generation != generation:
            return False
        if active.role != "active":
            return False
        open_rec = self._open.get(logical_agent_id)
        if open_rec is not None and open_rec.phase in {"final_kt", "kt2_pending", "ready"}:
            # Predecessor quiesced during final KT — no new ordinary effects.
            if generation == open_rec.predecessor_generation:
                return False
        if open_rec is not None and open_rec.phase == "shadowing":
            # Trainee cannot issue effects while shadowing.
            if generation == open_rec.trainee_generation:
                return False
        return True

    def can_claim_work(self, logical_agent_id: str, *, generation: int) -> bool:
        return self.can_issue_effects(logical_agent_id, generation=generation)

    def usable_capacity(self, model_context_limit: int, *, output_reserve: int) -> int:
        """W = C - O - S - H with S folded into conservative estimate; H = kt reserve."""
        if model_context_limit <= 0:
            raise SuccessionError("invalid_context_limit")
        headroom = max(1, int(model_context_limit * self.policy.kt_reserve_fraction))
        usable = model_context_limit - output_reserve - headroom
        if usable <= 0:
            raise SuccessionError("usable_capacity_non_positive")
        return usable

    def occupancy_of(self, tokens_used: int, usable_capacity: int) -> OccupancySnapshot:
        if usable_capacity <= 0:
            raise SuccessionError("usable_capacity_non_positive")
        return OccupancySnapshot(
            tokens_used=tokens_used,
            usable_capacity=usable_capacity,
            occupancy=tokens_used / usable_capacity,
            count_method="conservative_estimate",
            count_uncertain=True,
        )

    def evidence(self) -> dict[str, Any]:
        return {
            "policy": self.policy.model_dump(mode="json"),
            "open": {
                k: v.model_dump(mode="json") for k, v in self._open.items()
            },
            "history": [r.model_dump(mode="json") for r in self._history],
            "lineages": {
                lid: {
                    "logical": st.logical.model_dump(mode="json"),
                    "active_incarnation_id": st.active_incarnation_id,
                    "incarnations": {
                        iid: inc.model_dump(mode="json") for iid, inc in st.incarnations.items()
                    },
                }
                for lid, st in self._lineages.items()
            },
        }

    def _by_id(self, succession_id: str) -> SuccessionRecord:
        for rec in self._open.values():
            if rec.succession_id == succession_id:
                return rec
        for rec in self._history:
            if rec.succession_id == succession_id:
                return rec
        raise SuccessionError("succession_not_found")


def phase_allows_trainee_effects(phase: SuccessionPhase) -> bool:
    return phase == "promoted"
