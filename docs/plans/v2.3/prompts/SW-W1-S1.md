# SW-W1-S1 — Weighted-deficit round-robin selector (pure, deterministic)

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S1` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w1-s1-wdrr` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | SW-W0-S1, SW-W0-S2 |
| Handoff file | `docs/v2.3/sessions/SW-W1-S1.md` |
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
git checkout -b cursor/v23-w1-s1-wdrr origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W0-S1, SW-W0-S2. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/contracts/v23.py && echo "OK src/swarm/contracts/v23.py" || echo "MISSING src/swarm/contracts/v23.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:config/v23/scheduler_policy.v1.json && echo "OK config/v23/scheduler_policy.v1.json" || echo "MISSING config/v23/scheduler_policy.v1.json"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/scheduling/wdrr.py` — create
- `tests/controller/test_v23_wdrr.py` — create
- `docs/v2.3/sessions/SW-W1-S1.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Implement the V2.3 fairness selector: weighted deficit round robin (WDRR), project level first, then mission level, then task order. It is a **pure function**: no I/O, no clock reads (`now` is passed in), no mutation of inputs. SW-W2-S1 wraps it with persistence.

**Rules it implements** (from `docs/artifacts/future/ART-V23-MULTIMISSION_SCHEDULER.md` and `config/v23/scheduler_policy.v1.json`):
- For each decision, every *eligible* project accrues `base_quantum * weight`, capped at `max_credit_cap_multiplier * weight * base_quantum`. The chosen project pays `service_cost * base_quantum * total_eligible_weight`. Long-run share is therefore proportional to weight.
- Ineligible projects (paused, at the concurrency cap, or with only blocked work) neither accrue nor pay. Blocked work never earns credit.
- Urgent, aging and deadline bonuses add to the **score only**, never to credit, and are capped at `urgent_borrow_cap * base_quantum`.
- Tie-break: `(-score, last_served_seq, id)`. Tasks inside a mission are ordered by `(-priority, enqueued_at, task_id)`.
- On restart, only positive credit is clamped (to `restart_credit_cap_multiplier * weight * base_quantum`); debt is kept.

The code and tests below were compiled and run against `dev + SW-W0-S1 + SW-W0-S2` (15 passed; ruff and mypy clean). Paste them **exactly**.

### Step 1 — `src/swarm/scheduling/wdrr.py` (create, exactly)
```python
"""Weighted deficit round-robin selector (ART-V23-SCHEDULER, policy v23-wdrr-1).

Pure and deterministic: no I/O, no clocks (``now`` is injected), inputs are never
mutated. Two levels: project first, then mission inside the chosen project, then
the task inside the chosen mission.

Credit accounting per decision (project level; mission level is identical inside
the chosen project):

* every *eligible* project accrues ``base_quantum * weight``, capped at
  ``max_credit_cap_multiplier * weight * base_quantum``;
* the chosen project is charged ``service_cost * base_quantum * total_eligible_weight``;
* ineligible projects (paused, at cap, blocked work only) neither accrue nor pay.

Long-run admitted share is therefore proportional to weight. Urgency, aging and
deadline bonuses change the *score* only (bounded by ``urgent_borrow_cap``), never
the credit, so they cannot amplify long-run share.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from swarm.contracts.common import payload_hash
from swarm.contracts.v23 import (
    SCHEDULABLE_MISSION_STATES,
    V23_POLICY_VERSION,
    MissionQueueLifecycle,
    MissionQueueState,
    PriorityClass,
    ProjectQueueState,
    ReasonCode,
    SchedulableTask,
    SchedulerDecision,
)

ResourceCheck = Callable[[SchedulableTask], bool]


@dataclass(frozen=True)
class WdrrConfig:
    policy_version: str = V23_POLICY_VERSION
    base_quantum: float = 1.0
    max_credit_cap_multiplier: float = 10.0
    urgent_borrow_cap: float = 2.0
    aging_floor_ms: int = 60_000
    aging_bonus: float = 0.5
    deadline_bonus_cap: float = 1.0
    deadline_slack_ms: int = 300_000
    restart_credit_cap_multiplier: float = 10.0

    @classmethod
    def from_policy_file(cls, path: Path) -> WdrrConfig:
        data = json.loads(path.read_text(encoding="utf-8"))
        wdrr: dict[str, Any] = data["wdrr"]
        return cls(
            policy_version=str(data["policy_version"]),
            base_quantum=float(wdrr["base_quantum"]),
            max_credit_cap_multiplier=float(wdrr["max_credit_cap_multiplier"]),
            urgent_borrow_cap=float(wdrr["urgent_borrow_cap"]),
            aging_floor_ms=int(wdrr["aging_floor_ms"]),
            aging_bonus=float(wdrr["aging_bonus"]),
            deadline_bonus_cap=float(wdrr["deadline_bonus_cap"]),
            deadline_slack_ms=int(wdrr["deadline_slack_ms"]),
            restart_credit_cap_multiplier=float(wdrr["restart_credit_cap_multiplier"]),
        )


@dataclass(frozen=True)
class Selection:
    decision: SchedulerDecision
    reason_code: ReasonCode
    project_id: str | None = None
    mission_id: str | None = None
    task: SchedulableTask | None = None
    scores: dict[str, float] = field(default_factory=dict)
    credits_before: dict[str, float] = field(default_factory=dict)
    credits_after: dict[str, float] = field(default_factory=dict)
    mission_credits_after: dict[str, float] = field(default_factory=dict)
    candidate_set_hash: str = ""
    blocked: dict[str, str] = field(default_factory=dict)


def _cap(weight: float, config: WdrrConfig) -> float:
    return config.max_credit_cap_multiplier * weight * config.base_quantum


def _eligible_tasks_by_mission(
    missions: Sequence[MissionQueueState],
    tasks: Sequence[SchedulableTask],
    resource_available: ResourceCheck | None,
    blocked: dict[str, str],
) -> dict[str, list[SchedulableTask]]:
    mission_by_id = {m.mission_id: m for m in missions}
    out: dict[str, list[SchedulableTask]] = {}
    for task in sorted(tasks, key=lambda t: t.task_id):
        mission = mission_by_id.get(task.mission_id)
        if mission is None or mission.project_id != task.project_id:
            blocked[task.task_id] = ReasonCode.ISOLATION_DENIED.value
            continue
        if mission.lifecycle not in SCHEDULABLE_MISSION_STATES:
            reason = (
                ReasonCode.DRAINING
                if mission.lifecycle == MissionQueueLifecycle.DRAINING
                else ReasonCode.NO_ELIGIBLE_WORK
            )
            blocked[task.task_id] = reason.value
            continue
        if task.cancellation_generation != mission.cancellation_generation:
            blocked[task.task_id] = ReasonCode.CANCELLED_GENERATION.value
            continue
        if not task.dependencies_ready:
            blocked[task.task_id] = ReasonCode.NO_ELIGIBLE_WORK.value
            continue
        if mission.running >= mission.max_parallelism:
            blocked[task.task_id] = ReasonCode.MISSION_PARALLELISM_CAP.value
            continue
        if resource_available is not None and not resource_available(task):
            blocked[task.task_id] = ReasonCode.DEFERRED_RESOURCE_UNAVAILABLE.value
            continue
        out.setdefault(task.mission_id, []).append(task)
    return out


def _bonus(
    missions: Sequence[MissionQueueState],
    tasks: Sequence[SchedulableTask],
    *,
    now: datetime,
    config: WdrrConfig,
) -> float:
    urgent = 1.0 if any(m.priority == PriorityClass.URGENT for m in missions) else 0.0
    aging = 0.0
    if tasks and config.aging_floor_ms > 0:
        oldest = min(t.enqueued_at for t in tasks)
        waited_ms = max(0.0, (now - oldest).total_seconds() * 1000.0)
        aging = config.aging_bonus * float(int(waited_ms // config.aging_floor_ms))
    deadline = 0.0
    for m in missions:
        if m.deadline_at is None:
            continue
        slack_ms = (m.deadline_at - now).total_seconds() * 1000.0
        if slack_ms <= config.deadline_slack_ms:
            deadline = config.deadline_bonus_cap
    return min(config.urgent_borrow_cap, urgent + aging + deadline) * config.base_quantum


def candidate_set_hash(
    projects: Sequence[ProjectQueueState],
    missions: Sequence[MissionQueueState],
    tasks: Sequence[SchedulableTask],
) -> str:
    body = {
        "projects": sorted(
            [p.project_id, p.version, round(p.credit, 9), p.paused, p.running] for p in projects
        ),
        "missions": sorted(
            [m.mission_id, m.version, round(m.credit, 9), m.lifecycle.value, m.running]
            for m in missions
        ),
        "tasks": sorted(
            [t.task_id, t.attempt_id, t.dependencies_ready, t.cancellation_generation]
            for t in tasks
        ),
    }
    return payload_hash(body)


def _pick(
    ids: list[str],
    *,
    credit_after_accrual: dict[str, float],
    bonus: dict[str, float],
    last_served: dict[str, int],
) -> tuple[str, dict[str, float]]:
    scores = {i: credit_after_accrual[i] + bonus[i] for i in ids}
    chosen = min(ids, key=lambda i: (-scores[i], last_served[i], i))
    return chosen, scores


def select_next(
    projects: Sequence[ProjectQueueState],
    missions: Sequence[MissionQueueState],
    tasks: Sequence[SchedulableTask],
    *,
    now: datetime,
    config: WdrrConfig | None = None,
    resource_available: ResourceCheck | None = None,
) -> Selection:
    cfg = config or WdrrConfig()
    cset = candidate_set_hash(projects, missions, tasks)
    credits_before = {p.project_id: p.credit for p in projects}
    blocked: dict[str, str] = {}

    by_mission = _eligible_tasks_by_mission(missions, tasks, resource_available, blocked)
    missions_by_project: dict[str, list[MissionQueueState]] = {}
    for m in missions:
        if m.mission_id in by_mission:
            missions_by_project.setdefault(m.project_id, []).append(m)

    eligible: list[ProjectQueueState] = []
    for p in sorted(projects, key=lambda x: x.project_id):
        if p.paused:
            blocked[p.project_id] = ReasonCode.DRAINING.value
            continue
        if p.running >= p.max_concurrency:
            blocked[p.project_id] = ReasonCode.PROJECT_CONCURRENCY_CAP.value
            continue
        if p.project_id not in missions_by_project:
            continue
        eligible.append(p)

    if not eligible:
        reason = ReasonCode.NO_ELIGIBLE_WORK
        decision = SchedulerDecision.IDLE
        priority = [
            ReasonCode.DEFERRED_RESOURCE_UNAVAILABLE,
            ReasonCode.PROJECT_CONCURRENCY_CAP,
            ReasonCode.MISSION_PARALLELISM_CAP,
        ]
        for code in priority:
            if code.value in blocked.values():
                reason = code
                decision = SchedulerDecision.DEFER
                break
        return Selection(
            decision=decision,
            reason_code=reason,
            credits_before=credits_before,
            credits_after=dict(credits_before),
            candidate_set_hash=cset,
            blocked=blocked,
        )

    q = cfg.base_quantum
    accrued = {
        p.project_id: min(p.credit + q * p.weight, _cap(p.weight, cfg)) for p in eligible
    }
    p_bonus = {
        p.project_id: _bonus(
            missions_by_project[p.project_id],
            [t for m in missions_by_project[p.project_id] for t in by_mission[m.mission_id]],
            now=now,
            config=cfg,
        )
        for p in eligible
    }
    project_id, scores = _pick(
        [p.project_id for p in eligible],
        credit_after_accrual=accrued,
        bonus=p_bonus,
        last_served={p.project_id: p.last_served_seq for p in eligible},
    )

    chosen_missions = sorted(missions_by_project[project_id], key=lambda m: m.mission_id)
    m_accrued = {
        m.mission_id: min(m.credit + q * m.weight, _cap(m.weight, cfg)) for m in chosen_missions
    }
    m_bonus = {
        m.mission_id: _bonus([m], by_mission[m.mission_id], now=now, config=cfg)
        for m in chosen_missions
    }
    mission_id, _m_scores = _pick(
        [m.mission_id for m in chosen_missions],
        credit_after_accrual=m_accrued,
        bonus=m_bonus,
        last_served={m.mission_id: m.last_served_seq for m in chosen_missions},
    )
    task = min(
        by_mission[mission_id], key=lambda t: (-t.priority, t.enqueued_at, t.task_id)
    )

    total_w = sum(p.weight for p in eligible)
    credits_after = dict(credits_before)
    credits_after.update(accrued)
    credits_after[project_id] = accrued[project_id] - task.service_cost * q * total_w

    total_mw = sum(m.weight for m in chosen_missions)
    mission_credits_after = {m.mission_id: m.credit for m in missions}
    mission_credits_after.update(m_accrued)
    mission_credits_after[mission_id] = m_accrued[mission_id] - task.service_cost * q * total_mw

    return Selection(
        decision=SchedulerDecision.ADMIT,
        reason_code=ReasonCode.ADMITTED,
        project_id=project_id,
        mission_id=mission_id,
        task=task,
        scores=scores,
        credits_before=credits_before,
        credits_after=credits_after,
        mission_credits_after=mission_credits_after,
        candidate_set_hash=cset,
        blocked=blocked,
    )


def apply_selection(
    projects: Sequence[ProjectQueueState],
    missions: Sequence[MissionQueueState],
    selection: Selection,
    *,
    sequence: int,
) -> tuple[list[ProjectQueueState], list[MissionQueueState]]:
    """Return updated copies (credits, running counts, last_served_seq). Inputs untouched."""
    if selection.decision != SchedulerDecision.ADMIT:
        return [p.model_copy() for p in projects], [m.model_copy() for m in missions]
    new_projects: list[ProjectQueueState] = []
    for p in projects:
        update: dict[str, Any] = {"credit": selection.credits_after.get(p.project_id, p.credit)}
        if p.project_id == selection.project_id:
            update["running"] = p.running + 1
            update["last_served_seq"] = sequence
        new_projects.append(p.model_copy(update=update))
    new_missions: list[MissionQueueState] = []
    for m in missions:
        update = {"credit": selection.mission_credits_after.get(m.mission_id, m.credit)}
        if m.mission_id == selection.mission_id:
            update["running"] = m.running + 1
            update["last_served_seq"] = sequence
            update["lifecycle"] = MissionQueueLifecycle.RUNNING
        new_missions.append(m.model_copy(update=update))
    return new_projects, new_missions


def clamp_restart_credit(
    projects: Sequence[ProjectQueueState], config: WdrrConfig | None = None
) -> list[ProjectQueueState]:
    """After restart, clamp only the positive side of credit (debt is preserved)."""
    cfg = config or WdrrConfig()
    out: list[ProjectQueueState] = []
    for p in projects:
        cap = cfg.restart_credit_cap_multiplier * p.weight * cfg.base_quantum
        out.append(p.model_copy(update={"credit": min(p.credit, cap)}))
    return out
```

### Step 2 — `tests/controller/test_v23_wdrr.py` (create, exactly)
```python
"""SW-W1-S1: weighted deficit round-robin selector (offline, deterministic)."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

