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
