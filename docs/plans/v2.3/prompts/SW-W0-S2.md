# SW-W0-S2 — V2.3 shared contracts, scheduling package, in-memory store, ORM rows, single migration a23opsplatform0001

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W0-S2` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w0-s2-contracts-schema` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 0 |
| Depends on | none |
| Handoff file | `docs/v2.3/sessions/SW-W0-S2.md` |
| Independent reviewer | Codex (owner decision D2). You never accept your own work. |
| Plan | `docs/plans/v2.3/PLAN.md`; owner preflight `docs/plans/v2.3/OWNER_PREFLIGHT.md`; decisions `docs/swarm-mvp/DECISIONS.md` |

## 0. Hard rules (read twice)
1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.
2. Never push to, or merge into, `main`, `dev` or `cursor/sw-v23-integration-460c`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `cursor/sw-v23-integration-460c`.
3. Zero spend: no real model/provider calls, no paid APIs, no account creation, no deploys. `SWARM_ALLOW_PAID` stays `false`. Tests use fakes only.
4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n "$NAME"`.
5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.
6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).
7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.
8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.

## 1. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (S1)
git fetch origin cursor/sw-v23-integration-460c
git ls-remote --exit-code origin refs/heads/cursor/sw-v23-integration-460c >/dev/null && echo INTEG_OK || echo INTEG_MISSING
```
If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it.
```bash
git checkout -b cursor/v23-w0-s2-contracts-schema origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
This session has **no dependencies**. Go to Step 1.

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/contracts/v23.py` — create
- `src/swarm/scheduling/__init__.py` — create
- `src/swarm/scheduling/memory_store.py` — create
- `src/swarm/db/models.py` — modify (append at end of file only)
- `migrations/versions/a23opsplatform0001_v23_ops_platform.py` — create
- `tests/integration/db/test_action_receipts_durable.py` — modify (only the NEW_HEAD constant)
- `tests/contracts/test_v23_contracts.py` — create
- `tests/controller/test_v23_store_memory.py` — create
- `tests/integration/db/test_v23_schema.py` — create
- `docs/v2.3/sessions/SW-W0-S2.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Create the shared V2.3 data contracts, the `swarm.scheduling` package with an in-memory reference store, the ORM rows, and the **only** V2.3 Alembic migration. Every later session imports these; nobody else edits them.

The code below was compiled, type-checked, and tested against `dev @ 8e1c0fde` (ruff, mypy, 548 offline tests, 70 integration tests). Paste it **exactly**.

### Step 1 — `src/swarm/contracts/v23.py` (create, exactly)
```python
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
```

### Step 2 — `src/swarm/scheduling/__init__.py` (create, exactly one line)
```python
"""V2.3 scheduler package (ART-V23-SCHEDULER)."""
```

### Step 3 — `src/swarm/scheduling/memory_store.py` (create, exactly)
```python
"""In-memory SchedulingStore — reference semantics for the SQL store and for tests."""

from __future__ import annotations

import threading

from swarm.contracts.common import utc_now
from swarm.contracts.v23 import (
    DispatchIntent,
    DispatchIntentState,
    MissionQueueState,
    ProjectQueueState,
    SchedulingDecisionReceipt,
    StaleVersionError,
)


class InMemorySchedulingStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._projects: dict[str, ProjectQueueState] = {}
        self._missions: dict[str, MissionQueueState] = {}
        self._receipts: list[SchedulingDecisionReceipt] = []
        self._intents: dict[str, DispatchIntent] = {}
        self._intent_by_attempt: dict[str, str] = {}
        self._sequence = 0

    @staticmethod
    def _check(current_version: int | None, expected_version: int | None, key: str) -> int:
        if expected_version is None:
            if current_version is not None:
                raise StaleVersionError(f"already_exists:{key}")
            return 1
        if current_version != expected_version:
            raise StaleVersionError(
                f"stale_version:{key}:expected={expected_version}:actual={current_version}"
            )
        return expected_version + 1

    def get_project(self, project_id: str) -> ProjectQueueState | None:
        with self._lock:
            row = self._projects.get(project_id)
            return row.model_copy() if row else None

    def list_projects(self) -> list[ProjectQueueState]:
        with self._lock:
            return [self._projects[k].model_copy() for k in sorted(self._projects)]

    def put_project(
        self, state: ProjectQueueState, *, expected_version: int | None
    ) -> ProjectQueueState:
        with self._lock:
            cur = self._projects.get(state.project_id)
            version = self._check(cur.version if cur else None, expected_version, state.project_id)
            stored = state.model_copy(update={"version": version, "updated_at": utc_now()})
            self._projects[state.project_id] = stored
            return stored.model_copy()

    def get_mission(self, mission_id: str) -> MissionQueueState | None:
        with self._lock:
            row = self._missions.get(mission_id)
            return row.model_copy() if row else None

    def list_missions(self, project_id: str | None = None) -> list[MissionQueueState]:
        with self._lock:
            rows = [self._missions[k] for k in sorted(self._missions)]
            if project_id is not None:
                rows = [m for m in rows if m.project_id == project_id]
            return [m.model_copy() for m in rows]

    def put_mission(
        self, state: MissionQueueState, *, expected_version: int | None
    ) -> MissionQueueState:
        with self._lock:
            cur = self._missions.get(state.mission_id)
            version = self._check(cur.version if cur else None, expected_version, state.mission_id)
            stored = state.model_copy(update={"version": version, "updated_at": utc_now()})
            self._missions[state.mission_id] = stored
            return stored.model_copy()

    def next_sequence(self) -> int:
        with self._lock:
            self._sequence += 1
            return self._sequence

    def append_receipt(self, receipt: SchedulingDecisionReceipt) -> None:
        with self._lock:
            if any(r.sequence == receipt.sequence for r in self._receipts):
                raise StaleVersionError(f"duplicate_receipt_sequence:{receipt.sequence}")
            self._receipts.append(receipt.model_copy())

    def list_receipts(
        self, *, project_id: str | None = None, limit: int = 100
    ) -> list[SchedulingDecisionReceipt]:
        with self._lock:
            rows = sorted(self._receipts, key=lambda r: r.sequence)
            if project_id is not None:
                rows = [r for r in rows if r.project_id == project_id]
            return [r.model_copy() for r in rows[-limit:]]

    def get_intent(self, intent_id: str) -> DispatchIntent | None:
        with self._lock:
            row = self._intents.get(intent_id)
            return row.model_copy() if row else None

    def get_intent_by_attempt(self, attempt_id: str) -> DispatchIntent | None:
        with self._lock:
            intent_id = self._intent_by_attempt.get(attempt_id)
            return self.get_intent(intent_id) if intent_id else None

    def put_intent(
        self, intent: DispatchIntent, *, expected_version: int | None
    ) -> DispatchIntent:
        with self._lock:
            cur = self._intents.get(intent.intent_id)
            if expected_version is None:
                other = self._intent_by_attempt.get(intent.attempt_id)
                if other is not None:
                    raise StaleVersionError(f"attempt_already_has_intent:{intent.attempt_id}")
            version = self._check(cur.version if cur else None, expected_version, intent.intent_id)
            stored = intent.model_copy(update={"version": version, "updated_at": utc_now()})
            self._intents[intent.intent_id] = stored
            self._intent_by_attempt[intent.attempt_id] = intent.intent_id
            return stored.model_copy()

    def list_intents(
        self, *, states: frozenset[DispatchIntentState] | None = None
    ) -> list[DispatchIntent]:
        with self._lock:
            rows = [self._intents[k] for k in sorted(self._intents)]
            if states is not None:
                rows = [i for i in rows if i.state in states]
            return [i.model_copy() for i in rows]
```

### Step 4 — append ORM rows to `src/swarm/db/models.py`
Open the file, go to the **very end** (after `class PursuitDedupeRow`), and append this block. Do not change anything above it. No new imports are needed (`BigInteger, DateTime, Index, Integer, String, UniqueConstraint, func, JSONB, Mapped, mapped_column, Any, datetime` are already imported).
```python