from swarm.contracts.v23 import (
    MissionQueueLifecycle,
    MissionQueueState,
    PriorityClass,
    ProjectQueueState,
    ReasonCode,
    SchedulableTask,
    SchedulerDecision,
)
from swarm.scheduling.wdrr import (
    WdrrConfig,
    apply_selection,
    clamp_restart_credit,
    select_next,
)

NOW = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)
REPO = Path(__file__).resolve().parents[2]


def _project(pid: str, weight: float = 1.0, **kw: object) -> ProjectQueueState:
    return ProjectQueueState(project_id=pid, weight=weight, max_concurrency=10_000, **kw)


def _mission(mid: str, pid: str, **kw: object) -> MissionQueueState:
    kw.setdefault("max_parallelism", 10_000)
    return MissionQueueState(mission_id=mid, project_id=pid, enqueued_at=NOW, **kw)


def _task(tid: str, mid: str, pid: str, **kw: object) -> SchedulableTask:
    kw.setdefault("enqueued_at", NOW)
    return SchedulableTask(task_id=tid, mission_id=mid, project_id=pid, **kw)


def _simulate(
    projects: list[ProjectQueueState],
    missions: list[MissionQueueState],
    tasks: list[SchedulableTask],
    rounds: int,
) -> Counter[str]:
    """Each admitted task completes immediately and is replaced (infinite backlog)."""
    served: Counter[str] = Counter()
    for seq in range(1, rounds + 1):
        sel = select_next(projects, missions, tasks, now=NOW)
        assert sel.decision == SchedulerDecision.ADMIT
        assert sel.project_id is not None
        served[sel.project_id] += 1
        projects, missions = apply_selection(projects, missions, sel, sequence=seq)
        projects = [p.model_copy(update={"running": 0}) for p in projects]
        missions = [m.model_copy(update={"running": 0}) for m in missions]
    return served


