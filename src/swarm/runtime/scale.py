"""V0.3 P34/P35 — lightweight agents, scale path, dedup, consensus, isolation."""

from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.enums import RiskLevel
from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.contracts.mission import SizeFeatures, TaskSpec
from swarm.envfile import load_repo_dotenv
from swarm.mission.inference import local_chat
from swarm.runtime.backpressure import make_scale_scheduler


@dataclass
class LightAgent:
    """Minimal agent identity — no heavy session/session-store per agent."""

    agent_id: str
    role: str
    lane: int = 0
    model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentResult:
    agent_id: str
    task_id: str
    ok: bool
    summary: str
    artifact_hash: str | None = None
    error_class: str | None = None
    latency_ms: float = 0.0
    duplicate_of: str | None = None
    isolated: bool = False
    cost_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScaleMissionReport:
    run_id: str
    goal: str
    agent_count: int
    task_count: int
    completed: int
    failed: int
    duplicates_suppressed: int
    consensus: dict[str, Any]
    scheduler_stats: dict[str, Any]
    results: list[AgentResult] = field(default_factory=list)
    total_cost_usd: float = 0.0
    runtime_ms: float = 0.0
    mock_vs_live: str = "live_local_zero_cost_scale"
    report_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        body = {
            "run_id": self.run_id,
            "goal": self.goal,
            "agent_count": self.agent_count,
            "task_count": self.task_count,
            "completed": self.completed,
            "failed": self.failed,
            "duplicates_suppressed": self.duplicates_suppressed,
            "consensus": self.consensus,
            "scheduler_stats": self.scheduler_stats,
            "total_cost_usd": self.total_cost_usd,
            "runtime_ms": round(self.runtime_ms, 2),
            "mock_vs_live": self.mock_vs_live,
            "generated_at": utc_now().isoformat(),
            "results": [r.to_dict() for r in self.results],
            "report_hash": self.report_hash,
        }
        return body


def _file_fingerprint(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def _collect_targets(repo: Path, *, limit: int) -> list[Path]:
    roots = [repo / "src" / "swarm", repo / "sandbox"]
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            files.append(path)
            if len(files) >= limit:
                return files
    return files


def detect_duplicate_work(
    pending: list[tuple[LightAgent, TaskSpec, Path]],
) -> tuple[list[tuple[LightAgent, TaskSpec, Path]], int]:
    """Suppress duplicate targets (same relative path) — keep first agent."""
    seen: set[str] = set()
    unique: list[tuple[LightAgent, TaskSpec, Path]] = []
    dupes = 0
    for agent, task, path in pending:
        key = str(path)
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        unique.append((agent, task, path))
    return unique, dupes


def bounded_consensus(results: list[AgentResult]) -> dict[str, Any]:
    """Majority ok among non-isolated results; critics = failed/isolated count."""
    active = [r for r in results if not r.isolated]
    if not active:
        return {
            "decision": "reject",
            "reason": "all_isolated",
            "votes_accept": 0,
            "votes_reject": 0,
        }
    accept = sum(1 for r in active if r.ok)
    reject = len(active) - accept
    decision = "accept" if accept > reject else "reject"
    return {
        "decision": decision,
        "votes_accept": accept,
        "votes_reject": reject,
        "critics": reject,
        "isolated": sum(1 for r in results if r.isolated),
        "reason": "majority_ok" if decision == "accept" else "majority_fail_or_tie",
    }


def isolate_failures(results: list[AgentResult]) -> list[AgentResult]:
    """Mark correlated error classes as isolated bad branches."""
    by_err: dict[str, int] = {}
    for r in results:
        if r.error_class:
            by_err[r.error_class] = by_err.get(r.error_class, 0) + 1
    correlated = {k for k, n in by_err.items() if n >= 3}
    out: list[AgentResult] = []
    for r in results:
        if r.error_class and r.error_class in correlated:
            out.append(
                AgentResult(
                    **{
                        **r.to_dict(),
                        "isolated": True,
                        "summary": f"isolated:{r.summary}",
                    }
                )
            )
        else:
            out.append(r)
    return out


def _execute_agent(
    agent: LightAgent,
    task: TaskSpec,
    path: Path,
    repo: Path,
    *,
    use_model: bool,
) -> AgentResult:
    started = time.perf_counter()
    try:
        digest = _file_fingerprint(path)
        rel = str(path.relative_to(repo))
        summary = f"fingerprinted:{rel}:{digest[:12]}"
        cost = 0.0
        if use_model and agent.role == "supervisor":
            # One bounded live call for supervisor only — keeps scale cheap.
            chat = local_chat(
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Reply with OK if this path looks like python source: {rel}"
                        ),
                    }
                ],
                model=agent.model or "gemma3:4b",
                max_tokens=8,
                repo_root=repo,
            )
            cost = chat.cost_usd
            if not chat.ok:
                return AgentResult(
                    agent_id=agent.agent_id,
                    task_id=task.id,
                    ok=False,
                    summary="supervisor_inference_failed",
                    error_class=chat.error or "inference_error",
                    latency_ms=(time.perf_counter() - started) * 1000.0,
                    cost_usd=0.0,
                )
            summary = f"supervisor_ok:{rel}"
        return AgentResult(
            agent_id=agent.agent_id,
            task_id=task.id,
            ok=True,
            summary=summary,
            artifact_hash=digest,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            cost_usd=cost,
        )
    except Exception as exc:  # noqa: BLE001
        return AgentResult(
            agent_id=agent.agent_id,
            task_id=task.id,
            ok=False,
            summary="agent_exception",
            error_class=type(exc).__name__,
            latency_ms=(time.perf_counter() - started) * 1000.0,
        )


