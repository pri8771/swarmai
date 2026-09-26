# SW-W1-S7 — Fleet trust classes (ART names), drain state machine, deterministic placement

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S7` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w1-s7-fleet-policy` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | SW-W0-S2 |
| Handoff file | `docs/v2.3/sessions/SW-W1-S7.md` |
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
git checkout -b cursor/v23-w1-s7-fleet-policy origin/cursor/sw-v23-integration-460c
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
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/contracts/v23.py && echo "OK src/swarm/contracts/v23.py" || echo "MISSING src/swarm/contracts/v23.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/workers/fleet.py` — modify
- `tests/workers/test_v23_fleet_policy.py` — create
- `docs/v2.3/sessions/SW-W1-S7.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Bring the fleet policy up to the ART-V23 fleet section and finding **F-05** (fleet half):
- Use the ART trust classes (`observe_only` < `sandbox_compute` < `model_worker` < `tool_worker` < `integration_worker`) and accept the legacy names through `LEGACY_TRUST_ALIASES`.
- Add a drain state machine (`active → draining → drained`, and `revoked` as terminal from any state).
- Make placement deterministic and least-privilege: take the lowest sufficient trust rank first, then the lowest `worker_id`.
- Enforce a per-project trust ceiling.
- Make locality strict: a worker without a matching locality is never chosen.
- Refuse placement on workers that the registry reports as DRAINING, QUARANTINED or OFFLINE. `registry.operator_drain` sets an idle worker to OFFLINE.

The public API used by existing callers (`FleetPlacementService(registry)`, `annotate_worker`, `place`, `assert_same_tenant`, `audit_log`, `FleetError`) is preserved. The `trust_class` in decisions is now the ART value, such as `tool_worker`.

The code below was compiled and run against `dev @ 8e1c0fde`. The 6 new tests pass, and `tests/workers tests/portability tests/controller` gives 137 passed and 1 skipped. Paste it **exactly**.

### Step 1 — `src/swarm/workers/fleet.py` (replace the whole file, exactly)
```python
"""V2.3 fleet placement (ART-V23-FLEET-POLICY) — extends worker registry, no second registry.

Trust classes use the ART names (``observe_only`` < ``sandbox_compute`` <
``model_worker`` < ``tool_worker`` < ``integration_worker``). Legacy names are
accepted as aliases. Placement is deterministic and least-privilege: among
eligible workers pick the lowest sufficient trust class, then ``worker_id``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import WorkerStatus
from swarm.contracts.v23 import TRUST_RANK, TrustClass, WorkerDrainState
from swarm.workers.registry import WorkerRegistryService

LEGACY_TRUST_ALIASES: dict[str, TrustClass] = {
    "compute_only": TrustClass.SANDBOX_COMPUTE,
    "code_write": TrustClass.TOOL_WORKER,
    "browser_session": TrustClass.INTEGRATION_WORKER,
    "operator_local": TrustClass.INTEGRATION_WORKER,
}

_DRAIN_TRANSITIONS: dict[WorkerDrainState, set[WorkerDrainState]] = {
    WorkerDrainState.ACTIVE: {WorkerDrainState.DRAINING, WorkerDrainState.REVOKED},
    WorkerDrainState.DRAINING: {
        WorkerDrainState.DRAINED,
        WorkerDrainState.ACTIVE,
        WorkerDrainState.REVOKED,
    },
    WorkerDrainState.DRAINED: {WorkerDrainState.ACTIVE, WorkerDrainState.REVOKED},
    WorkerDrainState.REVOKED: set(),
}


class FleetError(PermissionError):
    pass


def normalize_trust(value: str | TrustClass) -> TrustClass:
    if isinstance(value, TrustClass):
        return value
    if value in LEGACY_TRUST_ALIASES:
        return LEGACY_TRUST_ALIASES[value]
    try:
        return TrustClass(value)
    except ValueError as exc:
        raise FleetError(f"unknown_trust_class:{value}") from exc


@dataclass
class FleetPlacementDecision:
    decision_id: str
    project_id: str
    tenant_id: str
    worker_id: str
    locality: str
    trust_class: str
    reason: str
    at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "worker_id": self.worker_id,
            "locality": self.locality,
            "trust_class": self.trust_class,
            "reason": self.reason,
            "at": self.at,
        }


@dataclass
class FleetAuditEvent:
    event_id: str
    tenant_id: str
    project_id: str
    action: str
    detail: dict[str, Any]
    at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "action": self.action,
            "detail": dict(self.detail),
            "at": self.at,
        }


class FleetPlacementService:
    """Tenant-aware placement using the existing in-memory WorkerRegistryService."""

    def __init__(self, registry: WorkerRegistryService) -> None:
        self.registry = registry
        self._tenant_of_project: dict[str, str] = {}
        self._project_ceiling: dict[str, TrustClass] = {}
        self._worker_tenant: dict[str, str] = {}
        self._worker_locality: dict[str, str] = {}
        self._worker_trust: dict[str, TrustClass] = {}
        self._worker_drain: dict[str, WorkerDrainState] = {}
        self._audit: list[FleetAuditEvent] = []
        self._decisions: list[FleetPlacementDecision] = []

    def _log(self, tenant: str, project: str, action: str, detail: dict[str, Any]) -> None:
        self._audit.append(
            FleetAuditEvent(
                event_id=new_id("faud_"),
                tenant_id=tenant,
                project_id=project,
                action=action,
                detail=detail,
            )
        )

    def bind_project_tenant(self, project_id: str, tenant_id: str) -> None:
        self._tenant_of_project[project_id] = tenant_id

    def set_project_trust_ceiling(self, project_id: str, ceiling: str | TrustClass) -> None:
        self._project_ceiling[project_id] = normalize_trust(ceiling)

    def annotate_worker(
        self,
        worker_id: str,
        *,
        tenant_id: str,
        locality: str = "local",
        trust_class: str = "compute_only",
    ) -> None:
        self._worker_tenant[worker_id] = tenant_id
        self._worker_locality[worker_id] = locality
        self._worker_trust[worker_id] = normalize_trust(trust_class)
        self._worker_drain.setdefault(worker_id, WorkerDrainState.ACTIVE)

    def drain_state(self, worker_id: str) -> WorkerDrainState:
        return self._worker_drain.get(worker_id, WorkerDrainState.ACTIVE)

    def set_drain_state(self, worker_id: str, state: WorkerDrainState) -> WorkerDrainState:
        current = self.drain_state(worker_id)
        if state == current:
            return current
        if state not in _DRAIN_TRANSITIONS[current]:
            raise FleetError(f"drain_transition_illegal:{current.value}->{state.value}")
        self._worker_drain[worker_id] = state
        tenant = self._worker_tenant.get(worker_id, "")
        self._log(tenant, "", "drain_state", {"worker_id": worker_id, "state": state.value})
        return state

    def _registry_blocks(self, worker_id: str) -> str | None:
        rec = self.registry._workers.get(worker_id)  # noqa: SLF001 — shared registry
        if rec is None:
            return "worker_not_registered"
        if rec.revoked:
            return "worker_revoked"
        if rec.lease.status in {
            WorkerStatus.DRAINING,
            WorkerStatus.QUARANTINED,
            WorkerStatus.OFFLINE,
        }:
            return f"worker_{rec.lease.status.value}"
        return None

    def place(
        self,
        *,
        project_id: str,
        preferred_locality: str | None = None,
        min_trust: str = "compute_only",
    ) -> FleetPlacementDecision:
        tenant = self._tenant_of_project.get(project_id)
        if tenant is None:
            raise FleetError("project_tenant_unbound")
        needed = normalize_trust(min_trust)
        ceiling = self._project_ceiling.get(project_id)
        if ceiling is not None and TRUST_RANK[needed] > TRUST_RANK[ceiling]:
            self._log(tenant, project_id, "trust_ceiling_reject", {"needed": needed.value})
            raise FleetError("trust_above_project_ceiling")
        candidates: list[tuple[int, str, str, TrustClass]] = []
        for worker_id in sorted(self.registry._workers):  # noqa: SLF001 — shared registry
            rec = self.registry._workers[worker_id]  # noqa: SLF001
            w_tenant = self._worker_tenant.get(worker_id)
            if w_tenant is None:
                continue
            if w_tenant != tenant:
                self._log(
                    tenant,
                    project_id,
                    "cross_tenant_reject",
                    {"worker_id": worker_id, "worker_tenant": w_tenant},
                )
                continue
            if rec.project_id and rec.project_id != project_id:
                self._log(
                    tenant,
                    project_id,
                    "cross_project_reject",
                    {"worker_id": worker_id, "worker_project": rec.project_id},
                )
                continue
            if self.drain_state(worker_id) != WorkerDrainState.ACTIVE:
                continue
            if self._registry_blocks(worker_id) is not None:
                continue
            locality = self._worker_locality.get(worker_id, "local")
            trust = self._worker_trust.get(worker_id, TrustClass.SANDBOX_COMPUTE)
            if TRUST_RANK[trust] < TRUST_RANK[needed]:
                continue
            if ceiling is not None and TRUST_RANK[trust] > TRUST_RANK[ceiling]:
                continue
            if preferred_locality and locality != preferred_locality:
                continue
            candidates.append((TRUST_RANK[trust], worker_id, locality, trust))
        if not candidates:
            raise FleetError("no_eligible_worker")
        _rank, worker_id, locality, trust = min(candidates)
        decision = FleetPlacementDecision(
            decision_id=new_id("fpl_"),
            project_id=project_id,
            tenant_id=tenant,
            worker_id=worker_id,
            locality=locality,
            trust_class=trust.value,
            reason="tenant_locality_least_privilege",
        )
        self._decisions.append(decision)
        self._log(tenant, project_id, "place", decision.to_dict())
        return decision

    def assert_same_tenant(self, *, actor_tenant: str, resource_tenant: str, action: str) -> None:
        if actor_tenant != resource_tenant:
            self._log(
                actor_tenant,
                "",
                "cross_tenant_denied",
                {"resource_tenant": resource_tenant, "denied_action": action},
            )
            raise FleetError(f"cross_tenant_denied:{action}")

    def audit_log(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._audit]
```

### Step 2 — `tests/workers/test_v23_fleet_policy.py` (create, exactly)
```python
"""SW-W1-S7: ART fleet trust classes, drain states and deterministic placement."""

from __future__ import annotations

import asyncio

import pytest

from swarm.contracts.v23 import TrustClass, WorkerDrainState
from swarm.contracts.workspace import WorkerLease
from swarm.workers.fleet import FleetError, FleetPlacementService, normalize_trust
from swarm.workers.registry import WorkerRegistryService


def _fleet(*workers: tuple[str, str, str]) -> FleetPlacementService:
    """workers: (worker_id, trust_class, locality) — all in tenant ten_a, unbound project."""
    reg = WorkerRegistryService()
    for worker_id, _trust, _loc in workers:
        lease = WorkerLease(
            worker_id=worker_id,
            node_identity=f"n_{worker_id}",
            architecture="x86_64",
            runtime_version="1",
            capacity_units=1.0,
        )
        asyncio.run(reg.register(lease, token=f"tok_{worker_id}"))
    fleet = FleetPlacementService(reg)
    fleet.bind_project_tenant("proj_a", "ten_a")
    for worker_id, trust, loc in workers:
        fleet.annotate_worker(worker_id, tenant_id="ten_a", locality=loc, trust_class=trust)
    return fleet


def test_legacy_aliases_map_to_art_classes() -> None:
    assert normalize_trust("compute_only") == TrustClass.SANDBOX_COMPUTE
    assert normalize_trust("code_write") == TrustClass.TOOL_WORKER
    assert normalize_trust("model_worker") == TrustClass.MODEL_WORKER
    with pytest.raises(FleetError, match="unknown_trust_class"):
        normalize_trust("root")


def test_least_privilege_deterministic_choice() -> None:
    fleet = _fleet(
        ("wk_c", "integration_worker", "local"),
        ("wk_b", "tool_worker", "local"),
        ("wk_a", "tool_worker", "local"),
    )
    first = fleet.place(project_id="proj_a", min_trust="tool_worker")
    second = fleet.place(project_id="proj_a", min_trust="tool_worker")
    assert first.worker_id == second.worker_id == "wk_a"
    assert first.trust_class == "tool_worker"
    assert fleet.place(project_id="proj_a", min_trust="integration_worker").worker_id == "wk_c"


def test_draining_worker_gets_no_new_work() -> None:
    fleet = _fleet(("wk_a", "sandbox_compute", "local"), ("wk_b", "sandbox_compute", "local"))
    fleet.set_drain_state("wk_a", WorkerDrainState.DRAINING)
    assert fleet.place(project_id="proj_a").worker_id == "wk_b"
    fleet.set_drain_state("wk_b", WorkerDrainState.DRAINING)
    with pytest.raises(FleetError, match="no_eligible_worker"):
        fleet.place(project_id="proj_a")
    fleet.set_drain_state("wk_a", WorkerDrainState.DRAINED)
    fleet.set_drain_state("wk_a", WorkerDrainState.ACTIVE)
    assert fleet.place(project_id="proj_a").worker_id == "wk_a"


def test_revoked_is_terminal_and_registry_drain_respected() -> None:
    fleet = _fleet(("wk_a", "sandbox_compute", "local"), ("wk_b", "sandbox_compute", "local"))
    fleet.set_drain_state("wk_a", WorkerDrainState.REVOKED)
    with pytest.raises(FleetError, match="drain_transition_illegal"):
        fleet.set_drain_state("wk_a", WorkerDrainState.ACTIVE)
    fleet.registry.operator_drain("wk_b")
    with pytest.raises(FleetError, match="no_eligible_worker"):
        fleet.place(project_id="proj_a")


def test_project_trust_ceiling() -> None:
    fleet = _fleet(("wk_a", "sandbox_compute", "local"), ("wk_z", "integration_worker", "local"))
    fleet.set_project_trust_ceiling("proj_a", "model_worker")
    with pytest.raises(FleetError, match="trust_above_project_ceiling"):
        fleet.place(project_id="proj_a", min_trust="tool_worker")
    assert fleet.place(project_id="proj_a", min_trust="observe_only").worker_id == "wk_a"


def test_locality_is_strict() -> None:
    fleet = _fleet(("wk_a", "sandbox_compute", "local"), ("wk_e", "sandbox_compute", "edge"))
    assert fleet.place(project_id="proj_a", preferred_locality="edge").worker_id == "wk_e"
    with pytest.raises(FleetError, match="no_eligible_worker"):
        fleet.place(project_id="proj_a", preferred_locality="mars")
```

### Step 3 — run
```bash
uv run pytest tests/workers/test_v23_fleet_policy.py -q      # 6 passed
uv run pytest tests/workers tests/portability tests/controller -q   # all pass (1 pre-existing skip)
```
If an existing test asserts a legacy value such as `"code_write"` as the *output* `trust_class`, that is a base change. STOP (S4, section 10); do not edit that test.

### Section-5 acceptance
- [ ] `normalize_trust("code_write") == TrustClass.TOOL_WORKER` and the other 3 legacy aliases map as documented; unknown names raise `FleetError`.
- [ ] With two eligible workers, placement picks the lowest sufficient trust class and then the lowest `worker_id`, and the result is the same on every run.
- [ ] Draining, drained and revoked workers get no new work; `revoked` cannot transition back.
- [ ] A worker drained via `registry.operator_drain` is not placed.
- [ ] A project trust ceiling below the required class denies placement.
- [ ] Locality is strict.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s7 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s7
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/workers tests/portability -q
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
git add src/swarm/workers/fleet.py tests/workers/test_v23_fleet_policy.py docs/v2.3/sessions/SW-W1-S7.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): ART fleet trust classes with legacy aliases, drain states and deterministic placement" -m "Session: SW-W1-S7. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w1-s7-fleet-policy
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w1-s7-fleet-policy --title "[SW-W1-S7] Fleet trust classes (ART names), drain state machine, deterministic placement" --body-file docs/v2.3/sessions/SW-W1-S7.md
git ls-remote origin refs/heads/cursor/v23-w1-s7-fleet-policy   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S7.md` with exactly these headings:
```markdown
# SW-W1-S7 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S7.md` then `git commit -m "WIP(SW-W1-S7): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w1-s7-fleet-policy` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w1-s7-fleet-policy?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S7
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/workers/fleet.py`, `tests/workers/test_v23_fleet_policy.py`, `docs/v2.3/sessions/SW-W1-S7.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete").
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
