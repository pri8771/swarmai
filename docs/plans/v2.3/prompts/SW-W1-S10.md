# SW-W1-S10 — V20-E04 durable usage holds + pursuit lessons; unknown usage never frees budget (F-13)

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S10` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v20-w1-s10-durable-holds` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | SW-W0-S2 |
| Handoff file | `docs/v2.3/sessions/SW-W1-S10.md` |
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
git checkout -b cursor/v20-w1-s10-durable-holds origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W0-S2. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:migrations/versions/a23opsplatform0001_v23_ops_platform.py && echo "OK migrations/versions/a23opsplatform0001_v23_ops_platform.py" || echo "MISSING migrations/versions/a23opsplatform0001_v23_ops_platform.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/pursuit/durable_accounting.py` — create
- `src/swarm/pursuit/accounting.py` — modify
- `src/swarm/pursuit/learning.py` — modify
- `tests/pursuit/test_v20_unknown_usage_budget.py` — create
- `tests/pursuit/test_v20_durable_holds.py` — create
- `tests/integration/db/test_v20_holds_sql.py` — create
- `docs/v2.3/sessions/SW-W1-S10.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Fix finding **F-13** (financial) and implement V20-E04.

**F-13.**
- In `GoalResourceLedger`, `_held_totals` counts only `held` holds and `_settled_totals` skips `unknown` holds, so a hold settled with `usage_unknown=True` **frees its budget**.
- `release()` also accepts unknown holds.
- After this session:
  - An unknown hold keeps `max(reserved, reported)` committed.
  - `release` refuses unknown holds.
  - The only way out is `reconcile_unknown(..., evidence_ref=...)`.

**V20-E04.**
- Holds and lessons are process memory only today.
- This session adds `durable_accounting.py`, which provides:
  - `HoldStore` with in-memory and SQL implementations over `v20_goal_usage_holds`.
  - `bind_durable_ledger`, which restores holds and then persists each change **before** it becomes visible in memory. A failure rolls memory back.
  - `LessonPersistence` with in-memory and SQL implementations over `v20_pursuit_lessons`.
- `PursuitLessonStore(persistence=None)` keeps today's behaviour when no argument is given.

**Do not** wire these into `api/store.py` or `pursuit/loop.py`; SW-W3-S2 owns them.

The code below was compiled and run against `dev @ 8e1c0fde` plus SW-W0-S2. `tests/pursuit tests/goals tests/product` gives 54 passed and the integration tests give 2 passed. Paste it **exactly**.

### Step 1 — `src/swarm/pursuit/accounting.py` (replace the whole file, exactly)
```python
"""Goal-scoped usage and budget accounting (PC-06).

Tracks holds and settlements against a goal resource envelope. Unknown usage
stays unknown — never invent refunds or LiveGrant approvals. Paid spend is
denied under a zero ceiling.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from swarm.contracts.common import new_id, utc_now


class AccountingError(PermissionError):
    """Raised for envelope violations or double-settle attempts."""


HoldState = Literal["held", "settled", "released", "unknown"]


@dataclass
class UsageAmounts:
    spend_usd: float = 0.0
    model_calls: int = 0
    tool_calls: int = 0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    route_id: str | None = None
    runtime: str | None = None
    usage_unknown: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "spend_usd": self.spend_usd,
            "model_calls": self.model_calls,
            "tool_calls": self.tool_calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "route_id": self.route_id,
            "runtime": self.runtime,
            "usage_unknown": self.usage_unknown,
        }


@dataclass
class ResourceHold:
    hold_id: str
    goal_id: str
    mission_id: str
    reserved: UsageAmounts
    state: HoldState = "held"
    settled: UsageAmounts | None = None
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "hold_id": self.hold_id,
            "goal_id": self.goal_id,
            "mission_id": self.mission_id,
            "reserved": self.reserved.to_dict(),
            "state": self.state,
            "settled": self.settled.to_dict() if self.settled else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class GoalResourceLedger:
    """Parent-goal ledger: child missions reserve from remaining envelope."""

    goal_id: str
    spend_usd_ceiling: float = 0.0
    max_model_calls: int = 100
    max_tool_calls: int = 400
    allow_paid: bool = False
    holds: dict[str, ResourceHold] = field(default_factory=dict)
    on_change: Callable[[ResourceHold], None] | None = field(
        default=None, repr=False, compare=False
    )

    def _commit(self, hold: ResourceHold, prior: ResourceHold | None) -> ResourceHold:
        """Persist first (when durable); on failure restore the prior in-memory state."""
        if self.on_change is not None:
            try:
                self.on_change(hold)
            except Exception:
                if prior is None:
                    self.holds.pop(hold.hold_id, None)
                else:
                    self.holds[hold.hold_id] = prior
                raise
        self.holds[hold.hold_id] = hold
        return hold

    @classmethod
    def from_envelope(cls, goal_id: str, envelope: dict[str, Any] | None) -> GoalResourceLedger:
        env = dict(envelope or {})
        ceiling = float(env.get("spend_usd_ceiling", env.get("max_spend_usd", 0.0)) or 0.0)
        if ceiling < 0:
            ceiling = 0.0
        return cls(
            goal_id=goal_id,
            spend_usd_ceiling=ceiling,
            max_model_calls=int(env.get("max_model_calls", env.get("model_calls", 100)) or 100),
            max_tool_calls=int(env.get("max_tool_calls", env.get("tool_calls", 400)) or 400),
            allow_paid=bool(env.get("allow_paid", False)),
        )

    def _held_totals(self) -> UsageAmounts:
        """Budget still committed: open holds plus unknown-outcome holds.

        An ``unknown`` hold keeps the larger of its reservation and its reported
        usage committed until reconciled; unknown usage is never treated as zero.
        """
        spend = 0.0
        models = 0
        tools = 0
        for hold in self.holds.values():
            if hold.state == "held":
                spend += hold.reserved.spend_usd
                models += hold.reserved.model_calls
                tools += hold.reserved.tool_calls
            elif hold.state == "unknown":
                reported = hold.settled or UsageAmounts()
                spend += max(hold.reserved.spend_usd, reported.spend_usd)
                models += max(hold.reserved.model_calls, reported.model_calls)
                tools += max(hold.reserved.tool_calls, reported.tool_calls)
        return UsageAmounts(spend_usd=spend, model_calls=models, tool_calls=tools)

    def _settled_totals(self) -> UsageAmounts:
        spend = 0.0
        models = 0
        tools = 0
        unknown = False
        for hold in self.holds.values():
            if hold.state == "unknown":
                unknown = True
                continue
            if hold.state != "settled" or hold.settled is None:
                continue
            if hold.settled.usage_unknown:
                unknown = True
                continue
            spend += hold.settled.spend_usd
            models += hold.settled.model_calls
            tools += hold.settled.tool_calls
        return UsageAmounts(
            spend_usd=spend, model_calls=models, tool_calls=tools, usage_unknown=unknown
        )

    def remaining(self) -> UsageAmounts:
        held = self._held_totals()
        settled = self._settled_totals()
        return UsageAmounts(
            spend_usd=max(0.0, self.spend_usd_ceiling - held.spend_usd - settled.spend_usd),
            model_calls=max(0, self.max_model_calls - held.model_calls - settled.model_calls),
            tool_calls=max(0, self.max_tool_calls - held.tool_calls - settled.tool_calls),
            usage_unknown=settled.usage_unknown,
        )

    def reserve(
        self,
        *,
        mission_id: str,
        spend_usd: float = 0.0,
        model_calls: int = 0,
        tool_calls: int = 0,
        route_id: str | None = None,
        runtime: str | None = None,
    ) -> ResourceHold:
        spend = max(0.0, float(spend_usd))
        models = max(0, int(model_calls))
        tools = max(0, int(tool_calls))
        if spend > 0 and not self.allow_paid and self.spend_usd_ceiling <= 0:
            raise AccountingError("paid_cost_denied_under_zero_spend_budget")
        rem = self.remaining()
        if spend > rem.spend_usd + 1e-9:
            raise AccountingError("insufficient_spend_budget")
        if models > rem.model_calls:
            raise AccountingError("insufficient_model_call_budget")
        if tools > rem.tool_calls:
            raise AccountingError("insufficient_tool_call_budget")
        hold = ResourceHold(
            hold_id=new_id("hold_"),
            goal_id=self.goal_id,
            mission_id=mission_id,
            reserved=UsageAmounts(
                spend_usd=spend,
                model_calls=models,
                tool_calls=tools,
                route_id=route_id,
                runtime=runtime,
            ),
        )
        return self._commit(hold, None)

    def settle(
        self,
        hold_id: str,
        *,
        spend_usd: float = 0.0,
        model_calls: int = 0,
        tool_calls: int = 0,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        route_id: str | None = None,
        runtime: str | None = None,
        usage_unknown: bool = False,
    ) -> ResourceHold:
        hold = self.holds.get(hold_id)
        if hold is None:
            raise AccountingError(f"unknown_hold:{hold_id}")
        if hold.state == "settled":
            raise AccountingError(f"double_settle:{hold_id}")
        if hold.state == "released":
            raise AccountingError(f"settle_after_release:{hold_id}")
        if hold.state == "unknown":
            # Preserve unknown — do not invent a refund or clearance.
            raise AccountingError(f"unknown_hold_requires_reconciliation:{hold_id}")

        prior = copy.deepcopy(hold)
        spend = max(0.0, float(spend_usd))
        # Unknown usage is recorded without authorizing payment or inventing a refund.
        if usage_unknown:
            hold.state = "unknown"
            hold.settled = UsageAmounts(
                spend_usd=spend,
                model_calls=max(0, int(model_calls)),
                tool_calls=max(0, int(tool_calls)),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                route_id=route_id or hold.reserved.route_id,
                runtime=runtime or hold.reserved.runtime,
                usage_unknown=True,
            )
            hold.updated_at = utc_now().isoformat()
            return self._commit(hold, prior)

        if spend > 0 and not self.allow_paid and self.spend_usd_ceiling <= 0:
            raise AccountingError("paid_cost_denied_under_zero_spend_budget")
        # Cannot settle more spend than reserved + remaining (no silent expansion).
        rem = self.remaining()
        # Current hold is still "held", so rem already excludes it; allow up to reserved+rem.
        max_spend = hold.reserved.spend_usd + rem.spend_usd
        if spend > max_spend + 1e-9:
            raise AccountingError("settle_exceeds_envelope")

        hold.state = "settled"
        hold.settled = UsageAmounts(
            spend_usd=spend,
            model_calls=max(0, int(model_calls)),
            tool_calls=max(0, int(tool_calls)),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            route_id=route_id or hold.reserved.route_id,
            runtime=runtime or hold.reserved.runtime,
            usage_unknown=False,
        )
        hold.updated_at = utc_now().isoformat()
        return self._commit(hold, prior)

    def release(self, hold_id: str) -> ResourceHold:
        hold = self.holds.get(hold_id)
        if hold is None:
            raise AccountingError(f"unknown_hold:{hold_id}")
        if hold.state == "settled":
            raise AccountingError(f"release_after_settle:{hold_id}")
        if hold.state == "unknown":
            raise AccountingError(f"unknown_hold_requires_reconciliation:{hold_id}")
        if hold.state == "released":
            return hold
        prior = copy.deepcopy(hold)
        hold.state = "released"
        hold.updated_at = utc_now().isoformat()
        return self._commit(hold, prior)

    def reconcile_unknown(
        self,
        hold_id: str,
        *,
        spend_usd: float,
        model_calls: int,
        tool_calls: int,
        evidence_ref: str,
    ) -> ResourceHold:
        """Operator/provider reconciliation of an unknown hold to known usage."""
        hold = self.holds.get(hold_id)
        if hold is None:
            raise AccountingError(f"unknown_hold:{hold_id}")
        if hold.state != "unknown":
            raise AccountingError(f"reconcile_requires_unknown:{hold_id}")
        if not evidence_ref:
            raise AccountingError("reconcile_requires_evidence_ref")
        before = copy.deepcopy(hold)
        prior = hold.settled or UsageAmounts()
        hold.state = "settled"
        hold.settled = UsageAmounts(
            spend_usd=max(0.0, float(spend_usd)),
            model_calls=max(0, int(model_calls)),
            tool_calls=max(0, int(tool_calls)),
            prompt_tokens=prior.prompt_tokens,
            completion_tokens=prior.completion_tokens,
            route_id=prior.route_id or hold.reserved.route_id,
            runtime=prior.runtime or hold.reserved.runtime,
            usage_unknown=False,
        )
        hold.updated_at = utc_now().isoformat()
        return self._commit(hold, before)

    def snapshot(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "spend_usd_ceiling": self.spend_usd_ceiling,
            "max_model_calls": self.max_model_calls,
            "max_tool_calls": self.max_tool_calls,
            "allow_paid": self.allow_paid,
            "remaining": self.remaining().to_dict(),
            "held": self._held_totals().to_dict(),
            "settled": self._settled_totals().to_dict(),
            "holds": [h.to_dict() for h in self.holds.values()],
        }
```

### Step 2 — `src/swarm/pursuit/durable_accounting.py` (create, exactly)
```python
"""V20-E04: durable goal usage holds and pursuit lessons.

