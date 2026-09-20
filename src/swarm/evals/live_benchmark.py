"""V0.2 P28 — real multi-model qualification benchmarks (zero-spend).

Runs starter-dataset cases against available local Ollama models, grades with
deterministic graders, and persists cell-level results for the evidence-based
router. Never calls paid cloud inference under SWARM_ALLOW_PAID=false.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.workspace import EvalResult
from swarm.envfile import load_repo_dotenv
from swarm.evals.dataset import BenchmarkCase, build_model_input, load_dataset
from swarm.evals.graders import grade_case
from swarm.evals.profiles import ProfileStore
from swarm.evals.wilson import wilson_lower_bound
from swarm.mission.brokered_inference import (
    brokered_local_chat_sync,
    build_local_mission_broker,
)

# Kit task families → starter dataset families.
FAMILY_MAP: dict[str, str] = {
    "planning": "dependency_planning",
    "coding": "code_generation",
    "extraction": "extraction",
    "reasoning": "evidence_qa",
    "review": "tool_selection",
    "summarization": "context_compaction",
}

DEFAULT_FAMILIES = list(FAMILY_MAP.values())
DEFAULT_SIZES = ["S", "M"]
# Prefer smaller local models for bounded zero-spend dogfood; skip huge ones by default.
PREFERRED_MODELS = ("gemma3:4b", "qwen3.5:4b", "qwen3.5:9b", "qwen2.5-coder:14b")


@dataclass
class BenchmarkTrial:
    case_id: str
    family: str
    size: str
    model: str
    route_id: str
    correct: bool
    latency_ms: float
    detail: str
    cost_usd: float = 0.0
    error: str | None = None
    output_preview: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "family": self.family,
            "size": self.size,
            "model": self.model,
            "route_id": self.route_id,
            "correct": self.correct,
            "latency_ms": round(self.latency_ms, 2),
            "detail": self.detail,
            "cost_usd": self.cost_usd,
            "error": self.error,
            "output_preview": self.output_preview[:500],
        }


@dataclass
class LiveBenchmarkReport:
    run_id: str
    purpose: str
    models: list[str]
    case_ids: list[str]
    trials: list[BenchmarkTrial] = field(default_factory=list)
    cells: list[dict[str, Any]] = field(default_factory=list)
    profiles_summary: dict[str, Any] = field(default_factory=dict)
    total_cost_usd: float = 0.0
    mock_vs_live: str = "live_local_zero_cost"
    report_hash: str | None = None
    family_map: dict[str, str] = field(default_factory=lambda: dict(FAMILY_MAP))

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "purpose": self.purpose,
            "schema_version": "0.2.0",
            "generated_at": utc_now().isoformat(),
            "models": self.models,
            "case_ids": self.case_ids,
            "trial_count": len(self.trials),
            "passed": sum(1 for t in self.trials if t.correct),
            "failed": sum(1 for t in self.trials if not t.correct and not t.error),
            "errors": sum(1 for t in self.trials if t.error),
            "total_cost_usd": self.total_cost_usd,
            "mock_vs_live": self.mock_vs_live,
            "family_map": self.family_map,
            "cells": self.cells,
            "profiles_summary": self.profiles_summary,
            "trials": [t.to_dict() for t in self.trials],
            "report_hash": self.report_hash,
            "swarm_allow_paid": os.environ.get("SWARM_ALLOW_PAID", "false"),
            "note": (
                "Live Ollama benchmarks only — cloud paid inference blocked; "
                "sparse cells remain honest (no invented rankings)"
            ),
        }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def list_ollama_models(*, base_url: str = "http://127.0.0.1:11434") -> list[str]:
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return [str(m.get("name") or "") for m in data.get("models") or [] if m.get("name")]
    except Exception:  # noqa: BLE001 — soft failure for selection
        return []


def select_benchmark_models(
    *,
    available: list[str] | None = None,
    requested: list[str] | None = None,
    limit: int = 3,
) -> list[str]:
    have = available if available is not None else list_ollama_models()
    if requested:
        return [m for m in requested if m in have][:limit]
    chosen: list[str] = []
    for pref in PREFERRED_MODELS:
        if pref in have and pref not in chosen:
            chosen.append(pref)
        if len(chosen) >= limit:
            break
    if not chosen and have:
        chosen = have[:limit]
    return chosen


def _case_prompt(case: BenchmarkCase) -> str:
    visible = build_model_input(case)["input"]
    if isinstance(visible.get("prompt"), str):
        return str(visible["prompt"])
    return json.dumps(visible)


def _strip_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _select_cases(
    dataset: Path,
    *,
    families: list[str],
    sizes: list[str],
    max_cases: int,
) -> list[BenchmarkCase]:
    """Round-robin across families/sizes so planning→summarization are all covered."""
    cases = load_dataset(dataset)
    cases = [c for c in cases if c.family in families and c.size in sizes]
    # Prefer holdout, then calibration; keep order stable within cell.
    cases = sorted(
        cases,
        key=lambda c: (0 if c.split == "holdout" else 1, c.family, c.size, c.id),
    )
    selected: list[BenchmarkCase] = []
    seen_cells: dict[tuple[str, str], int] = {}
    # Pass 1: one case per family (any allowed size).
    seen_family: set[str] = set()
    for case in cases:
        if case.family in seen_family:
            continue
        selected.append(case)
        seen_family.add(case.family)
        seen_cells[(case.family, case.size)] = 1
        if len(selected) >= max_cases:
            return selected
    # Pass 2: fill remaining budget up to 1–2 per cell.
    for case in cases:
        if case in selected:
            continue
        key = (case.family, case.size)
        if seen_cells.get(key, 0) >= 1:
            continue
        selected.append(case)
        seen_cells[key] = seen_cells.get(key, 0) + 1
        if len(selected) >= max_cases:
            break
    return selected


def _aggregate_cells(trials: list[BenchmarkTrial]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str, str], list[BenchmarkTrial]] = {}
    for t in trials:
        buckets.setdefault((t.family, t.size, t.model), []).append(t)
    cells: list[dict[str, Any]] = []
    for (family, size, model), rows in sorted(buckets.items()):
        n = len(rows)
        passes = sum(1 for r in rows if r.correct)
        errors = sum(1 for r in rows if r.error)
        latencies = [r.latency_ms for r in rows]
        latencies.sort()
        p50 = latencies[len(latencies) // 2] if latencies else None
        lower = wilson_lower_bound(passes, n) if n else None
        state = "provisional" if n >= 2 else "untested" if n == 0 else "provisional"
        if n == 1:
            state = "provisional"
        cells.append(
            {
                "family": family,
                "size": size,
                "model": model,
                "route_id": f"rt_ollama_{model}",
                "sample_count": n,
                "pass_count": passes,
                "error_count": errors,
                "wilson_lower": lower,
                "latency_ms_p50": p50,
                "error_rate": (errors / n) if n else None,
                "pass_rate": (passes / n) if n else None,
                "state": state,
                "cost_usd": 0.0,
            }
        )
    return cells


def run_live_benchmarks(
    *,
    repo: Path | None = None,
    dataset: Path | None = None,
    models: list[str] | None = None,
    families: list[str] | None = None,
    sizes: list[str] | None = None,
    max_cases: int = 8,
    max_tokens: int = 600,
    purpose: str = "v0.2_p28_model_qualification",
    out_dir: Path | None = None,
) -> LiveBenchmarkReport:
    root = repo or _repo_root()
    load_repo_dotenv(root)
    if os.environ.get("SWARM_ALLOW_PAID", "false").lower() in {"1", "true", "yes"}:
        # Still prefer local for this packet; paid cloud stays opt-in elsewhere.
        pass

    ds = dataset or (root / "benchmarks" / "starter.jsonl")
    fams = families or DEFAULT_FAMILIES
    sz = sizes or DEFAULT_SIZES
    selected_models = select_benchmark_models(requested=models, limit=3)
    if not selected_models:
        raise RuntimeError(
            "no_ollama_models_available: start Ollama and pull at least one model "
            f"(preferred: {', '.join(PREFERRED_MODELS[:3])})"
        )

    cases = _select_cases(ds, families=fams, sizes=sz, max_cases=max_cases)
    if not cases:
        raise RuntimeError("no_benchmark_cases_selected")

    store = ProfileStore()
    trials: list[BenchmarkTrial] = []
    # G12: every model call goes through the shared broker (local zero-spend).
    broker = build_local_mission_broker(
        repo_root=root,
        models=list(selected_models),
        request_limit=max(50, len(selected_models) * len(cases) + 10),
    )

    for model in selected_models:
        route_id = f"rt_ollama_{model}"
        for case in cases:
            prompt = _case_prompt(case)
            started = time.perf_counter()
            result = brokered_local_chat_sync(
                broker=broker,
                messages=[{"role": "user", "content": prompt}],
                model=model,
                max_tokens=max_tokens,
                project_id="proj_eval",
                purpose="evaluation",
            )
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            if not result.ok:
                trials.append(
                    BenchmarkTrial(
                        case_id=case.id,
                        family=case.family,
                        size=case.size,
                        model=model,
                        route_id=route_id,
                        correct=False,
                        latency_ms=elapsed_ms,
                        detail="inference_error",
                        cost_usd=0.0,
                        error=result.error or "empty_response",
                    )
                )
                continue
            raw_out = result.text
            graded_out: Any = raw_out
            if case.grader.get("kind") == "python_unit":
                graded_out = _strip_fences(raw_out)
            elif case.grader.get("kind") in {"json_exact", "topological_order"}:
                graded_out = _strip_fences(raw_out)
            grade = grade_case(case, graded_out)
            trials.append(
                BenchmarkTrial(
                    case_id=case.id,
                    family=case.family,
                    size=case.size,
                    model=model,
                    route_id=route_id,
                    correct=grade.correct,
                    latency_ms=elapsed_ms,
                    detail=grade.detail,
                    cost_usd=0.0,
                    output_preview=raw_out[:500],
                )
            )
            store.record_result(
                EvalResult(
                    distinct_case_id=case.id,
                    split=case.split,
                    route_fingerprint=route_id,
                    model_fingerprint=model,
                    exact_prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()[:16],
                    outcome="pass" if grade.correct else "fail",
                    grader_version="1",
                    correctness=grade.correct,
                    policy_violation=grade.policy_violation,
                    latency_ms=int(elapsed_ms),
                    score_components=dict(grade.score_components),
                ),
                task_family=case.family,
                size_band=case.size,
                dataset_version="starter-v1",
                model_revision=model,
                simulated=False,
            )

    cells = _aggregate_cells(trials)
    report = LiveBenchmarkReport(
        run_id=new_id("run_"),
        purpose=purpose,
        models=selected_models,
        case_ids=[c.id for c in cases],
        trials=trials,
        cells=cells,
        profiles_summary=store.summary(),
        total_cost_usd=0.0,
    )
    raw = json.dumps(report.to_dict(), sort_keys=True, default=str)
    report.report_hash = hashlib.sha256(raw.encode()).hexdigest()

    dest = out_dir or (root / "var" / "reports" / "qualification")
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{report.run_id}.json"
    path.write_text(json.dumps(report.to_dict(), indent=2, default=str) + "\n")
    # Also write a stable latest pointer for the router (P29).
    (dest / "latest_live_benchmark.json").write_text(
        json.dumps(report.to_dict(), indent=2, default=str) + "\n"
    )
    # Persist profiles snapshot for routing evidence.
    profiles_path = dest / f"{report.run_id}_profiles.json"
    profiles_path.write_text(
        json.dumps(
            {
                "run_id": report.run_id,
                "summary": store.summary(),
                "profiles": [p.model_dump(mode="json") for p in store.profiles.values()],
            },
            indent=2,
            default=str,
        )
        + "\n"
    )
    return report


def load_latest_live_benchmark(repo: Path | None = None) -> dict[str, Any] | None:
    root = repo or _repo_root()
    path = root / "var" / "reports" / "qualification" / "latest_live_benchmark.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return data if isinstance(data, dict) else None


def best_models_by_family(report: dict[str, Any] | None = None) -> dict[str, str]:
    """Pick highest pass_rate model per family (ties → lower latency)."""
    data = report or load_latest_live_benchmark()
    if not data:
        return {}
    best: dict[str, tuple[float, float, str]] = {}
    for cell in data.get("cells") or []:
        family = str(cell.get("family") or "")
        model = str(cell.get("model") or "")
        if not family or not model:
            continue
        rate = float(cell.get("pass_rate") or 0.0)
        lat = float(cell.get("latency_ms_p50") or 1e9)
        prev = best.get(family)
        if prev is None or rate > prev[0] or (rate == prev[0] and lat < prev[1]):
            best[family] = (rate, lat, model)
    return {fam: trip[2] for fam, trip in best.items()}