# --- V2.3 operations platform (ART-V23) + V2.0 durable holds/lessons -----------
# Row shape rule: key/index columns + ``version`` + full model JSON in ``payload``.
# Repositories read ``payload`` back with ``Model.model_validate(row.payload)``.


class V23ProjectQueueStateRow(Base):
    __tablename__ = "v23_project_queue_state"

    project_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class V23MissionQueueStateRow(Base):
    __tablename__ = "v23_mission_queue_state"

    mission_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    lifecycle: Mapped[str] = mapped_column(String(32), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class V23SchedulerReceiptRow(Base):
    __tablename__ = "v23_scheduler_receipts"
    __table_args__ = (UniqueConstraint("sequence", name="uq_v23_scheduler_receipts_sequence"),)

    receipt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sequence: Mapped[int] = mapped_column(BigInteger)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    decision: Mapped[str] = mapped_column(String(16))
    reason_code: Mapped[str] = mapped_column(String(48))
    digest: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class V23DispatchIntentRow(Base):
    __tablename__ = "v23_dispatch_intents"
    __table_args__ = (UniqueConstraint("attempt_id", name="uq_v23_dispatch_intents_attempt"),)

    intent_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(String(64))
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    state: Mapped[str] = mapped_column(String(32), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class V23SchedulerEpochRow(Base):
    __tablename__ = "v23_scheduler_epochs"

    site_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    epoch: Mapped[int] = mapped_column(BigInteger, default=0)
    holder_id: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class V23PackInstallRow(Base):
    __tablename__ = "v23_pack_installs"
    __table_args__ = (
        UniqueConstraint("pack_id", "pack_version", "project_id", name="uq_v23_pack_installs"),
    )

    install_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pack_id: Mapped[str] = mapped_column(String(128), index=True)
    pack_version: Mapped[str] = mapped_column(String(64))
    project_id: Mapped[str] = mapped_column(String(64))  # "*" = install-level record
    state: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class V23OpsEventRow(Base):
    __tablename__ = "v23_ops_events"
    __table_args__ = (Index("ix_v23_ops_events_project_at", "project_id", "at"),)

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(64), index=True)
    component: Mapped[str] = mapped_column(String(64))
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    site_epoch: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class V20GoalUsageHoldRow(Base):
    __tablename__ = "v20_goal_usage_holds"

    hold_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(64), index=True)
    mission_id: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class V20PursuitLessonRow(Base):
    __tablename__ = "v20_pursuit_lessons"

    lesson_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(64), index=True)
    state: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

