"""Authenticated agent messages — text cannot grant authority (PC-07)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, utc_now

MessageKind = Literal[
    "question",
    "answer",
    "suggestion",
    "evidence",
    "challenge",
    "lesson_offer",
    "lesson_feedback",
    "work_negotiation",
    "status",
    "request_help",
    "delegate",
    "kt_question",
    "handoff_kt",
]


class AuthenticatedMessage(StrictModel):
    """Durable addressed message with authenticated sender session/generation."""

    schema_version: str = "1.0"
    message_id: str = Field(default_factory=lambda: new_id("msg_"))
    project_id: str
    mission_id: str
    kind: MessageKind
    body: str
    # Authenticated identity — never trust body "from" claims.
    sender_logical_agent_id: str
    sender_session_id: str
    sender_generation: int
    recipient_logical_agent_id: str | None = None  # None = mission broadcast
    correlation_id: str | None = None
    reply_to: str | None = None
    event_order: int = 0
    evidence_refs: list[str] = Field(default_factory=list)
    artifact_refs: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    # Delivery bookkeeping (server-owned).
    delivered_to: list[str] = Field(default_factory=list)

    def authority_expanded(self) -> bool:
        return False


class DeliveryCursor(StrictModel):
    """Per-recipient inbox watermark for resume / succession catch-up."""

    schema_version: str = "1.0"
    mission_id: str
    logical_agent_id: str
    cursor: int = 0
    last_message_id: str | None = None
    updated_at: datetime = Field(default_factory=utc_now)