``bind_durable_ledger`` restores a ledger's holds from a ``HoldStore`` and makes
every later hold change write to the store *before* it is visible in memory.
Lesson persistence follows the same DB-first rule via ``LessonPersistence``.
"""

from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from swarm.pursuit.accounting import GoalResourceLedger, ResourceHold, UsageAmounts
from swarm.pursuit.models import PursuitLesson


class DurableAccountingError(RuntimeError):
    pass


def _amounts(d: dict[str, Any] | None) -> UsageAmounts | None:
    if d is None:
        return None
    return UsageAmounts(
        spend_usd=float(d.get("spend_usd") or 0.0),
        model_calls=int(d.get("model_calls") or 0),
        tool_calls=int(d.get("tool_calls") or 0),
        prompt_tokens=d.get("prompt_tokens"),
        completion_tokens=d.get("completion_tokens"),
        route_id=d.get("route_id"),
        runtime=d.get("runtime"),
        usage_unknown=bool(d.get("usage_unknown", False)),
    )


def hold_from_dict(d: dict[str, Any]) -> ResourceHold:
    reserved = _amounts(d.get("reserved")) or UsageAmounts()
    return ResourceHold(
        hold_id=str(d["hold_id"]),
        goal_id=str(d["goal_id"]),
        mission_id=str(d["mission_id"]),
        reserved=reserved,
        state=d["state"],
        settled=_amounts(d.get("settled")),
        created_at=str(d["created_at"]),
        updated_at=str(d["updated_at"]),
    )


class HoldStore(Protocol):
    def put(self, hold: ResourceHold) -> None: ...

    def list_for_goal(self, goal_id: str) -> list[ResourceHold]: ...


class InMemoryHoldStore:
    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}

    def put(self, hold: ResourceHold) -> None:
        self._rows[hold.hold_id] = hold.to_dict()

    def list_for_goal(self, goal_id: str) -> list[ResourceHold]:
        rows = [r for r in self._rows.values() if r["goal_id"] == goal_id]
        rows.sort(key=lambda r: (r["created_at"], r["hold_id"]))
        return [hold_from_dict(r) for r in rows]


class SqlHoldStore:
    """PostgreSQL ``v20_goal_usage_holds``; one transaction per change."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    def put(self, hold: ResourceHold) -> None:
        from swarm.db.engine import session_scope
        from swarm.db.models import V20GoalUsageHoldRow

        try:
            with session_scope(self._factory) as s:
                row = s.get(V20GoalUsageHoldRow, hold.hold_id, with_for_update=True)
                if row is None:
                    s.add(
                        V20GoalUsageHoldRow(
                            hold_id=hold.hold_id,
                            goal_id=hold.goal_id,
                            mission_id=hold.mission_id,
                            state=hold.state,
                            version=1,
                            payload=hold.to_dict(),
                        )
                    )
                else:
                    row.state = hold.state
                    row.version = row.version + 1
                    row.payload = hold.to_dict()
        except Exception as exc:  # noqa: BLE001 - fail closed on any DB error
            raise DurableAccountingError(f"hold_persist_failed:{type(exc).__name__}") from exc

    def list_for_goal(self, goal_id: str) -> list[ResourceHold]:
        from swarm.db.engine import session_scope
        from swarm.db.models import V20GoalUsageHoldRow

        stmt = select(V20GoalUsageHoldRow).where(V20GoalUsageHoldRow.goal_id == goal_id)
        try:
            with session_scope(self._factory) as s:
                payloads = [dict(r.payload) for r in s.execute(stmt).scalars()]
        except Exception as exc:  # noqa: BLE001
            raise DurableAccountingError(f"hold_load_failed:{type(exc).__name__}") from exc
        payloads.sort(key=lambda r: (r["created_at"], r["hold_id"]))
        return [hold_from_dict(p) for p in payloads]