def test_policy_file_loads() -> None:
    cfg = WdrrConfig.from_policy_file(REPO / "config" / "v23" / "scheduler_policy.v1.json")
    assert cfg.policy_version == "v23-wdrr-1"
    assert cfg.base_quantum == 1.0


def test_long_run_share_proportional_to_weight() -> None:
    weights = {"proj_a": 1.0, "proj_b": 2.0, "proj_c": 3.0}
    projects = [_project(p, w) for p, w in weights.items()]
    missions = [_mission(f"msn_{p}", p) for p in weights]
    tasks = [_task(f"tsk_{p}", f"msn_{p}", p) for p in weights]
    served = _simulate(projects, missions, tasks, rounds=600)
    total_w = sum(weights.values())
    for pid, w in weights.items():
        expected = 600 * w / total_w
        assert abs(served[pid] - expected) <= 0.15 * expected, (pid, served)


def test_more_missions_do_not_amplify_project_share() -> None:
    projects = [_project("proj_many"), _project("proj_one")]
    missions = [_mission(f"msn_many_{i}", "proj_many") for i in range(10)]
    missions.append(_mission("msn_one", "proj_one"))
    tasks = [_task(f"tsk_many_{i}", f"msn_many_{i}", "proj_many") for i in range(10)]
    tasks.append(_task("tsk_one", "msn_one", "proj_one"))
    served = _simulate(projects, missions, tasks, rounds=400)
    assert abs(served["proj_many"] - 200) <= 30
    assert abs(served["proj_one"] - 200) <= 30


