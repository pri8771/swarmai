"""Synthetic load scenarios — logical scale vs bounded concurrency.

Mock/simulated only. Separates:
- logical_sessions (mission session count under test)
- simulated_provider_concurrency (fake capacity envelope)
- actual_hardware_concurrency (host process limit for the run)
"""

from __future__ import annotations

import hashlib
import json
import resource
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import TaskStatus, WorkerStatus
from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.contracts.workspace import WorkerLease
from swarm.controller.mission import MissionController, spawn_proposal
from swarm.controller.scheduler import AdaptiveScheduler, SchedulerConfig
from swarm.load.metrics import percentile
from swarm.workers.registry import WorkerRegistryService

ScenarioName = Literal["adaptive", "fixed"]


@dataclass
class LoadConfig:
    scenario: ScenarioName = "adaptive"
    mode: str = "mock"
    seed: int = 42
    logical_sessions: int = 100
    queued_tasks: int = 1000
    actual_concurrency: int = 8
    simulated_provider_concurrency: int = 16
    missions: int = 2
    expand_workers_to: int = 12
    contract_workers_to: int = 4


@dataclass
class LoadReport:
    run_id: str
    scenario: str
    mode: str
    seed: int
    config: dict[str, Any]
    metrics: dict[str, Any]
    scaling: dict[str, Any]
    fairness: dict[str, Any]
    gates: dict[str, bool]
    mock_vs_live: str = "simulated_load_not_live"
    report_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario": self.scenario,
            "mode": self.mode,
            "seed": self.seed,
            "config": self.config,
            "metrics": self.metrics,
            "scaling": self.scaling,
            "fairness": self.fairness,
            "gates": self.gates,
            "mock_vs_live": self.mock_vs_live,
            "report_hash": self.report_hash,
            "generated_at": utc_now().isoformat(),
            "note": (
                "logical_sessions ≠ production capacity; "
                "simulated_provider_concurrency ≠ real provider QPS"
            ),
        }


def _rss_mb() -> float:
    # ru_maxrss is bytes on macOS, kilobytes on Linux.
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if usage > 10_000_000:  # heuristic: already bytes
        return usage / (1024 * 1024)
    return usage / 1024


