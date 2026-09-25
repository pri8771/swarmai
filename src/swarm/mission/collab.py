"""Collaborative mission communication + context handoff (V1.7 / PC-07).

Agents on one mission exchange authenticated scoped messages and transfer
working context with provenance. Kernel authority is not expanded by message
text. Deterministic / offline only for this module.

PC-07 extensions:
- optional DurableMissionMailbox for authenticated durable messages
- optional SuccessionService for real X/Y KT1/KT2 fencing
- legacy prepare_handoff/adopt_handoff retained for existing campaigns
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.agent import LogicalAgent
from swarm.contracts.common import new_id, utc_now
from swarm.contracts.succession import OccupancySnapshot
from swarm.mission.mailbox import DurableMissionMailbox
from swarm.runtime.succession import SuccessionError, SuccessionService


@dataclass
class MissionMessage:
    message_id: str
    mission_id: str
    from_agent: str
    to_agent: str | None
    kind: str  # request_help | evidence | delegate | status | handoff_kt
    body: str
    evidence_refs: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    # PC-07 optional auth metadata (populated when mailbox is used).
    sender_session_id: str | None = None
    sender_generation: int | None = None
    event_order: int | None = None
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "mission_id": self.mission_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "kind": self.kind,
            "body": self.body,
            "evidence_refs": list(self.evidence_refs),
            "created_at": self.created_at,
            "sender_session_id": self.sender_session_id,
            "sender_generation": self.sender_generation,
            "event_order": self.event_order,
            "correlation_id": self.correlation_id,
        }


@dataclass
class ContextHandoff:
    """X→Y succession packet — digest + watermark; does not grant authority."""

    handoff_id: str
    mission_id: str
    from_agent: str
    to_agent: str
    context_digest: str
    event_watermark: str
    inbox_cursor: int
    retained_facts: list[str]
    open_commitments: list[str]
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    adopted: bool = False
    succession_id: str | None = None
    kt1_digest: str | None = None
    kt2_digest: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "mission_id": self.mission_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "context_digest": self.context_digest,
            "event_watermark": self.event_watermark,
            "inbox_cursor": self.inbox_cursor,
            "retained_facts": list(self.retained_facts),
            "open_commitments": list(self.open_commitments),
            "created_at": self.created_at,
            "adopted": self.adopted,
            "authority_expanded": False,
            "succession_id": self.succession_id,
            "kt1_digest": self.kt1_digest,
            "kt2_digest": self.kt2_digest,
        }


@dataclass
class CollaborativeMissionBoard:
    """In-process authenticated mission board (server authority when wired to API)."""

    mission_id: str
    project_id: str = "proj_local"
    agents: set[str] = field(default_factory=set)
    messages: list[MissionMessage] = field(default_factory=list)
    handoffs: list[ContextHandoff] = field(default_factory=list)
    active_generation: dict[str, int] = field(default_factory=dict)
    # PC-07 optional services
    mailbox: DurableMissionMailbox | None = None
    succession: SuccessionService | None = None
    _session_secrets: dict[str, tuple[str, str]] = field(default_factory=dict)
    # logical_agent_id -> (session_id, secret)
    _logical_ids: dict[str, str] = field(default_factory=dict)  # agent display -> logical id

    def enable_durable_mailbox(self, root: Path) -> DurableMissionMailbox:
        self.mailbox = DurableMissionMailbox(
            mission_id=self.mission_id,
            project_id=self.project_id,
            root=root,
        )
        for agent_id in list(self.agents):
            self._ensure_mailbox_agent(agent_id)
        return self.mailbox

    def enable_succession(self, service: SuccessionService | None = None) -> SuccessionService:
        self.succession = service or SuccessionService()
        for agent_id in list(self.agents):
            self._ensure_lineage(agent_id)
        return self.succession

    def join(self, agent_id: str) -> None:
        self.agents.add(agent_id)
        self.active_generation.setdefault(agent_id, 1)
        if self.mailbox is not None:
            self._ensure_mailbox_agent(agent_id)
        if self.succession is not None:
            self._ensure_lineage(agent_id)

    def _ensure_mailbox_agent(self, agent_id: str) -> None:
        assert self.mailbox is not None
        if agent_id in self._session_secrets:
            return
        session_id, secret = self.mailbox.join(
            agent_id, generation=self.active_generation.get(agent_id, 1)
        )
        self._session_secrets[agent_id] = (session_id, secret)

    def _ensure_lineage(self, agent_id: str) -> None:
        assert self.succession is not None
        if agent_id in self._logical_ids:
            return
        logical = LogicalAgent(
            logical_agent_id=agent_id if agent_id.startswith("lag_") else new_id("lag_"),
            project_id=self.project_id,
            display_name=agent_id,
            role="mission_agent",
        )
        # Preserve stable display mapping; use display id as logical when already namespaced.
        if not agent_id.startswith("lag_"):
            # Keep agent_id as the board key; store generated logical id.
            pass
        try:
            # Prefer registering under the board agent id for fencing lookups.
            logical = logical.model_copy(update={"logical_agent_id": agent_id})
            self.succession.register_logical(logical, mission_id=self.mission_id)
        except SuccessionError:
            # Already registered.
            pass
        self._logical_ids[agent_id] = agent_id

    def session_for(self, agent_id: str) -> tuple[str, str]:
        if agent_id not in self._session_secrets:
            raise PermissionError("session_not_issued")
        return self._session_secrets[agent_id]

    def post(
        self,
        *,
        from_agent: str,
        kind: str,
        body: str,
        to_agent: str | None = None,
        evidence_refs: list[str] | None = None,
        correlation_id: str | None = None,
        require_auth: bool = False,
    ) -> MissionMessage:
        if from_agent not in self.agents:
            raise PermissionError("agent_not_on_mission")
        if to_agent is not None and to_agent not in self.agents:
            raise PermissionError("recipient_not_on_mission")
        # Message text cannot invent new capabilities.
        forbidden = ("expand_budget", "grant_admin", "bypass_kernel", "self_accept")
        lowered = body.lower()
        if any(tok in lowered for tok in forbidden):
            raise PermissionError("message_authority_expansion_forbidden")

        # Generation fence when succession is enabled.
        if self.succession is not None:
            gen = self.active_generation.get(from_agent, 1)
            if not self.succession.can_issue_effects(from_agent, generation=gen):
                # Allow trainee kt_question / status during shadowing only for kt kinds.
                if kind not in {"kt_question", "status", "handoff_kt"}:
                    raise PermissionError("generation_fenced")

        sender_session_id = None
        sender_generation = None
        event_order = None
        if self.mailbox is not None:
            if from_agent not in self._session_secrets:
                self._ensure_mailbox_agent(from_agent)
            session_id, secret = self._session_secrets[from_agent]
            auth_msg = self.mailbox.post(
                session_id=session_id,
                secret=secret,
                kind=kind,  # type: ignore[arg-type]
                body=body,
                to_logical_agent_id=to_agent,
                evidence_refs=evidence_refs,
                correlation_id=correlation_id,
            )
            sender_session_id = auth_msg.sender_session_id
            sender_generation = auth_msg.sender_generation
            event_order = auth_msg.event_order
        elif require_auth:
            raise PermissionError("mailbox_required_for_auth")

        msg = MissionMessage(
            message_id=new_id("msg_"),
            mission_id=self.mission_id,
            from_agent=from_agent,
            to_agent=to_agent,
            kind=kind,
            body=body,
            evidence_refs=list(evidence_refs or []),
            sender_session_id=sender_session_id,
            sender_generation=sender_generation,
            event_order=event_order,
            correlation_id=correlation_id,
        )
        self.messages.append(msg)
        return msg

    def prepare_handoff(
        self,
        *,
        from_agent: str,
        to_agent: str,
        retained_facts: list[str],
        open_commitments: list[str],
        event_watermark: str,
    ) -> ContextHandoff:
        if from_agent not in self.agents or to_agent not in self.agents:
            raise PermissionError("handoff_agents_not_on_mission")
        cursor = len(self.messages)
        material = json.dumps(
            {
                "mission_id": self.mission_id,
                "from": from_agent,
                "to": to_agent,
                "facts": retained_facts,
                "commitments": open_commitments,
                "watermark": event_watermark,
                "cursor": cursor,
            },
            sort_keys=True,
        )
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
        succession_id = None
        kt1_digest = None
        kt2_digest = None

        # When succession is enabled on the same logical lineage (X→Y trainee),
        # drive KT1/KT2 packets. Peer handoff between distinct agents keeps legacy path.
        if self.succession is not None and from_agent == to_agent:
            self._ensure_lineage(from_agent)
            usable = self.succession.usable_capacity(8192, output_reserve=512)
            snap = self.succession.occupancy_of(int(usable * 0.85), usable)
            rec = self.succession.observe_occupancy(
                mission_id=self.mission_id,
                project_id=self.project_id,
                logical_agent_id=from_agent,
                snapshot=snap,
            )
            if rec is None:
                raise SuccessionError("succession_not_triggered")
            if rec.kt1 is None:
                kt1 = self.succession.issue_kt1(
                    rec.succession_id,
                    objective=f"continue mission {self.mission_id}",
                    decisions=list(retained_facts),
                    evidence_refs=[],
                    grants_summary=[],
                    open_commitments=list(open_commitments),
                    current_task="handoff",
                    memory_refs=[],
                    event_watermark=event_watermark,
                    inbox_cursor=cursor,
                )
                self.succession.trainee_ack_kt1(rec.succession_id, ack_digest=kt1.content_digest)
                kt1_digest = kt1.content_digest
            self.succession.begin_final_kt(rec.succession_id)
            kt2 = self.succession.issue_kt2(
                rec.succession_id,
                deltas=[f"facts:{len(retained_facts)}"],
                unresolved_issues=[],
                final_event_watermark=event_watermark,
                final_inbox_cursor=cursor,
            )
            kt2_digest = kt2.content_digest
            succession_id = rec.succession_id

        handoff = ContextHandoff(
            handoff_id=new_id("ho_"),
            mission_id=self.mission_id,
            from_agent=from_agent,
            to_agent=to_agent,
            context_digest=digest,
            event_watermark=event_watermark,
            inbox_cursor=cursor,
            retained_facts=list(retained_facts),
            open_commitments=list(open_commitments),
            succession_id=succession_id,
            kt1_digest=kt1_digest,
            kt2_digest=kt2_digest,
        )
        self.handoffs.append(handoff)
        return handoff

    def adopt_handoff(self, handoff_id: str, *, by_agent: str) -> ContextHandoff:
        for handoff in self.handoffs:
            if handoff.handoff_id != handoff_id:
                continue
            if by_agent != handoff.to_agent:
                raise PermissionError("handoff_adopter_mismatch")

            if (
                self.succession is not None
                and handoff.succession_id is not None
                and handoff.kt2_digest is not None
            ):
                self.succession.trainee_ack_kt2(
                    handoff.succession_id, ack_digest=handoff.kt2_digest
                )
                promoted = self.succession.promote(handoff.succession_id)
                # Logical identity preserved; generation advances on successor incarnation.
                self.active_generation[by_agent] = int(promoted.trainee_generation or 0)
                if self.mailbox is not None:
                    session_id, secret = self.mailbox.rotate_session(
                        by_agent, generation=self.active_generation[by_agent]
                    )
                    self._session_secrets[by_agent] = (session_id, secret)
            else:
                # Legacy peer handoff: generation bump on successor; predecessor fenced.
                self.active_generation[handoff.from_agent] = (
                    self.active_generation.get(handoff.from_agent, 1) + 0
                )
                self.active_generation[by_agent] = self.active_generation.get(by_agent, 1) + 1

            handoff.adopted = True
            return handoff
        raise KeyError(handoff_id)

    def can_claim_work(self, agent_id: str) -> bool:
        """Predecessor after adopted handoff cannot claim new work."""
        if agent_id not in self.agents:
            return False
        if self.succession is not None:
            gen = self.active_generation.get(agent_id, 1)
            try:
                return self.succession.can_claim_work(agent_id, generation=gen)
            except SuccessionError:
                pass
        if not self.handoffs:
            return True
        for handoff in self.handoffs:
            if handoff.adopted and handoff.from_agent == agent_id and handoff.to_agent != agent_id:
                return False
            # Same-agent succession: after adopt, only current generation may claim —
            # handled via active_generation / succession service above.
            if (
                handoff.adopted
                and handoff.from_agent == agent_id
                and handoff.to_agent == agent_id
                and handoff.succession_id is None
            ):
                return False
        return True

    def run_xy_succession(
        self,
        *,
        logical_agent_id: str,
        occupancy: OccupancySnapshot,
        objective: str,
        retained_facts: list[str],
        open_commitments: list[str],
        event_watermark: str,
        deltas: list[str] | None = None,
    ) -> ContextHandoff:
        """Full X/Y KT1→shadow→KT2→promote for one logical agent lineage."""
        if self.succession is None:
            self.enable_succession()
        assert self.succession is not None
        self.join(logical_agent_id)
        rec = self.succession.observe_occupancy(
            mission_id=self.mission_id,
            project_id=self.project_id,
            logical_agent_id=logical_agent_id,
            snapshot=occupancy,
        )
        if rec is None:
            raise SuccessionError("occupancy_below_x")
        cursor = len(self.messages)
        if rec.kt1 is None:
            kt1 = self.succession.issue_kt1(
                rec.succession_id,
                objective=objective,
                decisions=list(retained_facts),
                evidence_refs=[],
                grants_summary=[],
                open_commitments=list(open_commitments),
                current_task=objective,
                memory_refs=[],
                event_watermark=event_watermark,
                inbox_cursor=cursor,
            )
            self.succession.trainee_ack_kt1(rec.succession_id, ack_digest=kt1.content_digest)
        else:
            kt1 = rec.kt1
        self.succession.begin_final_kt(rec.succession_id)
        kt2 = self.succession.issue_kt2(
            rec.succession_id,
            deltas=list(deltas or retained_facts),
            unresolved_issues=[],
            final_event_watermark=event_watermark,
            final_inbox_cursor=cursor,
        )
        handoff = ContextHandoff(
            handoff_id=new_id("ho_"),
            mission_id=self.mission_id,
            from_agent=logical_agent_id,
            to_agent=logical_agent_id,
            context_digest=kt2.content_digest,
            event_watermark=event_watermark,
            inbox_cursor=cursor,
            retained_facts=list(retained_facts),
            open_commitments=list(open_commitments),
            succession_id=rec.succession_id,
            kt1_digest=kt1.content_digest,
            kt2_digest=kt2.content_digest,
        )
        self.handoffs.append(handoff)
        return self.adopt_handoff(handoff.handoff_id, by_agent=logical_agent_id)

    def evidence(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "mission_id": self.mission_id,
            "project_id": self.project_id,
            "agents": sorted(self.agents),
            "message_count": len(self.messages),
            "messages": [m.to_dict() for m in self.messages],
            "handoffs": [h.to_dict() for h in self.handoffs],
            "active_generation": dict(self.active_generation),
            "spend_usd": 0,
        }
        if self.mailbox is not None:
            payload["mailbox"] = self.mailbox.evidence()
        if self.succession is not None:
            payload["succession"] = self.succession.evidence()
        return payload

    def dump(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.evidence(), indent=2) + "\n", encoding="utf-8")