def bind_durable_ledger(ledger: GoalResourceLedger, store: HoldStore) -> GoalResourceLedger:
    """Restore holds for ``ledger.goal_id`` and persist every later change first."""
    ledger.holds = {h.hold_id: h for h in store.list_for_goal(ledger.goal_id)}
    ledger.on_change = store.put
    return ledger


class LessonPersistence(Protocol):
    def put(self, lesson: PursuitLesson) -> None: ...

    def load_all(self) -> list[PursuitLesson]: ...


class InMemoryLessonPersistence:
    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}

    def put(self, lesson: PursuitLesson) -> None:
        self._rows[lesson.lesson_id] = lesson.model_dump(mode="json")

    def load_all(self) -> list[PursuitLesson]:
        rows = sorted(self._rows.values(), key=lambda r: (r["created_at"], r["lesson_id"]))
        return [PursuitLesson.model_validate(r) for r in rows]


class SqlLessonPersistence:
    """PostgreSQL ``v20_pursuit_lessons``."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    def put(self, lesson: PursuitLesson) -> None:
        from swarm.db.engine import session_scope
        from swarm.db.models import V20PursuitLessonRow

        payload = lesson.model_dump(mode="json")
        try:
            with session_scope(self._factory) as s:
                row = s.get(V20PursuitLessonRow, lesson.lesson_id, with_for_update=True)
                if row is None:
                    s.add(
                        V20PursuitLessonRow(
                            lesson_id=lesson.lesson_id,
                            goal_id=lesson.goal_id,
                            state=lesson.state.value,
                            payload=payload,
                        )
                    )
                else:
                    row.state = lesson.state.value
                    row.payload = payload
        except Exception as exc:  # noqa: BLE001
            raise DurableAccountingError(f"lesson_persist_failed:{type(exc).__name__}") from exc

    def load_all(self) -> list[PursuitLesson]:
        from swarm.db.engine import session_scope
        from swarm.db.models import V20PursuitLessonRow

        try:
            with session_scope(self._factory) as s:
                rows = s.execute(select(V20PursuitLessonRow)).scalars()
                payloads = [dict(r.payload) for r in rows]
        except Exception as exc:  # noqa: BLE001
            raise DurableAccountingError(f"lesson_load_failed:{type(exc).__name__}") from exc
        payloads.sort(key=lambda r: (r["created_at"], r["lesson_id"]))
        return [PursuitLesson.model_validate(p) for p in payloads]
```

### Step 3 — `src/swarm/pursuit/learning.py` (replace the whole file, exactly)
```python
"""Evaluated pursuit lessons — adopt affects behavior; rollback restores strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from swarm.contracts.common import utc_now
from swarm.pursuit.models import LessonState, PursuitLesson