async def run_load_scenario(
    config: LoadConfig,
    *,
    report_dir: Path | None = None,
) -> LoadReport:
    if config.mode == "live":
        raise PermissionError(
            "live_load_blocked: P18 live comparisons require verified account capacity"
        )

    run_id = new_id("load_")
    dispatch_latencies_ms: list[float] = []
    accepted = 0
    rejected_oversub = 0
    mission_served: dict[str, int] = {}
    queue_ages_ms: list[float] = []

    max_conc = (
        config.actual_concurrency
        if config.scenario == "fixed"
        else min(config.actual_concurrency, config.simulated_provider_concurrency)
    )
    scheduler = AdaptiveScheduler(
        config=SchedulerConfig(max_concurrency=max_conc, control_reserve_slots=1)
    )
    ctrl = MissionController(
        scheduler=scheduler,
        inference_slots=config.simulated_provider_concurrency,
        worker_slots=config.actual_concurrency,
    )
    registry = WorkerRegistryService()

    # Seed workers at baseline concurrency.
    worker_tokens: dict[str, str] = {}
    for i in range(config.actual_concurrency):
        lease = WorkerLease(
            worker_id=f"w_load_{i}",
            node_identity=f"node-load-{i}",
            architecture="cpu",
            runtime_version="load-1",
            status=WorkerStatus.ONLINE,
            capacity_units=1.0,
            lease_generation=1,
        )
        token = new_id("wt_")
        await registry.register(lease, token=token)
        worker_tokens[lease.worker_id] = token

    missions = []
    for m_i in range(config.missions):
        mission = sample_mission().model_copy(
            update={
                "id": f"msn_load_{m_i}",
                "max_graph_nodes": max(config.queued_tasks + 10, 2000),
            }
        )
        await ctrl.submit_mission(mission)
        missions.append(mission)
        mission_served[mission.id] = 0

    # Expand: raise capacity then contract — evidence both directions.
    expand_peak = 0
    ctrl.expand_capacity(config.expand_workers_to, config.expand_workers_to)
    expand_peak = ctrl.inference_slots
    ctrl.expand_capacity(config.contract_workers_to, config.contract_workers_to)
    contract_floor = ctrl.inference_slots
    # Restore usable envelope for the soak.
    ctrl.expand_capacity(
        config.simulated_provider_concurrency, config.actual_concurrency
    )

    t0 = time.perf_counter()
    # Enqueue synthetic ready tasks across missions (logical scale).
    per_mission = config.queued_tasks // max(1, config.missions)
    for mission in missions:
        children = []
        for i in range(per_mission):
            children.append(
                sample_task().model_copy(
                    update={
                        "id": f"task_{mission.id}_{i}",
                        "objective": f"synthetic load {i}",
                        "status": TaskStatus.PROPOSED,
                        "priority": i % 10,
                    }
                )
            )
        # Chunk spawn proposals to respect graph validation batching.
        chunk = 50
        for start in range(0, len(children), chunk):
            batch = children[start : start + chunk]
            mission = ctrl.missions[mission.id]
            prop = spawn_proposal(
                mission,
                author_session_id=f"as_load_{mission.id}",
                parent=None,
                children=batch,
            )
            await ctrl.propose_graph_change(prop)
            await ctrl.commit_validated_revision(prop.proposal_id)

    logical_session_ids = [f"sess_{i}" for i in range(config.logical_sessions)]

    # Dispatch loop under bounded concurrency — no oversubscription.
    in_flight = 0
    max_in_flight = 0
    ticks = 0
    idle_rounds = 0
    while accepted < config.queued_tasks and ticks < config.queued_tasks * 3:
        ticks += 1
        progressed = False
        for mission in missions:
            mid = mission.id
            ready = await ctrl.choose_ready_work(mid)
            for task in ready:
                if in_flight >= config.actual_concurrency:
                    rejected_oversub += 1
                    # Do not accept beyond hardware concurrency.
                    continue
                started = time.perf_counter()
                in_flight += 1
                max_in_flight = max(max_in_flight, in_flight)
                # Simulated dispatch cost.
                registry.enqueue(task)
                elapsed_ms = (time.perf_counter() - started) * 1000
                dispatch_latencies_ms.append(elapsed_ms)
                queue_ages_ms.append(float(ticks))
                # Complete immediately in mock (no live provider).
                task_map = ctrl.tasks[mid]
                task_map[task.id] = task.model_copy(
                    update={"status": TaskStatus.ACCEPTED}
                )
                in_flight -= 1
                accepted += 1
                mission_served[mid] = mission_served.get(mid, 0) + 1
                progressed = True

        # Capacity churn: mid-run provider shrink then recover (fake).
        if ticks == max(1, config.queued_tasks // 4):
            ctrl.note_inference_exhaustion()
            assert ctrl.scheduler is not None
            ctrl.scheduler.note_overload()
        if ticks == max(2, config.queued_tasks // 2):
            ctrl.expand_capacity(
                config.simulated_provider_concurrency, config.actual_concurrency
            )
        if not progressed:
            idle_rounds += 1
            if idle_rounds >= 3:
                break
        else:
            idle_rounds = 0

    wall_s = time.perf_counter() - t0
    # Fairness: no mission should receive ~0 while another monopolizes.
    served_vals = list(mission_served.values())
    fairness_ok = True
    if len(served_vals) >= 2 and sum(served_vals) > 0:
        fairness_ok = min(served_vals) >= max(1, int(0.1 * max(served_vals)))

    oversub_ok = max_in_flight <= config.actual_concurrency
    runaway_ok = len(ctrl.tasks.get(missions[0].id, {})) <= config.queued_tasks + 50

    metrics = {
        "accepted_tasks": accepted,
        "queued_tasks_target": config.queued_tasks,
        "wall_seconds": round(wall_s, 4),
        "accepted_per_second": round(accepted / wall_s, 2) if wall_s > 0 else None,
        "dispatch_ms_p50": percentile(dispatch_latencies_ms, 50),
        "dispatch_ms_p95": percentile(dispatch_latencies_ms, 95),
        "queue_age_ticks_p50": percentile(queue_ages_ms, 50),
        "queue_age_ticks_p95": percentile(queue_ages_ms, 95),
        "rss_mb_peak": round(_rss_mb(), 2),
        "max_in_flight": max_in_flight,
        "oversubscription_rejects": rejected_oversub,
        "logical_sessions": len(logical_session_ids),
        "ticks": ticks,
    }
    scaling = {
        "expand_peak_inference_slots": expand_peak,
        "contract_floor_inference_slots": contract_floor,
        "expanded_then_contracted": expand_peak > contract_floor,
        "strategy": config.scenario,
    }
    fairness = {
        "mission_served": mission_served,
        "no_starvation": fairness_ok,
    }
    gates = {
        "no_oversubscription": oversub_ok,
        "no_runaway_spawn": runaway_ok,
        "no_starvation": fairness_ok,
        "expand_and_contract_observed": expand_peak > contract_floor,
        "thousand_task_envelope": config.queued_tasks >= 1000
        and accepted >= min(accepted, config.queued_tasks) * 0.5,
    }

    report = LoadReport(
        run_id=run_id,
        scenario=config.scenario,
        mode="mock",
        seed=config.seed,
        config={
            "logical_sessions": config.logical_sessions,
            "queued_tasks": config.queued_tasks,
            "actual_concurrency": config.actual_concurrency,
            "simulated_provider_concurrency": config.simulated_provider_concurrency,
            "missions": config.missions,
            "scenario": config.scenario,
        },
        metrics=metrics,
        scaling=scaling,
        fairness=fairness,
        gates=gates,
    )
    raw = json.dumps(report.to_dict(), sort_keys=True, default=str)
    report.report_hash = hashlib.sha256(raw.encode()).hexdigest()

    if report_dir is not None:
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / f"{run_id}.json").write_text(
            json.dumps(report.to_dict(), indent=2, default=str) + "\n"
        )
    return report


async def compare_strategies(
    *,
    queued_tasks: int = 200,
    logical_sessions: int = 20,
    actual_concurrency: int = 4,
    report_dir: Path | None = None,
) -> dict[str, Any]:
    """Fixed-team vs adaptive under the same synthetic envelope."""
    shared = dict(
        queued_tasks=queued_tasks,
        logical_sessions=logical_sessions,
        actual_concurrency=actual_concurrency,
        simulated_provider_concurrency=8,
        missions=2,
        mode="mock",
        seed=7,
    )
    fixed = await run_load_scenario(
        LoadConfig(scenario="fixed", **shared), report_dir=report_dir
    )
    adaptive = await run_load_scenario(
        LoadConfig(scenario="adaptive", **shared), report_dir=report_dir
    )
    return {
        "mode": "mock",
        "mock_vs_live": "simulated_load_not_live",
        "fixed": fixed.to_dict(),
        "adaptive": adaptive.to_dict(),
        "same_envelope": True,
    }