### Step 5 — migration `migrations/versions/a23opsplatform0001_v23_ops_platform.py` (create, exactly)
```python
"""Alembic migration: V2.3 operations platform + V2.0 durable holds/lessons."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a23opsplatform0001"
down_revision: str | Sequence[str] | None = "a20pursuitpersist0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _jsonb() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def _ts(name: str) -> sa.Column:
    return sa.Column(
        name, sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "v23_project_queue_state",
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("project_id"),
    )
    op.create_index(
        "ix_v23_project_queue_state_tenant_id", "v23_project_queue_state", ["tenant_id"]
    )

    op.create_table(
        "v23_mission_queue_state",
        sa.Column("mission_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("lifecycle", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("mission_id"),
    )
    op.create_index(
        "ix_v23_mission_queue_state_project_id", "v23_mission_queue_state", ["project_id"]
    )
    op.create_index(
        "ix_v23_mission_queue_state_lifecycle", "v23_mission_queue_state", ["lifecycle"]
    )

    op.create_table(
        "v23_scheduler_receipts",
        sa.Column("receipt_id", sa.String(length=64), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=True),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("reason_code", sa.String(length=48), nullable=False),
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("receipt_id"),
        sa.UniqueConstraint("sequence", name="uq_v23_scheduler_receipts_sequence"),
    )
    op.create_index(
        "ix_v23_scheduler_receipts_project_id", "v23_scheduler_receipts", ["project_id"]
    )

    op.create_table(
        "v23_dispatch_intents",
        sa.Column("intent_id", sa.String(length=64), nullable=False),
        sa.Column("attempt_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("intent_id"),
        sa.UniqueConstraint("attempt_id", name="uq_v23_dispatch_intents_attempt"),
    )
    op.create_index(
        "ix_v23_dispatch_intents_project_id", "v23_dispatch_intents", ["project_id"]
    )
    op.create_index("ix_v23_dispatch_intents_state", "v23_dispatch_intents", ["state"])

    op.create_table(
        "v23_scheduler_epochs",
        sa.Column("site_id", sa.String(length=64), nullable=False),
        sa.Column("epoch", sa.BigInteger(), nullable=False),
        sa.Column("holder_id", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("site_id"),
    )

    op.create_table(
        "v23_pack_installs",
        sa.Column("install_id", sa.String(length=64), nullable=False),
        sa.Column("pack_id", sa.String(length=128), nullable=False),
        sa.Column("pack_version", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("install_id"),
        sa.UniqueConstraint(
            "pack_id", "pack_version", "project_id", name="uq_v23_pack_installs"
        ),
    )
    op.create_index("ix_v23_pack_installs_pack_id", "v23_pack_installs", ["pack_id"])

    op.create_table(
        "v23_ops_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("component", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("site_epoch", sa.BigInteger(), nullable=True),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("at"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_v23_ops_events_kind", "v23_ops_events", ["kind"])
    op.create_index("ix_v23_ops_events_trace_id", "v23_ops_events", ["trace_id"])
    op.create_index("ix_v23_ops_events_project_at", "v23_ops_events", ["project_id", "at"])

    op.create_table(
        "v20_goal_usage_holds",
        sa.Column("hold_id", sa.String(length=64), nullable=False),
        sa.Column("goal_id", sa.String(length=64), nullable=False),
        sa.Column("mission_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("hold_id"),
    )
    op.create_index("ix_v20_goal_usage_holds_goal_id", "v20_goal_usage_holds", ["goal_id"])
    op.create_index("ix_v20_goal_usage_holds_state", "v20_goal_usage_holds", ["state"])

    op.create_table(
        "v20_pursuit_lessons",
        sa.Column("lesson_id", sa.String(length=64), nullable=False),
        sa.Column("goal_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("lesson_id"),
    )
    op.create_index("ix_v20_pursuit_lessons_goal_id", "v20_pursuit_lessons", ["goal_id"])


def downgrade() -> None:
    op.drop_index("ix_v20_pursuit_lessons_goal_id", table_name="v20_pursuit_lessons")
    op.drop_table("v20_pursuit_lessons")
    op.drop_index("ix_v20_goal_usage_holds_state", table_name="v20_goal_usage_holds")
    op.drop_index("ix_v20_goal_usage_holds_goal_id", table_name="v20_goal_usage_holds")
    op.drop_table("v20_goal_usage_holds")
    op.drop_index("ix_v23_ops_events_project_at", table_name="v23_ops_events")
    op.drop_index("ix_v23_ops_events_trace_id", table_name="v23_ops_events")
    op.drop_index("ix_v23_ops_events_kind", table_name="v23_ops_events")
    op.drop_table("v23_ops_events")
    op.drop_index("ix_v23_pack_installs_pack_id", table_name="v23_pack_installs")
    op.drop_table("v23_pack_installs")
    op.drop_table("v23_scheduler_epochs")
    op.drop_index("ix_v23_dispatch_intents_state", table_name="v23_dispatch_intents")
    op.drop_index("ix_v23_dispatch_intents_project_id", table_name="v23_dispatch_intents")
    op.drop_table("v23_dispatch_intents")
    op.drop_index("ix_v23_scheduler_receipts_project_id", table_name="v23_scheduler_receipts")
    op.drop_table("v23_scheduler_receipts")
    op.drop_index("ix_v23_mission_queue_state_lifecycle", table_name="v23_mission_queue_state")
    op.drop_index("ix_v23_mission_queue_state_project_id", table_name="v23_mission_queue_state")
    op.drop_table("v23_mission_queue_state")
    op.drop_index("ix_v23_project_queue_state_tenant_id", table_name="v23_project_queue_state")
    op.drop_table("v23_project_queue_state")
```
Then check there is exactly one head:
```bash
uv run alembic heads      # expected output: a23opsplatform0001 (head)
```