if TYPE_CHECKING:
    from swarm.pursuit.durable_accounting import LessonPersistence


class PursuitLearningError(RuntimeError):
    pass


_TRANSITIONS: dict[LessonState, set[LessonState]] = {
    LessonState.CANDIDATE: {LessonState.EVALUATED, LessonState.REJECTED},
    LessonState.EVALUATED: {LessonState.ADOPTED, LessonState.REJECTED},
    LessonState.ADOPTED: {LessonState.ROLLED_BACK},
    LessonState.ROLLED_BACK: set(),
    LessonState.REJECTED: set(),
}


class PursuitLessonStore:
    def __init__(self, persistence: LessonPersistence | None = None) -> None:
        self._lessons: dict[str, PursuitLesson] = {}
        self._by_goal: dict[str, list[str]] = {}
        self._persistence = persistence
        if persistence is not None:
            for lesson in persistence.load_all():
                self._lessons[lesson.lesson_id] = lesson
                self._by_goal.setdefault(lesson.goal_id, []).append(lesson.lesson_id)

    def _store(self, lesson: PursuitLesson) -> PursuitLesson:
        """Durable first: a persistence failure leaves memory unchanged."""
        if self._persistence is not None:
            self._persistence.put(lesson)
        self._lessons[lesson.lesson_id] = lesson
        return lesson

    def propose(self, lesson: PursuitLesson) -> PursuitLesson:
        self._store(lesson)
        self._by_goal.setdefault(lesson.goal_id, []).append(lesson.lesson_id)
        return lesson

    def get(self, lesson_id: str) -> PursuitLesson:
        if lesson_id not in self._lessons:
            raise PursuitLearningError("lesson_missing")
        return self._lessons[lesson_id]

    def list_for_goal(self, goal_id: str) -> list[PursuitLesson]:
        return [self._lessons[i] for i in self._by_goal.get(goal_id, []) if i in self._lessons]

    def adopted_for_goal(self, goal_id: str) -> list[PursuitLesson]:
        return [
            lesson for lesson in self.list_for_goal(goal_id) if lesson.state == LessonState.ADOPTED
        ]

    def evaluate(
        self,
        lesson_id: str,
        *,
        holdout_check_id: str,
        holdout_passed: bool,
    ) -> PursuitLesson:
        lesson = self.get(lesson_id)
        if lesson.state != LessonState.CANDIDATE:
            raise PursuitLearningError(f"evaluate_illegal_from:{lesson.state.value}")
        if not holdout_check_id:
            raise PursuitLearningError("holdout_required")
        if "answer=" in holdout_check_id:
            raise PursuitLearningError("holdout_plaintext_forbidden")
        updated = lesson.model_copy(
            update={
                "holdout_check_id": holdout_check_id,
                "holdout_passed": holdout_passed,
                "state": LessonState.EVALUATED if holdout_passed else LessonState.REJECTED,
                "updated_at": utc_now().isoformat(),
            }
        )
        return self._store(updated)

    def adopt(self, lesson_id: str, *, current_strategy: str) -> PursuitLesson:
        lesson = self.get(lesson_id)
        if lesson.state != LessonState.EVALUATED:
            raise PursuitLearningError(f"adopt_illegal_from:{lesson.state.value}")
        if lesson.holdout_passed is not True:
            raise PursuitLearningError("holdout_not_passed")
        updated = lesson.model_copy(
            update={
                "state": LessonState.ADOPTED,
                "prior_strategy": current_strategy,
                "updated_at": utc_now().isoformat(),
            }
        )
        return self._store(updated)

    def rollback(self, lesson_id: str) -> PursuitLesson:
        lesson = self.get(lesson_id)
        if lesson.state != LessonState.ADOPTED:
            raise PursuitLearningError(f"rollback_illegal_from:{lesson.state.value}")
        updated = lesson.model_copy(
            update={"state": LessonState.ROLLED_BACK, "updated_at": utc_now().isoformat()}
        )
        return self._store(updated)

    def applied_strategy(self, goal_id: str, base_strategy: str) -> str:
        adopted = self.adopted_for_goal(goal_id)
        if not adopted:
            return base_strategy
        deltas = [lesson.strategy_delta for lesson in adopted if lesson.strategy_delta]
        if not deltas:
            return base_strategy
        return (base_strategy + " | " + " | ".join(deltas)).strip(" |")
