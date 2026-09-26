# SW-W3-S4 — V2.3 deterministic acceptance probes A01–A10

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W3-S4` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w3-s4-acceptance-probes` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 3 |
| Depends on | SW-W2-S1, SW-W1-S5, SW-W1-S6, SW-W1-S7, SW-W1-S8, SW-W1-S11, SW-W0-S1 |
| Handoff file | `docs/v2.3/sessions/SW-W3-S4.md` |
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
git checkout -b cursor/v23-w3-s4-acceptance-probes origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W2-S1, SW-W1-S5, SW-W1-S6, SW-W1-S7, SW-W1-S8, SW-W1-S11, SW-W0-S1. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/scheduling/service.py && echo "OK src/swarm/scheduling/service.py" || echo "MISSING src/swarm/scheduling/service.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/capabilities/lifecycle.py && echo "OK src/swarm/capabilities/lifecycle.py" || echo "MISSING src/swarm/capabilities/lifecycle.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/contracts/router_capabilities.py && echo "OK src/swarm/contracts/router_capabilities.py" || echo "MISSING src/swarm/contracts/router_capabilities.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/observability/trace_graph.py && echo "OK src/swarm/observability/trace_graph.py" || echo "MISSING src/swarm/observability/trace_graph.py"
git cat-file -e origin/cursor/sw-v23-integration-460c:benchmarks/v23_acceptance/scenarios.freeze.json && echo "OK benchmarks/v23_acceptance/scenarios.freeze.json" || echo "MISSING benchmarks/v23_acceptance/scenarios.freeze.json"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/acceptance/v23_probes.py` — create
- `tests/acceptance/test_v23_acceptance.py` — create
- `docs/v2.3/sessions/SW-W3-S4.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Bind the frozen V2.3 acceptance manifest (`benchmarks/v23_acceptance/scenarios.freeze.json`, created by SW-W0-S1) to **ten deterministic probes**, V23-A01 through V23-A10.
- Each probe drives the *real* V2.3 services in-process, with fake brokers and injected clocks: `SchedulerService`, `FleetPlacementService`, `PackLifecycleService`, `PortabilityService`, `OpsEventLog` / `build_trace`, `RouteCapabilities.admissible`, and the `AuthRegistry.require_project` path used by the routes.
- V23-A11 (multi-process, private infrastructure) has no probe. It is reported as `pending_owner_approval`.

**Truth rules** (tests enforce each one):
- `run_v23_probes` always returns `"version_claim": "not_accepted_by_harness"`. The harness never marks V2.3 accepted.
- A probe that raises counts as a **failure** (`error:<Type>`), never as a pass.
- `load_v23_freeze` fails closed in four cases:
  - the schema is not `2.3.0`;
  - the manifest's `policy_version` differs from `config/v23/scheduler_policy.v1.json`;
  - `version_claim_policy` is missing;
  - a scenario names an unknown probe, or scenario ids are duplicated.
- There is no network, no provider and no spend. The only key is a probe-local literal, `b"probe-only-key"`, used to sign a throwaway manifest.
- Probes read the manifest and policy relative to the **repository root**, so run them from there.

**Probe → ART item:**

| Scenario | Probe | What it proves |
|---|---|---|
| A01 | `fairness_three_projects` | weights 1:2:3 over 600 decisions; every share within 15% relative error |
| A02 | `anti_amplification` | 60 child missions do not beat the one-mission project (share stays about 0.5) |
| A03 | `isolation_negatives` | cross-project read 403; cross-tenant placement rejected **and** audited; pack isolation; forged task/mission project never admitted |
| A04 | `restart_recovery` | reload equals pre-restart state; credit clamped to the restart cap; expired intent compensated exactly once; stale epoch cannot write |
| A05 | `drain_active` | a draining worker gets no placement; a cancelled mission gets no admission; a duplicate result gives `already_terminal` |
| A06 | `pack_lifecycle` | unsigned or wrongly signed packs refused; enable → deny other project → no widening → drain → disable → uninstall |
| A07 | `portability_roundtrip` | secret values refused; digests verify in a clean root; tampering refused; approvals and leases tombstoned |
| A08 | `trace_chain` | the full `TRACE_CHAIN` is linked through `parent_event_id`; a gap is reported, not invented |
| A09 | `failure_truth` | provider unavailable gives DEFER `deferred_resource_unavailable` with nothing reserved; the site-scoped ops event records it; a lost or drained worker gets no work |
| A10 | `zero_spend` | billing `paid`, `unknown`, `trial` or missing is denied (`paid_route_forbidden`); `free` is admitted |