def test_low_weight_project_is_not_starved() -> None:
    projects = [_project("proj_small", 0.1), _project("proj_big", 10.0)]
    missions = [_mission("msn_s", "proj_small"), _mission("msn_b", "proj_big")]
    tasks = [_task("tsk_s", "msn_s", "proj_small"), _task("tsk_b", "msn_b", "proj_big")]
    served = _simulate(projects, missions, tasks, rounds=1000)
    assert served["proj_small"] >= 5


def test_blocked_work_does_not_accrue_credit() -> None:
    projects = [_project("proj_a"), _project("proj_blocked")]
    missions = [_mission("msn_a", "proj_a"), _mission("msn_x", "proj_blocked")]
    tasks = [
        _task("tsk_a", "msn_a", "proj_a"),
        _task("tsk_x", "msn_x", "proj_blocked", dependencies_ready=False),
    ]
    sel = select_next(projects, missions, tasks, now=NOW)
    assert sel.project_id == "proj_a"
    assert sel.credits_after["proj_blocked"] == 0.0


def test_stale_cancellation_generation_is_never_selected() -> None:
    projects = [_project("proj_a")]
    missions = [_mission("msn_a", "proj_a", cancellation_generation=2)]
    tasks = [_task("tsk_old", "msn_a", "proj_a", cancellation_generation=1)]
    sel = select_next(projects, missions, tasks, now=NOW)
    assert sel.decision == SchedulerDecision.IDLE
    assert sel.blocked["tsk_old"] == ReasonCode.CANCELLED_GENERATION.value


