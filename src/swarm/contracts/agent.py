"""Logical agent identity vs replaceable session/incarnation (PC-07 / P11)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, utc_now

IncarnationRole = Literal["active", "trainee", "retired", "blocked"]


class LogicalAgent(StrictModel):
    """Durable agent identity — survives session/generation replacement."""

    schema_version: str = "1.0"
    logical_agent_id: str = Field(default_factory=lambda: new_id("lag_"))
    project_id: str
    display_name: str
    role: str
    personality: str = ""
    profile_id: str | None = None
    runtime_id: str = "native"
    model_policy: str = "default"
    interaction_policy: str = "same_mission_peers"
    created_at: datetime = Field(default_factory=utc_now)


class AgentIncarnation(StrictModel):
    """One generation of a logical agent — session-bound, fenced by generation."""

    schema_version: str = "1.0"
    incarnation_id: str = Field(default_factory=lambda: new_id("inc_"))
    logical_agent_id: str
    generation: int = 1
    session_id: str = Field(default_factory=lambda: new_id("as_"))
    mission_id: str | None = None
    role: IncarnationRole = "active"
    context_manifest_ref: str | None = None
    inbox_cursor: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    retired_at: datetime | None = None