```

### Step 4 — `tests/pursuit/test_v20_unknown_usage_budget.py` (create, exactly)
```python
"""SW-W1-S10 / F-13: unknown usage keeps budget committed until reconciled."""

from __future__ import annotations

import pytest

from swarm.pursuit import AccountingError, GoalResourceLedger


def _ledger() -> GoalResourceLedger:
    return GoalResourceLedger.from_envelope(
        "goal_u", {"spend_usd_ceiling": 1.0, "allow_paid": True, "max_model_calls": 3}
    )


def test_unknown_hold_still_counts_against_remaining() -> None:
    ledger = _ledger()
    hold = ledger.reserve(mission_id="msn_1", spend_usd=0.6, model_calls=2)
    ledger.settle(hold.hold_id, spend_usd=0.1, model_calls=1, usage_unknown=True)
    remaining = ledger.remaining()
    assert remaining.spend_usd == pytest.approx(0.4)
    assert remaining.model_calls == 1
    with pytest.raises(AccountingError, match="insufficient_spend_budget"):
        ledger.reserve(mission_id="msn_2", spend_usd=0.5)


def test_unknown_hold_uses_larger_of_reserved_and_reported() -> None:
    ledger = _ledger()
    hold = ledger.reserve(mission_id="msn_1", spend_usd=0.2, model_calls=1)
    ledger.settle(hold.hold_id, spend_usd=0.7, model_calls=1, usage_unknown=True)
    assert ledger.remaining().spend_usd == pytest.approx(0.3)