**Known limitation (do not fix here).** A non-admit decision has no task, so its `scheduler.decision` event carries `project_id=None` and appears only in the admin (site-wide) view. That is why A09 queries by `kind`. Record it in the PR body under "Follow-ups".

The code below was compiled and run against `dev @ 8e1c0fde` plus every Wave-1/Wave-2 change and the SW-W0-S1 manifest:
- `tests/acceptance`: 39 passed (15 new).
- All ten probes: `pass`.
- ruff and mypy: clean.

### Step 1 — `src/swarm/acceptance/v23_probes.py` (create, exactly)
```python
"""Deterministic V2.3 acceptance probes bound to the frozen scenario manifest.

Manifest: ``benchmarks/v23_acceptance/scenarios.freeze.json``.

Each probe drives the real V2.3 services (scheduler, fleet, packs, portability,
ops trace, route admission) in-process with fake brokers and injected clocks.
Probes never touch the network, never spend, and the runner never marks a version
accepted: ``version_claim`` is always ``not_accepted_by_harness``.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from swarm.acceptance.probes import ProbeResult
from swarm.api.auth import AuthRegistry
from swarm.api.errors import ApiError
from swarm.capabilities import CapabilityPackManifest, CapabilityPackRegistry
from swarm.capabilities.lifecycle import PackLifecycleService
from swarm.capabilities.signing import sign_manifest
from swarm.contracts.router_capabilities import RouteCapabilities, parse_billing
from swarm.contracts.v23 import (
    DispatchIntent,
    DispatchIntentComponent,
    ReasonCode,
    SchedulableTask,
    SchedulerDecision,
    WorkerDrainState,
)
from swarm.contracts.workspace import WorkerLease
from swarm.extensions.registry import ExtensionAuthzError
from swarm.observability import TRACE_CHAIN, OpsEventLog, build_trace
from swarm.product.portability import PortabilityService
from swarm.scheduling.epoch import InMemorySchedulerEpochService
from swarm.scheduling.memory_store import InMemorySchedulingStore
from swarm.scheduling.service import SchedulerService
from swarm.scheduling.wdrr import WdrrConfig
from swarm.workers.fleet import FleetError, FleetPlacementService
from swarm.workers.registry import WorkerRegistryService

FREEZE_SCHEMA = "2.3.0"
DEFAULT_FREEZE = Path("benchmarks/v23_acceptance/scenarios.freeze.json")
DEFAULT_POLICY = Path("config/v23/scheduler_policy.v1.json")
VERSION_CLAIM = "not_accepted_by_harness"
_T0 = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

Probe = Callable[[Path, dict[str, Any]], ProbeResult]


class V23FreezeError(ValueError):
    pass


# ------------------------------------------------------------------ fakes
class _Clock:
    def __init__(self) -> None:
        self.now = _T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now = self.now + timedelta(seconds=seconds)


class _Broker:
    def __init__(self) -> None:
        self.outstanding = 0
        self.reserves = 0
        self.releases = 0

    def reserve(self, intent: DispatchIntent, comp: DispatchIntentComponent) -> str:
        self.outstanding += 1
        self.reserves += 1
        return f"rsv_{self.reserves}"

    def release(self, intent: DispatchIntent, comp: DispatchIntentComponent) -> None:
        self.outstanding -= 1
        self.releases += 1


def _service(
    *,
    store: InMemorySchedulingStore | None = None,
    broker: _Broker | None = None,
    clock: _Clock | None = None,
    epochs: InMemorySchedulerEpochService | None = None,
    holder_id: str = "probe_a",
    ops: OpsEventLog | None = None,
    **kw: Any,
) -> tuple[SchedulerService, InMemorySchedulingStore, _Broker, _Clock]:
    clock = clock or _Clock()
    store = store or InMemorySchedulingStore()
    broker = broker or _Broker()
    svc = SchedulerService(
        store,
        epochs=epochs or InMemorySchedulerEpochService(clock=clock),
        holder_id=holder_id,
        reserve=broker.reserve,
        release=broker.release,
        clock=clock,
        ops=ops,
        config=WdrrConfig.from_policy_file(DEFAULT_POLICY) if DEFAULT_POLICY.is_file() else None,
        **kw,
    )
    return svc, store, broker, clock


def _task(project_id: str, mission_id: str, n: int, **kw: Any) -> SchedulableTask:
    return SchedulableTask(
        task_id=f"{mission_id}_t{n}",
        mission_id=mission_id,
        project_id=project_id,
        attempt_id=f"att_{mission_id}_{n}",
        enqueued_at=_T0 - timedelta(hours=1),
        **kw,
    )


def _share(svc: SchedulerService, demand: dict[str, list[str]], decisions: int) -> dict[str, int]:
    counts = dict.fromkeys(demand, 0)
    for n in range(decisions):
        tasks = [_task(p, m, n) for p, ms in demand.items() for m in ms]
        out = svc.schedule_once(tasks)
        if out.decision == SchedulerDecision.ADMIT and out.intent and out.task:
            counts[out.task.project_id] += 1
            svc.mark_dispatched(out.intent.intent_id)
            svc.finish(out.intent.intent_id)
    return counts


def _result(checks: dict[str, bool], detail: dict[str, Any]) -> ProbeResult:
    failed = [name for name, ok in checks.items() if not ok]
    status = "pass" if not failed else f"fail:{failed[0]}"
    return ProbeResult(not failed, status, {"checks": checks, **detail})


def _tolerance(scenario: dict[str, Any]) -> float:
    return float(scenario.get("_tolerance", 0.15))


# ------------------------------------------------------------------ probes
def probe_fairness_three_projects(work: Path, scenario: dict[str, Any]) -> ProbeResult:
    workload = scenario["workload"]
    weights: dict[str, float] = {k: float(v) for k, v in workload["projects"].items()}
    decisions = int(workload["decisions"])
    svc, _, _, _ = _service()
    for pid, w in weights.items():
        svc.register_project(pid, weight=w)
        svc.register_mission(f"{pid}_m", pid)
    counts = _share(svc, {p: [f"{p}_m"] for p in weights}, decisions)
    total_w = sum(weights.values())
    tol = _tolerance(scenario)
    errors = {
        p: abs(counts[p] / decisions - weights[p] / total_w) / (weights[p] / total_w)
        for p in weights
    }
    checks = {
        "share_within_tolerance": all(e <= tol for e in errors.values()),
        "every_project_admitted": all(c > 0 for c in counts.values()),
    }
    return _result(checks, {"admitted": counts, "relative_error": errors})


def probe_anti_amplification(work: Path, scenario: dict[str, Any]) -> ProbeResult:
    workload = scenario["workload"]
    fan = int(workload["expanding_project_tasks"])
    decisions = int(workload["decisions"])
    svc, _, _, _ = _service()
    svc.register_project("expanding")
    svc.register_project("baseline")
    missions = [f"exp_m{i}" for i in range(fan)]
    for m in missions:
        svc.register_mission(m, "expanding")
    svc.register_mission("base_m", "baseline")
    counts = _share(svc, {"expanding": missions, "baseline": ["base_m"]}, decisions)
    share = counts["expanding"] / decisions
    checks = {"expanding_share_within_tolerance": abs(share - 0.5) <= 0.5 * _tolerance(scenario)}
    return _result(checks, {"admitted": counts, "expanding_share": share})


def _registry_with(*workers: str) -> WorkerRegistryService:
    reg = WorkerRegistryService()
    for worker_id in workers:
        lease = WorkerLease(
            worker_id=worker_id,
            node_identity=f"n_{worker_id}",
            architecture="x86_64",
            runtime_version="1",
            capacity_units=1.0,
        )
        asyncio.run(reg.register(lease, token=f"tok_{worker_id}"))
    return reg


def _denied(fn: Callable[[], Any], exc: type[BaseException]) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def probe_isolation_negatives(work: Path, scenario: dict[str, Any]) -> ProbeResult:
    auth = AuthRegistry()
    auth.issue(subject="a", project_ids={"proj_a"}, token="atk_probe_a")
    principal = auth.tokens["atk_probe_a"]
    ops_denied = False
    try:
        auth.require_project(principal, "proj_b")
    except ApiError as err:
        ops_denied = err.status_code == 403

    fleet = FleetPlacementService(_registry_with("wk_b"))
    fleet.bind_project_tenant("proj_a", "ten_a")
    fleet.annotate_worker("wk_b", tenant_id="ten_b")
    placement_rejected = _denied(lambda: fleet.place(project_id="proj_a"), FleetError)
    audited = any(e["action"] == "cross_tenant_reject" for e in fleet.audit_log())

    packs = PackLifecycleService(CapabilityPackRegistry())
    packs.install(
        CapabilityPackManifest(
            pack_id="pk", version="1", content_digest="d", capability_declarations=["read"]
        )
    )
    packs.enable_for_project("pk", "1", "proj_a", ["read"])
    pack_isolated = _denied(
        lambda: packs.check_use("pk", "1", "proj_b", "read"), ExtensionAuthzError
    )

    svc, _, broker, _ = _service()
    svc.register_project("proj_a")
    svc.register_project("proj_b")
    svc.register_mission("m_a", "proj_a")
    forged = _task("proj_b", "m_a", 1)
    out = svc.schedule_once([forged])
    checks = {
        "cross_project_ops_read_403": ops_denied,
        "cross_tenant_placement_rejected": placement_rejected,
        "cross_tenant_placement_audited": audited,
        "pack_not_usable_by_other_project": pack_isolated,
        "mismatched_project_never_admitted": out.decision != SchedulerDecision.ADMIT
        and broker.reserves == 0,
    }
    blocked = out.receipt.detail.get("blocked", {}) if out.receipt else {}
    return _result(checks, {"forged_task_block": blocked.get(forged.task_id)})


def probe_restart_recovery(work: Path, scenario: dict[str, Any]) -> ProbeResult:
    clock = _Clock()
    epochs = InMemorySchedulerEpochService(clock=clock)
    old, store, broker, _ = _service(clock=clock, epochs=epochs, holder_id="old")
    old.register_project("p")
    old.register_mission("m", "p")
    old.register_project("q")
    old.register_mission("qm", "q")
    pending = old.schedule_once([_task("p", "m", 1)])
    before = {p.project_id: p.model_dump(mode="json") for p in store.list_projects()}
    cfg = old.config
    rich = store.get_project("q")
    assert rich is not None
    cap = cfg.restart_credit_cap_multiplier * rich.weight * cfg.base_quantum
    store.put_project(rich.model_copy(update={"credit": cap * 5}), expected_version=rich.version)
    clock.advance(60)
    new, _, _, _ = _service(store=store, broker=broker, clock=clock, epochs=epochs, holder_id="new")
    reloaded = {p.project_id: p.model_dump(mode="json") for p in store.list_projects()}
    report = new.recover()
    releases_after_first = broker.releases
    new.recover()
    admitted = new.schedule_once([_task("p", "m", 2)])
    stale = old.schedule_once([_task("p", "m", 3)])
    q_after = store.get_project("q")
    checks = {
        "state_reloaded_equal": reloaded["p"] == before["p"],
        "positive_credit_clamped": q_after is not None and q_after.credit <= cap + 1e-9,
        "expired_intent_compensated_once": pending.intent is not None
        and report["expired_intents"] == [pending.intent.intent_id]
        and broker.releases == releases_after_first,
        "new_holder_admits": admitted.decision == SchedulerDecision.ADMIT,
        "stale_epoch_cannot_write": stale.reason_code == ReasonCode.STALE_SCHEDULER_EPOCH,
    }
    return _result(checks, {"recover": report})


def probe_drain_active(work: Path, scenario: dict[str, Any]) -> ProbeResult:
    fleet = FleetPlacementService(_registry_with("wk_a", "wk_b"))
    fleet.bind_project_tenant("p", "ten")
    fleet.annotate_worker("wk_a", tenant_id="ten")
    fleet.annotate_worker("wk_b", tenant_id="ten")
    fleet.set_drain_state("wk_a", WorkerDrainState.DRAINING)
    placements = {fleet.place(project_id="p").worker_id for _ in range(5)}

    svc, _, broker, _ = _service()
    svc.register_project("p")
    svc.register_mission("m_live", "p")
    svc.register_mission("m_drain", "p")
    active = svc.schedule_once([_task("p", "m_drain", 1)])
    assert active.intent is not None
    svc.mark_dispatched(active.intent.intent_id)
    svc.cancel_mission("m_drain")
    later = [svc.schedule_once([_task("p", "m_drain", n), _task("p", "m_live", n)])
             for n in range(2, 6)]
    first = svc.finish(active.intent.intent_id)
    dup = svc.finish(active.intent.intent_id)
    checks = {
        "draining_worker_no_new_placement": placements == {"wk_b"},
        "draining_mission_no_new_admission": all(
            o.task is None or o.task.mission_id == "m_live" for o in later
        ),
        "no_duplicate_accepted_result": not (first.accepted and dup.accepted)
        and dup.reason == "already_terminal",
        "reservations_released": broker.outstanding == sum(
            1 for o in later if o.decision == SchedulerDecision.ADMIT
        ),
    }
    return _result(checks, {"first_result": first.reason, "duplicate_result": dup.reason})


def _pack_denied(packs: PackLifecycleService, project_id: str, capability: str) -> bool:
    return _denied(lambda: packs.check_use("pk", "1", project_id, capability), ExtensionAuthzError)


def probe_pack_lifecycle(work: Path, scenario: dict[str, Any]) -> ProbeResult:
    key = b"probe-only-key"
    registry = CapabilityPackRegistry(require_signature=True, trusted_keys={"acme": key})
    packs = PackLifecycleService(registry)
    base = CapabilityPackManifest(
        pack_id="pk",
        version="1",
        content_digest="sha256:pk",
        capability_declarations=["read"],
        publisher="acme",
    )
    unsigned_refused = _denied(lambda: packs.install(base), ExtensionAuthzError)
    wrong = sign_manifest(base, key=b"wrong-key")
    wrong_refused = _denied(lambda: packs.install(wrong), ExtensionAuthzError)
    packs.install(sign_manifest(base, key=key))
    packs.enable_for_project("pk", "1", "proj_a", ["read"])
    usable = not _pack_denied(packs, "proj_a", "read")
    other_denied = _pack_denied(packs, "proj_b", "read")
    no_widen = _pack_denied(packs, "proj_a", "write")
    packs.begin_drain("pk", "1")
    drain_denied = _pack_denied(packs, "proj_a", "read")
    packs.disable("pk", "1")
    packs.uninstall("pk", "1")
    actions = [h["action"] for h in packs.history("pk", "1")]
    checks = {
        "unsigned_refused": unsigned_refused,
        "wrong_signature_refused": wrong_refused,
        "enabled_project_can_use": usable,
        "other_project_denied": other_denied,
        "no_implicit_widening": no_widen,
        "draining_denies_use": drain_denied,
        "full_lifecycle_recorded": actions == ["install", "drain", "disable", "uninstall"],
    }
    return _result(checks, {"history": actions})


def probe_portability_roundtrip(work: Path, scenario: dict[str, Any]) -> ProbeResult:
    svc = PortabilityService()
    src_dir = work / "export"
    secret_refused = _denied(
        lambda: svc.export_project(
            project_id="p", project_config={"api_key": "plain-value"}, out_dir=src_dir
        ),
        ValueError,
    )
    bundle = svc.export_project(
        project_id="p",
        project_config={"name": "demo", "token_ref": "env:SWARM_DEMO_TOKEN"},
        approvals=[{"approval_id": "apr_1", "state": "approved", "project_id": "p"}],
        leases=[{"lease_id": "lse_1", "state": "active", "project_id": "p"}],
        out_dir=src_dir,
    )
    clean = work / "clean_root"
    clean.mkdir(parents=True, exist_ok=True)
    copied = clean / f"{bundle.bundle_id}.json"
    copied.write_text((src_dir / f"{bundle.bundle_id}.json").read_text(encoding="utf-8"))
    imported = svc.import_bundle(copied, target_project_id="p_clean")
    rows = imported.sections.get("approvals", []) + imported.sections.get("leases", [])
    tampered = json.loads(copied.read_text(encoding="utf-8"))
    tampered["sections"]["approvals"][0]["executable"] = True
    bad = clean / "tampered.json"
    bad.write_text(json.dumps(tampered), encoding="utf-8")
    checks = {
        "secret_values_refused": secret_refused,
        "digests_verify_after_import": imported.integrity_digest == bundle.integrity_digest,
        "tampered_bundle_refused": _denied(lambda: svc.import_bundle(bad), ValueError),
        "approvals_leases_tombstoned": bool(rows)
        and all(r["state"] == "tombstoned" and r["executable"] is False for r in rows),
        "remapped_to_target": imported.project_id == "p_clean",
    }
    return _result(checks, {"bundle_id": bundle.bundle_id})


def probe_trace_chain(work: Path, scenario: dict[str, Any]) -> ProbeResult:
    log = OpsEventLog()
    parent: str | None = None
    for stage in TRACE_CHAIN:
        parent = log.emit(
            stage[0], "probe", project_id="p", trace_id="tr_probe", parent_event_id=parent
        ).event_id
    graph = build_trace(log, "tr_probe")
    log.emit("operator.action", "probe", project_id="p", trace_id="tr_gap")
    gap = build_trace(log, "tr_gap")
    checks = {
        "chain_linked_in_order": [n.kind for n in graph.nodes] == [s[0] for s in TRACE_CHAIN],
        "trace_complete": graph.complete,
        "durable_ids": all(n.event_id.startswith("oev_") for n in graph.nodes),
        "gap_reported_not_invented": not gap.complete and "mission.created" in gap.missing,
    }
    return _result(checks, {"nodes": len(graph.nodes)})


def probe_failure_truth(work: Path, scenario: dict[str, Any]) -> ProbeResult:
    ops = OpsEventLog()
    svc, _, broker, _ = _service(ops=ops, resource_available=lambda t: False)
    svc.register_project("p")
    svc.register_mission("m", "p")
    out = svc.schedule_once([_task("p", "m", 1, provider_route="rt_down")])
    # Non-admit receipts carry no task, so the event is site-scoped (project_id None).
    events = ops.list_events(kind="scheduler.decision")
    fleet = FleetPlacementService(_registry_with("wk_lost"))
    fleet.bind_project_tenant("p", "ten")
    fleet.annotate_worker("wk_lost", tenant_id="ten")
    fleet.registry.operator_drain("wk_lost")
    lost = _denied(lambda: fleet.place(project_id="p"), FleetError)
    checks = {
        "defer_not_admit": out.decision == SchedulerDecision.DEFER,
        "reason_resource_unavailable": out.reason_code == ReasonCode.DEFERRED_RESOURCE_UNAVAILABLE,
        "nothing_reserved": broker.reserves == 0,
        "ops_event_records_blocked_state": any(
            e["detail"].get("decision") == "defer"
            and e["detail"].get("reason_code") == ReasonCode.DEFERRED_RESOURCE_UNAVAILABLE.value
            for e in events
        ),
        "lost_worker_gets_no_work": lost,
    }
    return _result(checks, {"reason": out.reason_code.value if out.reason_code else None})


def probe_zero_spend(work: Path, scenario: dict[str, Any]) -> ProbeResult:
    def route(billing: str) -> RouteCapabilities:
        return RouteCapabilities(
            model_id=f"m_{billing}", kind="route", billing=parse_billing(billing)
        )

    verdicts = {b: route(b).admissible() for b in ("free", "trial", "paid", "unknown", "")}
    checks = {
        "free_admitted": verdicts["free"] == (True, None),
        "paid_denied": verdicts["paid"] == (False, ReasonCode.PAID_ROUTE_FORBIDDEN.value),
        "unknown_denied": verdicts["unknown"] == (False, ReasonCode.PAID_ROUTE_FORBIDDEN.value),
        "missing_billing_denied": verdicts[""][0] is False,
        "trial_denied": verdicts["trial"][0] is False,
    }
    return _result(checks, {"verdicts": {k: list(v) for k, v in verdicts.items()}})


PROBES: dict[str, Probe] = {
    "fairness_three_projects": probe_fairness_three_projects,
    "anti_amplification": probe_anti_amplification,
    "isolation_negatives": probe_isolation_negatives,
    "restart_recovery": probe_restart_recovery,
    "drain_active": probe_drain_active,
    "pack_lifecycle": probe_pack_lifecycle,
    "portability_roundtrip": probe_portability_roundtrip,
    "trace_chain": probe_trace_chain,
    "failure_truth": probe_failure_truth,
    "zero_spend": probe_zero_spend,
}


# ------------------------------------------------------------------ freeze + runner
def load_v23_freeze(
    path: Path = DEFAULT_FREEZE, *, policy: Path = DEFAULT_POLICY
) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != FREEZE_SCHEMA:
        raise V23FreezeError(f"freeze_schema_mismatch:{data.get('schema_version')}")
    policy_version = json.loads(policy.read_text(encoding="utf-8"))["policy_version"]
    if data.get("policy_version") != policy_version:
        raise V23FreezeError("freeze_policy_version_mismatch")
    if data.get("version_claim_policy") != "never_mark_accepted_from_harness":
        raise V23FreezeError("freeze_version_claim_policy_missing")
    ids = [s["id"] for s in data["scenarios"]]
    if len(ids) != len(set(ids)):
        raise V23FreezeError("freeze_duplicate_scenario_id")
    for s in data["scenarios"]:
        probe = s.get("deterministic_probe")
        if probe is not None and probe not in PROBES:
            raise V23FreezeError(f"freeze_unknown_probe:{s['id']}:{probe}")
    return data


def run_v23_probes(
    work: Path, *, freeze: Path = DEFAULT_FREEZE, policy: Path = DEFAULT_POLICY
) -> dict[str, Any]:
    data = load_v23_freeze(freeze, policy=policy)
    tol = float(data.get("tolerance", {}).get("relative_share_error", 0.15))
    results: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    for s in data["scenarios"]:
        probe = s.get("deterministic_probe")
        if probe is None:
            pending.append({"id": s["id"], "status": s.get("status", "pending")})
            continue
        scenario_work = work / s["id"]
        scenario_work.mkdir(parents=True, exist_ok=True)
        try:
            res = PROBES[probe](scenario_work, {**s, "_tolerance": tol})
        except Exception as exc:  # noqa: BLE001 — a crashing probe is a failure, never a pass
            res = ProbeResult(False, f"error:{type(exc).__name__}", {"message": str(exc)[:300]})
        results.append({"id": s["id"], "probe": probe, "gate": s["primary_gate"], **res.to_dict()})
    return {
        "freeze_id": data["freeze_id"],
        "policy_version": data["policy_version"],
        "version_claim": VERSION_CLAIM,
        "deterministic_passed": sum(1 for r in results if r["ok"]),
        "deterministic_total": len(results),
        "results": results,
        "pending": pending,
    }
```

