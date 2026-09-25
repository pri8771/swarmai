"""Collaborative mission communication + context handoff (V1.7, no spend).

Agents on one mission exchange authenticated scoped messages and transfer
working context with provenance. Kernel authority is not expanded by message
text. Deterministic / offline only for this module.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now


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
        }


@dataclass
class CollaborativeMissionBoard:
    """In-process authenticated mission board (server authority when wired to API)."""

    mission_id: str
    agents: set[str] = field(default_factory=set)
    messages: list[MissionMessage] = field(default_factory=list)
    handoffs: list[ContextHandoff] = field(default_factory=list)
    active_generation: dict[str, int] = field(default_factory=dict)

    def join(self, agent_id: str) -> None:
        self.agents.add(agent_id)
        self.active_generation.setdefault(agent_id, 1)

    def post(
        self,
        *,
        from_agent: str,
        kind: str,
        body: str,
        to_agent: str | None = None,
        evidence_refs: list[str] | None = None,
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
        msg = MissionMessage(
            message_id=new_id("msg_"),
            mission_id=self.mission_id,
            from_agent=from_agent,
            to_agent=to_agent,
            kind=kind,
            body=body,
            evidence_refs=list(evidence_refs or []),
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
        )
        self.handoffs.append(handoff)
        return handoff

    def adopt_handoff(self, handoff_id: str, *, by_agent: str) -> ContextHandoff:
        for handoff in self.handoffs:
            if handoff.handoff_id != handoff_id:
                continue
            if by_agent != handoff.to_agent:
                raise PermissionError("handoff_adopter_mismatch")
            # Generation bump on successor; predecessor stops new claims at fence.
            self.active_generation[handoff.from_agent] = (
                self.active_generation.get(handoff.from_agent, 1) + 0
            )  # frozen marker below
            self.active_generation[by_agent] = self.active_generation.get(by_agent, 1) + 1
            handoff.adopted = True
            return handoff
        raise KeyError(handoff_id)

    def can_claim_work(self, agent_id: str) -> bool:
        """Predecessor after adopted handoff cannot claim new work."""
        if not self.handoffs:
            return agent_id in self.agents
        for handoff in self.handoffs:
            if handoff.adopted and handoff.from_agent == agent_id:
                return False
        return agent_id in self.agents

    def evidence(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "agents": sorted(self.agents),
            "message_count": len(self.messages),
            "messages": [m.to_dict() for m in self.messages],
            "handoffs": [h.to_dict() for h in self.handoffs],
            "active_generation": dict(self.active_generation),
            "spend_usd": 0,
        }

    def dump(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.evidence(), indent=2) + "\n", encoding="utf-8")