def test_unknown_hold_cannot_be_released() -> None:
    ledger = _ledger()
    hold = ledger.reserve(mission_id="msn_1", spend_usd=0.5, model_calls=1)
    ledger.settle(hold.hold_id, spend_usd=0.5, model_calls=1, usage_unknown=True)
    with pytest.raises(AccountingError, match="unknown_hold_requires_reconciliation"):
        ledger.release(hold.hold_id)


def test_reconcile_unknown_requires_evidence_and_settles() -> None:
    ledger = _ledger()
    hold = ledger.reserve(mission_id="msn_1", spend_usd=0.5, model_calls=1)
    ledger.settle(hold.hold_id, spend_usd=0.5, model_calls=1, usage_unknown=True)
    with pytest.raises(AccountingError, match="reconcile_requires_evidence_ref"):
        ledger.reconcile_unknown(
            hold.hold_id, spend_usd=0.2, model_calls=1, tool_calls=0, evidence_ref=""
        )
    ledger.reconcile_unknown(
        hold.hold_id, spend_usd=0.2, model_calls=1, tool_calls=0, evidence_ref="usage:rq_1"
    )
    assert ledger.holds[hold.hold_id].state == "settled"
    assert ledger.remaining().spend_usd == pytest.approx(0.8)
    assert ledger.remaining().usage_unknown is False