### Step 6 — update the pinned head in an existing test
In `tests/integration/db/test_action_receipts_durable.py`, change **only** this line (around line 28):
```python
NEW_HEAD = "a20pursuitpersist0001"
```
to
```python
NEW_HEAD = "a23opsplatform0001"
```
(Without this, `test_single_alembic_head_after_upgrade` fails because it asserts the head name.)

### Step 7 — tests (create, exactly)
`tests/contracts/test_v23_contracts.py`:
```python
"""SW-W0-S2: V2.3 shared contract shapes (offline)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from swarm.contracts.common import utc_now
from swarm.contracts.v23 import (
    SCHEDULABLE_MISSION_STATES,
    TERMINAL_INTENT_STATES,
    TRUST_RANK,
    V23_POLICY_VERSION,
    DispatchIntent,
    DispatchIntentState,
    MissionQueueLifecycle,
    MissionQueueState,
    ProjectQueueState,
    ReasonCode,
    SchedulerDecision,
    SchedulingDecisionReceipt,
    TrustClass,
)


def test_project_state_defaults_and_validation() -> None:
    state = ProjectQueueState(project_id="proj_a")
    assert state.weight == 1.0
    assert state.credit == 0.0
    assert state.version == 0
    assert state.policy_version == V23_POLICY_VERSION
    with pytest.raises(ValidationError):
        ProjectQueueState(project_id="proj_a", weight=0)
    with pytest.raises(ValidationError):
        ProjectQueueState(project_id="proj_a", unknown_field=1)  # type: ignore[call-arg]


def test_mission_schedulable_states() -> None:
    assert MissionQueueLifecycle.QUEUED in SCHEDULABLE_MISSION_STATES
    assert MissionQueueLifecycle.PAUSED not in SCHEDULABLE_MISSION_STATES
    mission = MissionQueueState(mission_id="msn_1", project_id="proj_a")
    assert mission.lifecycle == MissionQueueLifecycle.QUEUED


def test_receipt_digest_ignores_id_and_timestamp() -> None:
    a = SchedulingDecisionReceipt(
        sequence=1,
        decision=SchedulerDecision.ADMIT,
        reason_code=ReasonCode.ADMITTED,
        project_id="proj_a",
        scores={"proj_a": 1.0},
    )
    b = a.model_copy(update={"receipt_id": "sdr_other", "created_at": utc_now()})
    assert a.digest() == b.digest()
    c = a.model_copy(update={"sequence": 2})
    assert a.digest() != c.digest()


def test_intent_terminal_states_and_trust_rank() -> None:
    intent = DispatchIntent(
        attempt_id="att_1",
        project_id="proj_a",
        mission_id="msn_1",
        task_id="tsk_1",
        expires_at=utc_now() + timedelta(seconds=30),
    )
    assert intent.state == DispatchIntentState.PREPARED
    assert DispatchIntentState.DISPATCHED not in TERMINAL_INTENT_STATES
    assert TRUST_RANK[TrustClass.OBSERVE_ONLY] < TRUST_RANK[TrustClass.INTEGRATION_WORKER]
    assert sorted(TRUST_RANK.values()) == [0, 1, 2, 3, 4]
```
`tests/controller/test_v23_store_memory.py`:
```python
"""SW-W0-S2: InMemorySchedulingStore versioning semantics (the SQL store must match)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from swarm.contracts.common import utc_now
from swarm.contracts.v23 import (
    DispatchIntent,
    DispatchIntentState,
    ProjectQueueState,
    ReasonCode,
    SchedulerDecision,
    SchedulingDecisionReceipt,
    StaleVersionError,
)
from swarm.scheduling.memory_store import InMemorySchedulingStore


def test_project_insert_update_and_stale_version() -> None:
    store = InMemorySchedulingStore()
    stored = store.put_project(ProjectQueueState(project_id="proj_a"), expected_version=None)
    assert stored.version == 1
    with pytest.raises(StaleVersionError):
        store.put_project(ProjectQueueState(project_id="proj_a"), expected_version=None)
    updated = store.put_project(stored.model_copy(update={"credit": 2.0}), expected_version=1)
    assert updated.version == 2
    with pytest.raises(StaleVersionError):
        store.put_project(stored.model_copy(update={"credit": 3.0}), expected_version=1)
    got = store.get_project("proj_a")
    assert got is not None and got.credit == 2.0


def test_receipts_sequence_unique_and_filtered() -> None:
    store = InMemorySchedulingStore()
    s1 = store.next_sequence()
    s2 = store.next_sequence()
    assert (s1, s2) == (1, 2)
    base = {"decision": SchedulerDecision.ADMIT, "reason_code": ReasonCode.ADMITTED}
    store.append_receipt(SchedulingDecisionReceipt(sequence=s1, project_id="proj_a", **base))
    store.append_receipt(SchedulingDecisionReceipt(sequence=s2, project_id="proj_b", **base))
    with pytest.raises(StaleVersionError):
        store.append_receipt(SchedulingDecisionReceipt(sequence=s1, **base))
    assert [r.project_id for r in store.list_receipts(project_id="proj_b")] == ["proj_b"]


def test_one_intent_per_attempt() -> None:
    store = InMemorySchedulingStore()
    intent = DispatchIntent(
        attempt_id="att_1",
        project_id="proj_a",
        mission_id="msn_1",
        task_id="tsk_1",
        expires_at=utc_now() + timedelta(seconds=30),
    )
    stored = store.put_intent(intent, expected_version=None)
    assert store.get_intent_by_attempt("att_1") == stored
    dup = intent.model_copy(update={"intent_id": "din_other"})
    with pytest.raises(StaleVersionError):
        store.put_intent(dup, expected_version=None)
    done = store.put_intent(
        stored.model_copy(update={"state": DispatchIntentState.COMPLETED}), expected_version=1
    )
    assert done.version == 2
    assert store.list_intents(states=frozenset({DispatchIntentState.PREPARED})) == []
```
`tests/integration/db/test_v23_schema.py`:
```python
"""SW-W0-S2: migration a23opsplatform0001 round-trip (PostgreSQL)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from swarm.db.engine import create_db_engine, ping
from swarm.db.models import Base

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[3]
DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
V23_TABLES = {
    "v23_project_queue_state",
    "v23_mission_queue_state",
    "v23_scheduler_receipts",
    "v23_dispatch_intents",
    "v23_scheduler_epochs",
    "v23_pack_installs",
    "v23_ops_events",
    "v20_goal_usage_holds",
    "v20_pursuit_lessons",
}


def _alembic_config(url: str) -> Config:
    cfg = Config(str(REPO / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


@pytest.fixture(scope="module")
def engine():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.drop_all(eng)
    with eng.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    yield eng
    Base.metadata.drop_all(eng)
    with eng.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    eng.dispose()


def test_upgrade_downgrade_upgrade(engine) -> None:
    cfg = _alembic_config(DATABASE_URL)
    command.upgrade(cfg, "head")
    names = set(inspect(engine).get_table_names())
    assert V23_TABLES <= names
    command.downgrade(cfg, "a20pursuitpersist0001")
    names = set(inspect(engine).get_table_names())
    assert not (V23_TABLES & names)
    command.upgrade(cfg, "head")
    names = set(inspect(engine).get_table_names())
    assert V23_TABLES <= names
    with engine.begin() as conn:
        head = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert head == "a23opsplatform0001"
```