### Step 2 — `tests/acceptance/test_v23_acceptance.py` (create, exactly)
```python
"""SW-W3-S4: deterministic V2.3 probes A01-A10 bound to the frozen scenario manifest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from swarm.acceptance.v23_probes import (
    DEFAULT_FREEZE,
    PROBES,
    VERSION_CLAIM,
    V23FreezeError,
    load_v23_freeze,
    run_v23_probes,
)


@pytest.fixture(scope="module")
def report(tmp_path_factory: pytest.TempPathFactory) -> dict:
    return run_v23_probes(tmp_path_factory.mktemp("v23"))


def test_every_deterministic_scenario_has_a_probe() -> None:
    data = load_v23_freeze()
    probes = {s["deterministic_probe"] for s in data["scenarios"] if s["deterministic_probe"]}
    assert probes == set(PROBES)


@pytest.mark.parametrize("scenario_id", [f"V23-A{n:02d}" for n in range(1, 11)])
def test_probe_passes(report: dict, scenario_id: str) -> None:
    row = next(r for r in report["results"] if r["id"] == scenario_id)
    assert row["ok"], row


def test_harness_never_claims_acceptance(report: dict) -> None:
    assert report["version_claim"] == VERSION_CLAIM
    assert report["deterministic_passed"] == report["deterministic_total"] == 10
    assert report["pending"] == [{"id": "V23-A11", "status": "pending_owner_approval"}]
    assert "accepted" not in json.dumps(report["pending"])


def test_unknown_probe_fails_closed(tmp_path: Path) -> None:
    data = json.loads(DEFAULT_FREEZE.read_text(encoding="utf-8"))
    data["scenarios"][0]["deterministic_probe"] = "made_up"
    bad = tmp_path / "freeze.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(V23FreezeError, match="freeze_unknown_probe"):
        load_v23_freeze(bad)


def test_policy_drift_fails_closed(tmp_path: Path) -> None:
    data = json.loads(DEFAULT_FREEZE.read_text(encoding="utf-8"))
    data["policy_version"] = "v23-wdrr-999"
    bad = tmp_path / "freeze.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(V23FreezeError, match="freeze_policy_version_mismatch"):
        load_v23_freeze(bad)


def test_crashing_probe_is_a_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(work: Path, scenario: dict) -> None:
        raise RuntimeError("boom")

    monkeypatch.setitem(PROBES, "zero_spend", boom)
    row = next(r for r in run_v23_probes(tmp_path)["results"] if r["id"] == "V23-A10")
    assert row["ok"] is False and row["status"] == "error:RuntimeError"
```

