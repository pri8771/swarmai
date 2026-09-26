"""V2.3 operations-platform contracts (ART-V23-SCHEDULER / PACKS / FLEET / OPS).

Shared by the scheduler, dispatch intents, scheduler epochs, capability-pack
lifecycle, fleet placement and ops events. Other sessions import from here and
never redefine these shapes.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol

from pydantic import Field

from swarm.contracts.common import StrictModel, new_id, payload_hash, utc_now

V23_POLICY_VERSION = "v23-wdrr-1"


class PriorityClass(StrEnum):
    BACKGROUND = "background"
    NORMAL = "normal"
    URGENT = "urgent"


PRIORITY_RANK: dict[PriorityClass, int] = {
    PriorityClass.BACKGROUND: 0,
    PriorityClass.NORMAL: 1,
    PriorityClass.URGENT: 2,
}


class MissionQueueLifecycle(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    DRAINING = "draining"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


SCHEDULABLE_MISSION_STATES: frozenset[MissionQueueLifecycle] = frozenset(
    {MissionQueueLifecycle.QUEUED, MissionQueueLifecycle.RUNNING}
)


class SchedulerDecision(StrEnum):
    ADMIT = "admit"
    DEFER = "defer"
    DENY = "deny"
    IDLE = "idle"


class ReasonCode(StrEnum):
    ADMITTED = "admitted"
    NO_ELIGIBLE_WORK = "no_eligible_work"
    DEFERRED_RESOURCE_UNAVAILABLE = "deferred_resource_unavailable"
    UNKNOWN_CAPACITY = "unknown_capacity"
    PROJECT_CONCURRENCY_CAP = "project_concurrency_cap"
    MISSION_PARALLELISM_CAP = "mission_parallelism_cap"
    BACKPRESSURE = "backpressure"
    STALE_SITE_EPOCH = "stale_site_epoch"
    STALE_SCHEDULER_EPOCH = "stale_scheduler_epoch"
    CANCELLED_GENERATION = "cancelled_generation"
    DRAINING = "draining"
    DUPLICATE_DISPATCH = "duplicate_dispatch"
    ISOLATION_DENIED = "isolation_denied"
    PAID_ROUTE_FORBIDDEN = "paid_route_forbidden"
    RESERVATION_FAILED = "reservation_failed"


class DispatchIntentState(StrEnum):
    PREPARED = "prepared"
    RESERVED = "reserved"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    COMPENSATED = "compensated"
    EXPIRED = "expired"


TERMINAL_INTENT_STATES: frozenset[DispatchIntentState] = frozenset(
    {
        DispatchIntentState.COMPLETED,
        DispatchIntentState.CANCELLED,
        DispatchIntentState.COMPENSATED,
        DispatchIntentState.EXPIRED,
    }
)


class PackLifecycleState(StrEnum):
    INSTALLED = "installed"
    ENABLED_FOR_PROJECT = "enabled_for_project"
    DRAINING = "draining"
    DISABLED = "disabled"
    UNINSTALLED = "uninstalled"


class TrustClass(StrEnum):
    OBSERVE_ONLY = "observe_only"
    SANDBOX_COMPUTE = "sandbox_compute"
    MODEL_WORKER = "model_worker"
    TOOL_WORKER = "tool_worker"
    INTEGRATION_WORKER = "integration_worker"


TRUST_RANK: dict[TrustClass, int] = {
    TrustClass.OBSERVE_ONLY: 0,
    TrustClass.SANDBOX_COMPUTE: 1,
    TrustClass.MODEL_WORKER: 2,
    TrustClass.TOOL_WORKER: 3,
    TrustClass.INTEGRATION_WORKER: 4,
}


class WorkerDrainState(StrEnum):
    ACTIVE = "active"
    DRAINING = "draining"
    DRAINED = "drained"
    REVOKED = "revoked"


class StaleVersionError(RuntimeError):
    """Optimistic-concurrency conflict: stored version != expected version."""


class ProjectQueueState(StrictModel):
    project_id: str
    tenant_id: str = "default"
    weight: float = Field(default=1.0, gt=0)
    credit: float = 0.0
    last_served_seq: int = Field(default=0, ge=0)
    paused: bool = False
    max_concurrency: int = Field(default=4, ge=0)
    running: int = Field(default=0, ge=0)
    version: int = Field(default=0, ge=0)
    policy_version: str = V23_POLICY_VERSION
    updated_at: datetime = Field(default_factory=utc_now)


class MissionQueueState(StrictModel):
    mission_id: str
    project_id: str
    lifecycle: MissionQueueLifecycle = MissionQueueLifecycle.QUEUED
    priority: PriorityClass = PriorityClass.NORMAL
    weight: float = Field(default=1.0, gt=0)
    credit: float = 0.0
    last_served_seq: int = Field(default=0, ge=0)
    max_parallelism: int = Field(default=2, ge=0)
    running: int = Field(default=0, ge=0)
    cancellation_generation: int = Field(default=0, ge=0)
    deadline_at: datetime | None = None
    enqueued_at: datetime = Field(default_factory=utc_now)
    version: int = Field(default=0, ge=0)
    updated_at: datetime = Field(default_factory=utc_now)


class SchedulableTask(StrictModel):
    task_id: str
    mission_id: str
    project_id: str
    attempt_id: str = Field(default_factory=lambda: new_id("att_"))
    priority: int = 0
    enqueued_at: datetime = Field(default_factory=utc_now)
    dependencies_ready: bool = True
    cancellation_generation: int = Field(default=0, ge=0)
    service_cost: float = Field(default=1.0, gt=0)
    worker_class: str = "local"
    provider_route: str | None = None
    tool_units: float = Field(default=0.0, ge=0)


class SchedulingDecisionReceipt(StrictModel):
    receipt_id: str = Field(default_factory=lambda: new_id("sdr_"))
    sequence: int = Field(ge=1)
    decision: SchedulerDecision
    reason_code: ReasonCode
    project_id: str | None = None
    mission_id: str | None = None
    task_id: str | None = None
    attempt_id: str | None = None
    policy_version: str = V23_POLICY_VERSION
    site_id: str = "local"
    site_epoch: int = Field(default=0, ge=0)
    scheduler_epoch: int = Field(default=0, ge=0)
    candidate_set_hash: str = ""
    scores: dict[str, float] = Field(default_factory=dict)
    credits_before: dict[str, float] = Field(default_factory=dict)
    credits_after: dict[str, float] = Field(default_factory=dict)
    dispatch_intent_id: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    def digest(self) -> str:
        """Content digest that ignores receipt_id and created_at (replay-stable)."""
        return payload_hash(self.model_dump(mode="json", exclude={"receipt_id", "created_at"}))


class DispatchIntentComponent(StrictModel):
    kind: str  # "worker" | "provider" | "tool" | "budget"
    ref: str
    amount: float = Field(default=1.0, ge=0)
    reserved: bool = False
    reservation_id: str | None = None


class DispatchIntent(StrictModel):
    intent_id: str = Field(default_factory=lambda: new_id("din_"))
    attempt_id: str
    project_id: str
    mission_id: str
    task_id: str
    state: DispatchIntentState = DispatchIntentState.PREPARED
    components: list[DispatchIntentComponent] = Field(default_factory=list)
    site_epoch: int = Field(default=0, ge=0)
    scheduler_epoch: int = Field(default=0, ge=0)
    cancellation_generation: int = Field(default=0, ge=0)
    attempt_digest: str = ""
    expires_at: datetime
    failure_reason: str | None = None
    version: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SchedulerEpochLease(StrictModel):
    site_id: str = "local"
    epoch: int = Field(default=0, ge=0)
    holder_id: str
    acquired_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    version: int = Field(default=0, ge=0)


class OpsEventRecord(StrictModel):
    event_id: str = Field(default_factory=lambda: new_id("oev_"))
    kind: str
    component: str
    project_id: str | None = None
    tenant_id: str | None = None
    site_epoch: int | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    parent_event_id: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)
    at: datetime = Field(default_factory=utc_now)


class SchedulingStore(Protocol):
    """Durable scheduler state. Versioning rule for every ``put_*``:

    * ``expected_version=None`` inserts; raises StaleVersionError if the key exists;
      the stored copy has ``version=1``.
    * otherwise the stored version must equal ``expected_version``; the stored copy
      gets ``version=expected_version + 1``. Mismatch raises StaleVersionError.
    * ``put_*`` returns the stored copy (with the new version).
    """

    def get_project(self, project_id: str) -> ProjectQueueState | None: ...

    def list_projects(self) -> list[ProjectQueueState]: ...

    def put_project(
        self, state: ProjectQueueState, *, expected_version: int | None
    ) -> ProjectQueueState: ...

    def get_mission(self, mission_id: str) -> MissionQueueState | None: ...

    def list_missions(self, project_id: str | None = None) -> list[MissionQueueState]: ...

    def put_mission(
        self, state: MissionQueueState, *, expected_version: int | None
    ) -> MissionQueueState: ...

    def next_sequence(self) -> int: ...

    def append_receipt(self, receipt: SchedulingDecisionReceipt) -> None: ...

    def list_receipts(
        self, *, project_id: str | None = None, limit: int = 100
    ) -> list[SchedulingDecisionReceipt]: ...

    def get_intent(self, intent_id: str) -> DispatchIntent | None: ...

    def get_intent_by_attempt(self, attempt_id: str) -> DispatchIntent | None: ...

    def put_intent(
        self, intent: DispatchIntent, *, expected_version: int | None
    ) -> DispatchIntent: ...

    def list_intents(
        self, *, states: frozenset[DispatchIntentState] | None = None
    ) -> list[DispatchIntent]: ...


__all__ = [
    "PRIORITY_RANK",
    "SCHEDULABLE_MISSION_STATES",
    "TERMINAL_INTENT_STATES",
    "TRUST_RANK",
    "V23_POLICY_VERSION",
    "DispatchIntent",
    "DispatchIntentComponent",
    "DispatchIntentState",
    "MissionQueueLifecycle",
    "MissionQueueState",
    "OpsEventRecord",
    "PackLifecycleState",
    "PriorityClass",
    "ProjectQueueState",
    "ReasonCode",
    "SchedulableTask",
    "SchedulerDecision",
    "SchedulerEpochLease",
    "SchedulingDecisionReceipt",
    "SchedulingStore",
    "StaleVersionError",
    "TrustClass",
    "WorkerDrainState",
]