def run_scale_mission(
    *,
    repo: Path,
    goal: str = "Scale fingerprint swarm across python modules",
    agent_count: int = 48,
    max_concurrency: int = 8,
    use_supervisor_model: bool = True,
    out_dir: Path | None = None,
) -> ScaleMissionReport:
    """Real scale path: dozens of lightweight agents with queue + dedup + consensus."""
    load_repo_dotenv(repo)
    run_id = new_id("scale_")
    started = time.perf_counter()
    targets = _collect_targets(repo, limit=agent_count)
    # If fewer files than agents, duplicate intentionally then dedup to prove suppression.
    pending: list[tuple[LightAgent, TaskSpec, Path]] = []
    mission = sample_mission().model_copy(update={"objective": goal, "id": new_id("mission_")})
    for i in range(agent_count):
        path = targets[i % max(1, len(targets))] if targets else repo / "README.md"
        role = "supervisor" if i == 0 else ("reviewer" if i == agent_count - 1 else "worker")
        agent = LightAgent(
            agent_id=new_id("ag_"),
            role=role,
            lane=i,
            model="gemma3:4b" if role == "supervisor" else None,
        )
        if role == "worker":
            family = "implement"
        elif role == "supervisor":
            family = "supervise"
        else:
            family = "review"
        task = sample_task(mission_id=mission.id).model_copy(
            update={
                "id": new_id("tsk_"),
                "objective": f"{role} lane {i} on {path.name}",
                "task_family": family,
                "size_features": SizeFeatures(
                    file_count=1, risk_level=RiskLevel.LOW, source_complexity="scale"
                ),
            }
        )
        pending.append((agent, task, path))

    # Inject deliberate duplicates for P35 proof when we have targets.
    if targets:
        pending.append(
            (
                LightAgent(agent_id=new_id("ag_"), role="worker", lane=999),
                sample_task(mission_id=mission.id).model_copy(
                    update={"id": new_id("tsk_"), "objective": "dup"}
                ),
                targets[0],
            )
        )

    unique, dupes = detect_duplicate_work(pending)
    sched = make_scale_scheduler(max_concurrency=max_concurrency, ollama_in_flight=max_concurrency)
    for _agent, task, _path in unique:
        sched.enqueue(task, provider_id="ollama", timeout_s=60.0)

    # Drain via backpressure dispatcher in waves.
    results: list[AgentResult] = []
    remaining = {t.id: (a, t, p) for a, t, p in unique}
    waves = 0
    with ThreadPoolExecutor(max_workers=max_concurrency) as pool:
        while remaining and waves < 200:
            waves += 1
            dispatched, _expl = sched.dispatch(
                mission, inference_slots=max_concurrency, worker_slots=max_concurrency
            )
            if not dispatched:
                # Nothing runnable — clear timeouts already counted; break if empty queue.
                if sched.stats()["queue_depth"] == 0:
                    break
                # Force-progress: pop one without quota to avoid deadlock in tests.
                item = None
                if sched.queue:
                    item = sched.queue.popleft()
                if item is None:
                    break
                dispatched = [item]
            futures = []
            for item in dispatched:
                trip = remaining.pop(item.task.id, None)
                if trip is None:
                    sched.complete(item.provider_id)
                    continue
                agent, task, path = trip
                futures.append(
                    pool.submit(
                        _execute_agent,
                        agent,
                        task,
                        path,
                        repo,
                        use_model=use_supervisor_model,
                    )
                )
            for fut in as_completed(futures):
                result = fut.result()
                results.append(result)
                sched.complete("ollama")

    results = isolate_failures(results)
    consensus = bounded_consensus(results)
    report = ScaleMissionReport(
        run_id=run_id,
        goal=goal,
        agent_count=agent_count,
        task_count=len(unique),
        completed=sum(1 for r in results if r.ok and not r.isolated),
        failed=sum(1 for r in results if not r.ok or r.isolated),
        duplicates_suppressed=dupes,
        consensus=consensus,
        scheduler_stats={**sched.stats(), "waves": waves},
        results=results,
        total_cost_usd=sum(r.cost_usd for r in results),
        runtime_ms=(time.perf_counter() - started) * 1000.0,
    )
    raw = json.dumps(report.to_dict(), sort_keys=True, default=str)
    report.report_hash = hashlib.sha256(raw.encode()).hexdigest()
    dest = out_dir or (repo / "var" / "reports" / "scale")
    dest.mkdir(parents=True, exist_ok=True)
    (dest / f"{run_id}.json").write_text(
        json.dumps(report.to_dict(), indent=2, default=str) + "\n"
    )
    (dest / "latest_scale_mission.json").write_text(
        json.dumps(report.to_dict(), indent=2, default=str) + "\n"
    )
    return report
