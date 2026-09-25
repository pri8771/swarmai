"""X/Y context succession contracts — KT1/KT2 + fencing (PC-07 / P11)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from swarm.contracts.common import StrictModel, new_id, utc_now

SuccessionPhase = Literal[
    "idle",
    "trainee_created",
    "kt1_pending",
    "shadowing",
    "final_kt",
    "kt2_pending",
    "ready",
    "promoted",
    "blocked",
]


class OccupancyPolicy(StrictModel):
    """Usable-input occupancy thresholds. Defaults from FAST_TRACK (X=0.65, Y=0.80)."""

    schema_version: str = "1.0"
    trainee_at: float = 0.65
    takeover_at: float = 0.80
    kt_reserve_fraction: float = 0.15

    @model_validator(mode="after")
    def _ordered(self) -> OccupancyPolicy:
        if not (0.0 < self.trainee_at < self.takeover_at < 1.0):
            raise ValueError("require_0_lt_X_lt_Y_lt_1")
        if not (0.0 < self.kt_reserve_fraction < 1.0):
            raise ValueError("kt_reserve_must_be_in_(0,1)")
        return self


class OccupancySnapshot(StrictModel):
    """Measured occupancy against usable input capacity W."""

    schema_version: str = "1.0"
    tokens_used: int
    usable_capacity: int
    occupancy: float
    count_method: str = "conservative_estimate"
    count_uncertain: bool = True
    observed_at: datetime = Field(default_factory=utc_now)


class KT1Packet(StrictModel):
    """Initial knowledge transfer — objective, decisions, grants, commitments, memory refs."""

    schema_version: str = "1.0"
    packet_id: str = Field(default_factory=lambda: new_id("kt1_"))
    succession_id: str
    objective: str
    decisions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    grants_summary: list[str] = Field(default_factory=list)
    open_commitments: list[str] = Field(default_factory=list)
    current_task: str = ""
    memory_refs: list[str] = Field(default_factory=list)
    event_watermark: str
    inbox_cursor: int = 0
    content_digest: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class KT2Packet(StrictModel):
    """Final transfer — deltas since KT1 + final watermark."""

    schema_version: str = "1.0"
    packet_id: str = Field(default_factory=lambda: new_id("kt2_"))
    succession_id: str
    kt1_packet_id: str
    deltas: list[str] = Field(default_factory=list)
    unresolved_issues: list[str] = Field(default_factory=list)
    final_event_watermark: str
    final_inbox_cursor: int = 0
    content_digest: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class SuccessionRecord(StrictModel):
    """One open succession per logical lineage (enforced by service)."""

    schema_version: str = "1.0"
    succession_id: str = Field(default_factory=lambda: new_id("suc_"))
    mission_id: str
    project_id: str
    logical_agent_id: str
    predecessor_incarnation_id: str
    predecessor_generation: int
    trainee_incarnation_id: str | None = None
    trainee_generation: int | None = None
    phase: SuccessionPhase = "idle"
    policy: OccupancyPolicy = Field(default_factory=OccupancyPolicy)
    trigger_occupancy: OccupancySnapshot | None = None
    kt1: KT1Packet | None = None
    kt2: KT2Packet | None = None
    trainee_ack_digest: str | None = None
    cutover_watermark: str | None = None
    blocked_reason: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    promoted_at: datetime | None = None
