"""V3.0 persistent objective contracts."""

from __future__ import annotations

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, utc_now


class ObjectiveContract(StrictModel):
    objective_id: str = Field(default_factory=lambda: new_id("obj_"))
    project_id: str
    version: int = 1
    goal: str
    trigger_policy: str = "manual"  # manual|schedule|event
    schedule_cron: str | None = None
    event_types: list[str] = Field(default_factory=list)
    rate_limit_per_hour: int = 1
    max_active_missions: int = 1
    allowed_mission_templates: list[str] = Field(default_factory=list)
    tool_envelope: list[str] = Field(default_factory=list)
    data_envelope: list[str] = Field(default_factory=list)
    provider_envelope: list[str] = Field(default_factory=list)
    spend_usd_ceiling: float = 0.0
    state: str = "active"  # active|paused|revoked|expired
    stop_conditions: list[str] = Field(default_factory=list)
    expires_at: str | None = None
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class MissionProposal(StrictModel):
    proposal_id: str = Field(default_factory=lambda: new_id("mpr_"))
    objective_id: str
    objective_version: int
    project_id: str
    goal: str
    template_id: str
    state: str = "proposed"  # proposed|admitted|rejected|duplicate
    mission_id: str | None = None
    dedupe_key: str
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