### Step 3 — run (from the repository root)
```bash
uv run pytest tests/acceptance/test_v23_acceptance.py -q      # 15 passed
uv run pytest tests/acceptance -q
uv run python -c "import tempfile,pathlib,json; from swarm.acceptance.v23_probes import run_v23_probes as r; x=r(pathlib.Path(tempfile.mkdtemp())); print(x['deterministic_passed'], x['deterministic_total'], x['version_claim'])"
# expect: 10 10 not_accepted_by_harness
```
If a probe fails, **do not loosen its check**. Print its `detail["checks"]`: the failing key names the broken behaviour in a dependency session. STOP (S3, section 10) and name that key in the handoff.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w3_s4 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w3_s4
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/acceptance -q
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
git add src/swarm/acceptance/v23_probes.py tests/acceptance/test_v23_acceptance.py docs/v2.3/sessions/SW-W3-S4.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): deterministic acceptance probes A01-A10 bound to the frozen scenario manifest" -m "Session: SW-W3-S4. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w3-s4-acceptance-probes
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w3-s4-acceptance-probes --title "[SW-W3-S4] V2.3 deterministic acceptance probes A01–A10" --body-file docs/v2.3/sessions/SW-W3-S4.md
git ls-remote origin refs/heads/cursor/v23-w3-s4-acceptance-probes   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W3-S4.md` with exactly these headings:
```markdown
# SW-W3-S4 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W3-S4.md` then `git commit -m "WIP(SW-W3-S4): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w3-s4-acceptance-probes` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w3-s4-acceptance-probes?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W3-S4
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/acceptance/v23_probes.py`, `tests/acceptance/test_v23_acceptance.py`, `docs/v2.3/sessions/SW-W3-S4.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete").
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