```

### Step 5 — `tests/pursuit/test_v20_durable_holds.py` (create, exactly)
```python
"""SW-W1-S10 / V20-E04: holds and lessons survive restart; persistence is DB-first."""

from __future__ import annotations

import pytest

from swarm.pursuit import AccountingError, GoalResourceLedger
from swarm.pursuit.accounting import ResourceHold
from swarm.pursuit.durable_accounting import (
    InMemoryHoldStore,
    InMemoryLessonPersistence,
    bind_durable_ledger,
)
from swarm.pursuit.learning import PursuitLessonStore
from swarm.pursuit.models import LessonState, PursuitLesson

ENV = {"spend_usd_ceiling": 1.0, "allow_paid": True, "max_model_calls": 5}


def _ledger(store: InMemoryHoldStore) -> GoalResourceLedger:
    return bind_durable_ledger(GoalResourceLedger.from_envelope("goal_d", ENV), store)


def test_holds_survive_restart_including_unknown() -> None:
    store = InMemoryHoldStore()
    first = _ledger(store)
    a = first.reserve(mission_id="msn_a", spend_usd=0.3, model_calls=1)
    b = first.reserve(mission_id="msn_b", spend_usd=0.2, model_calls=1)
    first.settle(a.hold_id, spend_usd=0.1, model_calls=1)
    first.settle(b.hold_id, spend_usd=0.0, usage_unknown=True)

    cold = _ledger(store)
    assert {h.hold_id: h.state for h in cold.holds.values()} == {
        a.hold_id: "settled",
        b.hold_id: "unknown",
    }
    assert cold.remaining().spend_usd == pytest.approx(first.remaining().spend_usd)
    with pytest.raises(AccountingError, match="double_settle"):
        cold.settle(a.hold_id, spend_usd=0.1)
    with pytest.raises(AccountingError, match="unknown_hold_requires_reconciliation"):
        cold.release(b.hold_id)


class _FailingStore(InMemoryHoldStore):
    def __init__(self) -> None:
        super().__init__()
        self.fail = False

    def put(self, hold: ResourceHold) -> None:
        if self.fail:
            raise RuntimeError("db_down")
        super().put(hold)


def test_persist_failure_leaves_memory_unchanged() -> None:
    store = _FailingStore()
    ledger = _ledger(store)
    hold = ledger.reserve(mission_id="msn_a", spend_usd=0.3)
    store.fail = True
    with pytest.raises(RuntimeError, match="db_down"):
        ledger.reserve(mission_id="msn_b", spend_usd=0.1)
    assert len(ledger.holds) == 1
    with pytest.raises(RuntimeError, match="db_down"):
        ledger.settle(hold.hold_id, spend_usd=0.2)
    assert ledger.holds[hold.hold_id].state == "held"


def test_lessons_survive_restart() -> None:
    persist = InMemoryLessonPersistence()
    store = PursuitLessonStore(persist)
    lesson = store.propose(PursuitLesson(goal_id="goal_l", summary="s", strategy_delta="d"))
    store.evaluate(lesson.lesson_id, holdout_check_id="hold:1", holdout_passed=True)
    store.adopt(lesson.lesson_id, current_strategy="base")

    cold = PursuitLessonStore(persist)
    assert cold.get(lesson.lesson_id).state == LessonState.ADOPTED
    assert cold.applied_strategy("goal_l", "base") == "base | d"
    cold.rollback(lesson.lesson_id)
    assert PursuitLessonStore(persist).get(lesson.lesson_id).state == LessonState.ROLLED_BACK


def test_store_without_persistence_is_unchanged() -> None:
    store = PursuitLessonStore()
    lesson = store.propose(PursuitLesson(goal_id="g", summary="s"))
    assert store.list_for_goal("g") == [lesson]