def test_paused_project_and_caps_are_excluded() -> None:
    projects = [
        _project("proj_paused", paused=True),
        ProjectQueueState(project_id="proj_full", max_concurrency=1, running=1),
    ]
    missions = [_mission("msn_p", "proj_paused"), _mission("msn_f", "proj_full")]
    tasks = [_task("tsk_p", "msn_p", "proj_paused"), _task("tsk_f", "msn_f", "proj_full")]
    sel = select_next(projects, missions, tasks, now=NOW)
    assert sel.decision == SchedulerDecision.DEFER
    assert sel.reason_code == ReasonCode.PROJECT_CONCURRENCY_CAP
    assert sel.blocked["proj_paused"] == ReasonCode.DRAINING.value


def test_draining_mission_is_not_selected() -> None:
    projects = [_project("proj_a")]
    missions = [_mission("msn_a", "proj_a", lifecycle=MissionQueueLifecycle.DRAINING)]
    tasks = [_task("tsk_a", "msn_a", "proj_a")]
    sel = select_next(projects, missions, tasks, now=NOW)
    assert sel.decision == SchedulerDecision.IDLE
    assert sel.blocked["tsk_a"] == ReasonCode.DRAINING.value


def test_resource_unavailable_defers() -> None:
    projects = [_project("proj_a")]
    missions = [_mission("msn_a", "proj_a")]
    tasks = [_task("tsk_a", "msn_a", "proj_a")]
    sel = select_next(projects, missions, tasks, now=NOW, resource_available=lambda t: False)
    assert sel.decision == SchedulerDecision.DEFER
    assert sel.reason_code == ReasonCode.DEFERRED_RESOURCE_UNAVAILABLE


def test_idle_when_no_work() -> None:
    sel = select_next([_project("proj_a")], [], [], now=NOW)
    assert sel.decision == SchedulerDecision.IDLE
    assert sel.reason_code == ReasonCode.NO_ELIGIBLE_WORK