### Step 8 — run the new tests first
```bash
uv run pytest tests/contracts/test_v23_contracts.py tests/controller/test_v23_store_memory.py -q    # 7 passed
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w0_s2 OWNER swarm;" || true
SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w0_s2 uv run pytest tests/integration/db/test_v23_schema.py tests/integration/db/test_action_receipts_durable.py -q -m integration
```

### Section-5 acceptance
- [ ] `uv run alembic heads` prints exactly `a23opsplatform0001 (head)`.
- [ ] `uv run python -c "import swarm.contracts.v23, swarm.scheduling.memory_store"` succeeds.
- [ ] The 7 new offline tests pass; `test_v23_schema.py` passes (upgrade → downgrade to `a20pursuitpersist0001` → upgrade).
- [ ] `models.py` diff is append-only (`git diff src/swarm/db/models.py` shows only `+` lines at the end).
- [ ] Handoff lists the 9 new table names and says: "Contracts frozen; later sessions import only. Field changes need a follow-up PR from the coordinator."

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w0_s2 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w0_s2
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/contracts/test_v23_contracts.py tests/controller/test_v23_store_memory.py -q
uv run pytest tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives tests/onboarding tests/product tests/providers tests/recovery tests/regressions tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers tests/workspace tests/e2e tests/acceptance tests/portability -q --ignore=tests/integration

