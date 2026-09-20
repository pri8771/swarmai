"""V0.2 P29 — evidence-based model router (zero-spend).

Combines P27 capability registry + P28 live benchmark history + task role
requirements to assign planner / worker / verifier models with an explicit
rationale. Never selects paid-blocked or deferred providers when
SWARM_ALLOW_PAID=false.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from swarm.evals.live_benchmark import (
    FAMILY_MAP,
    best_models_by_family,
    list_ollama_models,
    load_latest_live_benchmark,
    select_benchmark_models,
)
from swarm.providers.capability_registry import (
    build_capability_registry,
    routable_providers,
)

# Mission task_family → benchmark family used for evidence lookup.
TASK_TO_BENCHMARK: dict[str, str] = {
    "inspect": "dependency_planning",  # planning
    "implement": "code_generation",  # coding worker
    "verify": "tool_selection",  # specialized / local verifier preference
    "review": "evidence_qa",  # separate reasoning verifier
}

ROLE_ALIASES: dict[str, str] = {
    "planner": "inspect",
    "worker": "implement",
    "verifier": "verify",
    "reviewer": "review",
}

DEFAULT_FALLBACK = "gemma3:4b"


@dataclass
class RouteAssignment:
    role: str
    task_family: str
    benchmark_family: str
    model: str
    route_id: str
    provider_id: str = "ollama"
    cost_policy: str = "zero_spend_ok"
    rationale: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MissionRoutePlan:
    assignments: dict[str, RouteAssignment]
    available_models: list[str]
    swarm_allow_paid: bool
    benchmark_run_id: str | None
    rationale_summary: str

    def model_for(self, task_family: str) -> str:
        a = self.assignments.get(task_family)
        return a.model if a else DEFAULT_FALLBACK

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "0.2.0",
            "swarm_allow_paid": self.swarm_allow_paid,
            "benchmark_run_id": self.benchmark_run_id,
            "available_models": self.available_models,
            "rationale_summary": self.rationale_summary,
            "kit_family_map": FAMILY_MAP,
            "assignments": {k: v.to_dict() for k, v in self.assignments.items()},
            "heterogeneous": len({a.model for a in self.assignments.values()}) >= 2,
        }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _ollama_routable(repo: Path | None = None) -> bool:
    report = build_capability_registry(probe=False, repo=repo)
    for p in routable_providers(report):
        if p.get("provider_id") == "ollama":
            return True
    # Probe-less build may still mark ollama healthy via defaults.
    for p in report.get("providers") or []:
        if p.get("provider_id") == "ollama" and p.get("cost_policy") in {
            "zero_spend_ok",
            "unknown",
        }:
            return True
    return True  # local loopback is always the zero-spend fallback


def _cell_score(cell: dict[str, Any]) -> tuple[float, float]:
    """Higher pass_rate wins; ties break toward lower latency."""
    rate = float(cell.get("pass_rate") or 0.0)
    lat = float(cell.get("latency_ms_p50") or 1e9)
    return rate, -lat


def _pick_model_for_family(
    *,
    benchmark_family: str,
    available: list[str],
    report: dict[str, Any] | None,
    prefer_not: set[str] | None = None,
    prefer_fast: bool = False,
) -> tuple[str, dict[str, Any]]:
    prefer_not = prefer_not or set()
    cells = [
        c
        for c in (report or {}).get("cells") or []
        if c.get("family") == benchmark_family and c.get("model") in available
    ]
    cells = sorted(cells, key=_cell_score, reverse=True)
    # Prefer a different model when diversifying roles, if evidence allows.
    for cell in cells:
        model = str(cell["model"])
        if model in prefer_not and len(cells) > 1:
            continue
        return model, {"source": "benchmark_cell", "cell": cell}
    if prefer_fast:
        # Latency-oriented fallback among available.
        ranked = sorted(
            (
                c
                for c in (report or {}).get("cells") or []
                if c.get("model") in available
            ),
            key=lambda c: float(c.get("latency_ms_p50") or 1e9),
        )
        for cell in ranked:
            model = str(cell["model"])
            if model not in prefer_not or len(available) == 1:
                return model, {"source": "fastest_available", "cell": cell}
    # Global best-by-family map.
    best = best_models_by_family(report)
    if benchmark_family in best and best[benchmark_family] in available:
        model = best[benchmark_family]
        if model not in prefer_not or len(available) == 1:
            return model, {"source": "best_by_family", "model": model}
    # Prefer first unused preferred model.
    preferred = select_benchmark_models(available=available, limit=5)
    for model in preferred:
        if model not in prefer_not:
            return model, {"source": "preferred_available", "model": model}
    model = available[0] if available else DEFAULT_FALLBACK
    return model, {"source": "fallback", "model": model}


def build_mission_route_plan(
    *,
    repo: Path | None = None,
    models: list[str] | None = None,
    roles: list[str] | None = None,
) -> MissionRoutePlan:
    root = repo or _repo_root()
    paid = os.environ.get("SWARM_ALLOW_PAID", "false").lower() in {"1", "true", "yes"}
    if not _ollama_routable(root):
        raise RuntimeError("no_zero_spend_routable_providers")

    available = models or list_ollama_models()
    if not available:
        available = [DEFAULT_FALLBACK]
    report = load_latest_live_benchmark(root)
    # Prefer models that already have live benchmark cells when unconstrained.
    if models is None and report:
        evidenced = []
        for cell in report.get("cells") or []:
            m = str(cell.get("model") or "")
            if m and m in available and m not in evidenced:
                evidenced.append(m)
        if evidenced:
            available = evidenced
        else:
            available = select_benchmark_models(available=available, limit=4) or available[:3]
    elif models is None:
        available = select_benchmark_models(available=available, limit=4) or available[:3]

    run_id = (report or {}).get("run_id") if report else None

    task_families = roles or ["inspect", "implement", "verify", "review"]
    # Normalize aliases.
    normalized: list[str] = []
    for r in task_families:
        normalized.append(ROLE_ALIASES.get(r, r))

    assignments: dict[str, RouteAssignment] = {}
    used: set[str] = set()
    for fam in normalized:
        bench = TASK_TO_BENCHMARK.get(fam, "code_generation")
        prefer_fast = fam in {"verify", "inspect"}
        # Diversify: workers vs verifiers should differ when possible.
        avoid = set(used) if fam in {"implement", "review", "verify"} else set()
        if fam == "implement" and "inspect" in assignments:
            avoid.add(assignments["inspect"].model)
        model, evidence = _pick_model_for_family(
            benchmark_family=bench,
            available=available,
            report=report,
            prefer_not=avoid if len(available) > 1 else set(),
            prefer_fast=prefer_fast,
        )
        used.add(model)
        role = {
            "inspect": "planner",
            "implement": "worker",
            "verify": "verifier",
            "review": "reviewer",
        }.get(fam, fam)
        rationale = (
            f"{role}/{fam} → benchmark family {bench}; "
            f"selected {model} via {evidence.get('source')} "
            f"under zero_spend_ok (SWARM_ALLOW_PAID={paid})"
        )
        assignments[fam] = RouteAssignment(
            role=role,
            task_family=fam,
            benchmark_family=bench,
            model=model,
            route_id=f"rt_ollama_{model}",
            provider_id="ollama",
            cost_policy="zero_spend_ok" if not paid else "paid_allowed",
            rationale=rationale,
            evidence=evidence,
        )

    distinct = {a.model for a in assignments.values()}
    summary = (
        f"Evidence router assigned {len(assignments)} roles across "
        f"{len(distinct)} model(s): "
        + ", ".join(f"{a.role}={a.model}" for a in assignments.values())
    )
    return MissionRoutePlan(
        assignments=assignments,
        available_models=available,
        swarm_allow_paid=paid,
        benchmark_run_id=str(run_id) if run_id else None,
        rationale_summary=summary,
    )


def save_route_plan(plan: MissionRoutePlan, *, repo: Path | None = None) -> Path:
    root = repo or _repo_root()
    path = root / "var" / "routing" / "latest_mission_route_plan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan.to_dict(), indent=2, default=str) + "\n")
    return path