def test_deterministic_and_inputs_not_mutated() -> None:
    projects = [_project("proj_a"), _project("proj_b")]
    missions = [_mission("msn_a", "proj_a"), _mission("msn_b", "proj_b")]
    tasks = [_task("tsk_a", "msn_a", "proj_a"), _task("tsk_b", "msn_b", "proj_b")]
    before = [x.model_dump() for x in [*projects, *missions, *tasks]]
    first = select_next(projects, missions, tasks, now=NOW)
    second = select_next(list(reversed(projects)), missions, list(reversed(tasks)), now=NOW)
    assert first.project_id == second.project_id == "proj_a"
    assert first.candidate_set_hash == second.candidate_set_hash
    assert [x.model_dump() for x in [*projects, *missions, *tasks]] == before


def test_urgent_bonus_is_bounded() -> None:
    projects = [_project("proj_urgent"), _project("proj_normal")]
    missions = [
        _mission("msn_u", "proj_urgent", priority=PriorityClass.URGENT),
        _mission("msn_n", "proj_normal"),
    ]
    tasks = [_task("tsk_u", "msn_u", "proj_urgent"), _task("tsk_n", "msn_n", "proj_normal")]
    served = _simulate(projects, missions, tasks, rounds=400)
    assert served["proj_normal"] >= 150
    assert served["proj_urgent"] <= 250


def test_near_deadline_mission_wins_tie() -> None:
    projects = [_project("proj_a")]
    missions = [
        _mission("msn_late", "proj_a", deadline_at=NOW + timedelta(hours=5)),
        _mission("msn_soon", "proj_a", deadline_at=NOW + timedelta(minutes=1)),
    ]
    tasks = [_task("tsk_l", "msn_late", "proj_a"), _task("tsk_s", "msn_soon", "proj_a")]
    sel = select_next(projects, missions, tasks, now=NOW)
    assert sel.mission_id == "msn_soon"


def test_task_order_within_mission() -> None:
    projects = [_project("proj_a")]
    missions = [_mission("msn_a", "proj_a")]
    tasks = [
        _task("tsk_2", "msn_a", "proj_a", priority=1, enqueued_at=NOW),
        _task("tsk_1", "msn_a", "proj_a", priority=5, enqueued_at=NOW + timedelta(seconds=9)),
    ]
    sel = select_next(projects, missions, tasks, now=NOW + timedelta(seconds=10))
    assert sel.task is not None and sel.task.task_id == "tsk_1"


def test_restart_clamps_positive_credit_only() -> None:
    projects = [_project("proj_rich", credit=500.0), _project("proj_debt", credit=-50.0)]
    clamped = {p.project_id: p.credit for p in clamp_restart_credit(projects)}
    assert clamped["proj_rich"] == 10.0
    assert clamped["proj_debt"] == -50.0
```

### Step 3 — run
```bash
uv run pytest tests/controller/test_v23_wdrr.py -q     # 15 passed
```
If `test_policy_file_loads` fails with FileNotFoundError, SW-W0-S1 has not merged into the integration branch. STOP (S2, section 10).

### Section-5 acceptance
- [ ] 15 tests pass, covering: weight-proportional share within ±15% over 600 decisions; no amplification from more missions; low weight not starved; blocked work earns no credit; stale cancellation generation never selected; paused, draining and capped work excluded with reason codes; resource-unavailable gives DEFER; deterministic output with inputs unchanged; urgent bonus bounded; deadline tie-break; task order; restart clamp.
- [ ] `wdrr.py` imports nothing from `swarm.db`, `swarm.api` or any I/O module.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s1 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s1
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/controller/test_v23_wdrr.py -q
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
git add src/swarm/scheduling/wdrr.py tests/controller/test_v23_wdrr.py docs/v2.3/sessions/SW-W1-S1.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): weighted deficit round-robin selector (project then mission) with bounded urgency/aging" -m "Session: SW-W1-S1. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w1-s1-wdrr
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w1-s1-wdrr --title "[SW-W1-S1] Weighted-deficit round-robin selector (pure, deterministic)" --body-file docs/v2.3/sessions/SW-W1-S1.md
git ls-remote origin refs/heads/cursor/v23-w1-s1-wdrr   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S1.md` with exactly these headings:
```markdown
# SW-W1-S1 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S1.md` then `git commit -m "WIP(SW-W1-S1): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w1-s1-wdrr` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w1-s1-wdrr?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S1
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/scheduling/wdrr.py`, `tests/controller/test_v23_wdrr.py`, `docs/v2.3/sessions/SW-W1-S1.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete").
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