# PostgreSQL integration (install steps in “PostgreSQL” below)
uv run pytest tests/integration -q -m integration

git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files
git status --porcelain            # every path listed must be one of YOUR files
```

### PostgreSQL (for the integration line)
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.
If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.

## 7. Acceptance checklist (tick every box in the handoff)
- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.
- [ ] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [ ] `uv run alembic heads` prints exactly one head.
- [ ] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [ ] Integration run passed, or SKIPPED with reason in the handoff.
- [ ] `git status --porcelain` lists only files from section 3 + the handoff.
- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [ ] The Codex review packet (section 11) is in the PR description and the handoff.

## 8. Commit, push, draft PR
```bash
git checkout -- schemas/v1 docs/evidence/fix-004 var
git add src/swarm/contracts/v23.py src/swarm/scheduling/__init__.py src/swarm/scheduling/memory_store.py src/swarm/db/models.py migrations/versions/a23opsplatform0001_v23_ops_platform.py tests/integration/db/test_action_receipts_durable.py tests/contracts/test_v23_contracts.py tests/controller/test_v23_store_memory.py tests/integration/db/test_v23_schema.py docs/v2.3/sessions/SW-W0-S2.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): shared scheduler/intent/epoch/pack/fleet/ops contracts, in-memory store, migration a23opsplatform0001" -m "Session: SW-W0-S2. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w0-s2-contracts-schema
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w0-s2-contracts-schema --title "[SW-W0-S2] V2.3 shared contracts, scheduling package, in-memory store, ORM rows, single migration a23opsplatform0001" --body-file docs/v2.3/sessions/SW-W0-S2.md
git ls-remote origin refs/heads/cursor/v23-w0-s2-contracts-schema   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W0-S2.md` with exactly these headings:
```markdown
# SW-W0-S2 handoff
- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>
- PR: <url, or compare URL>
## Done
<bullet list of what you implemented>
## Verification
<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>
## Acceptance
<copy the checkboxes from sections 5 and 7, ticked>
## Decisions
<choices you made under hard rule 8, or 'none'>
## Needs other owner
<files outside your scope that should change, with the exact change; or 'none'>
## Codex review packet
<the block from section 11, filled in>
## Status
implemented + tested (NOT accepted; needs Codex review)
```

## 10. STOP conditions (never wait for a human)
STOP immediately when any of these is true:
- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)
- **S2** a dependency check prints `MISSING`.
- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.
- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.
- **S5** finishing would require editing a file that is not in section 3.
- **S6** a required environment variable prints `MISSING`.
- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.
- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).

What to do on STOP, in this order:
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W0-S2.md` then `git commit -m "WIP(SW-W0-S2): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w0-s2-contracts-schema` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w0-s2-contracts-schema?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W0-S2
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/contracts/v23.py`, `src/swarm/scheduling/__init__.py`, `src/swarm/scheduling/memory_store.py`, `src/swarm/db/models.py`, `migrations/versions/a23opsplatform0001_v23_ops_platform.py`, `tests/integration/db/test_action_receipts_durable.py`, `tests/contracts/test_v23_contracts.py`, `tests/controller/test_v23_store_memory.py`, `tests/integration/db/test_v23_schema.py`, `docs/v2.3/sessions/SW-W0-S2.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: migration is additive only, single Alembic head; ORM rows match the migration; no data loss on downgrade path.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