```

### Step 6 — `tests/integration/db/test_v20_holds_sql.py` (create, exactly)
```python
"""SW-W1-S10 / V20-E04: usage holds and lessons persisted in PostgreSQL."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base
from swarm.pursuit import GoalResourceLedger
from swarm.pursuit.durable_accounting import (
    SqlHoldStore,
    SqlLessonPersistence,
    bind_durable_ledger,
)
from swarm.pursuit.learning import PursuitLessonStore
from swarm.pursuit.models import LessonState, PursuitLesson

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)


@pytest.fixture(scope="module")
def factory():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE v20_goal_usage_holds, v20_pursuit_lessons"))
    yield make_session_factory(eng)
    eng.dispose()


def test_holds_restore_from_postgres(factory) -> None:
    env = {"spend_usd_ceiling": 1.0, "allow_paid": True}
    first = bind_durable_ledger(GoalResourceLedger.from_envelope("goal_sql", env), SqlHoldStore(factory))
    hold = first.reserve(mission_id="msn_1", spend_usd=0.4)
    first.settle(hold.hold_id, spend_usd=0.0, usage_unknown=True)

    cold = bind_durable_ledger(GoalResourceLedger.from_envelope("goal_sql", env), SqlHoldStore(factory))
    assert cold.holds[hold.hold_id].state == "unknown"
    assert cold.remaining().spend_usd == pytest.approx(0.6)
    with factory() as s:
        version = s.execute(
            text("SELECT version FROM v20_goal_usage_holds WHERE hold_id = :h"), {"h": hold.hold_id}
        ).scalar_one()
    assert version == 2


def test_lessons_restore_from_postgres(factory) -> None:
    store = PursuitLessonStore(SqlLessonPersistence(factory))
    lesson = store.propose(PursuitLesson(goal_id="goal_sql", summary="s"))
    store.evaluate(lesson.lesson_id, holdout_check_id="hold:1", holdout_passed=False)
    cold = PursuitLessonStore(SqlLessonPersistence(factory))
    assert cold.get(lesson.lesson_id).state == LessonState.REJECTED
```

### Step 7 — run
```bash
uv run pytest tests/pursuit -q                      # all pass (existing tests/pursuit/test_usage_accounting.py unchanged)
uv run pytest tests/goals tests/product tests/api -q
```
If an existing test expects `release()` of an unknown hold to succeed, or expects remaining budget to grow after an unknown settle, **stop**. That test encodes F-13; STOP (S4, section 10) and name the test. Do not edit it.

### Section-5 acceptance
- [ ] After an unknown settle, `remaining()` still subtracts `max(reserved, reported)`, and a reserve that needs the freed amount fails with `insufficient_spend_budget`.
- [ ] `release()` of an unknown hold raises `unknown_hold_requires_reconciliation`; `reconcile_unknown` requires a non-empty `evidence_ref`.
- [ ] Holds, including unknown holds, and lessons survive a cold restart through the store (both in-memory and PostgreSQL).
- [ ] A persistence failure leaves in-memory ledger and lesson state unchanged, and the error propagates.
- [ ] With no store or persistence, behaviour is unchanged apart from the F-13 fix.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s10 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s10
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/pursuit -q
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
git add src/swarm/pursuit/durable_accounting.py src/swarm/pursuit/accounting.py src/swarm/pursuit/learning.py tests/pursuit/test_v20_unknown_usage_budget.py tests/pursuit/test_v20_durable_holds.py tests/integration/db/test_v20_holds_sql.py docs/v2.3/sessions/SW-W1-S10.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "fix(v2.0): unknown usage keeps budget committed (F-13); feat: E04 durable holds and lessons stores" -m "Session: SW-W1-S10. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v20-w1-s10-durable-holds
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v20-w1-s10-durable-holds --title "[SW-W1-S10] V20-E04 durable usage holds + pursuit lessons; unknown usage never frees budget (F-13)" --body-file docs/v2.3/sessions/SW-W1-S10.md
git ls-remote origin refs/heads/cursor/v20-w1-s10-durable-holds   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S10.md` with exactly these headings:
```markdown
# SW-W1-S10 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S10.md` then `git commit -m "WIP(SW-W1-S10): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v20-w1-s10-durable-holds` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v20-w1-s10-durable-holds?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S10
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/pursuit/durable_accounting.py`, `src/swarm/pursuit/accounting.py`, `src/swarm/pursuit/learning.py`, `tests/pursuit/test_v20_unknown_usage_budget.py`, `tests/pursuit/test_v20_durable_holds.py`, `tests/integration/db/test_v20_holds_sql.py`, `docs/v2.3/sessions/SW-W1-S10.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: unknown usage keeps budget committed (F-13); holds survive restart.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
