"""P29 evidence-based router unit tests."""

from __future__ import annotations

import json
from pathlib import Path

from swarm.evals.evidence_router import (
    TASK_TO_BENCHMARK,
    build_mission_route_plan,
    save_route_plan,
)


def test_task_benchmark_map_covers_mission_roles() -> None:
    assert set(TASK_TO_BENCHMARK) >= {"inspect", "implement", "verify", "review"}


def test_build_route_plan_heterogeneous(tmp_path: Path, monkeypatch) -> None:
    # Seed a synthetic benchmark report favoring different models per family.
    # Fail-closed ollama probe is not under test here — stub local readiness.
    monkeypatch.setattr(
        "swarm.evals.evidence_router._ollama_routable", lambda repo=None: True
    )
    qual = tmp_path / "var" / "reports" / "qualification"
    qual.mkdir(parents=True)
    report = {
        "run_id": "run_test",
        "cells": [
            {
                "family": "dependency_planning",
                "size": "M",
                "model": "gemma3:4b",
                "pass_rate": 1.0,
                "latency_ms_p50": 1000,
            },
            {
                "family": "dependency_planning",
                "size": "M",
                "model": "qwen3.5:4b",
                "pass_rate": 0.5,
                "latency_ms_p50": 2000,
            },
            {
                "family": "code_generation",
                "size": "M",
                "model": "qwen3.5:4b",
                "pass_rate": 1.0,
                "latency_ms_p50": 1500,
            },
            {
                "family": "code_generation",
                "size": "M",
                "model": "gemma3:4b",
                "pass_rate": 0.0,
                "latency_ms_p50": 1200,
            },
            {
                "family": "tool_selection",
                "size": "M",
                "model": "gemma3:4b",
                "pass_rate": 0.5,
                "latency_ms_p50": 800,
            },
            {
                "family": "evidence_qa",
                "size": "M",
                "model": "qwen3.5:4b",
                "pass_rate": 0.5,
                "latency_ms_p50": 900,
            },
        ],
    }
    (qual / "latest_live_benchmark.json").write_text(json.dumps(report) + "\n")
    plan = build_mission_route_plan(
        repo=tmp_path, models=["gemma3:4b", "qwen3.5:4b"]
    )
    assert plan.assignments["inspect"].model == "gemma3:4b"
    assert plan.assignments["implement"].model == "qwen3.5:4b"
    assert plan.to_dict()["heterogeneous"] is True
    assert plan.swarm_allow_paid is False
    path = save_route_plan(plan, repo=tmp_path)
    assert path.exists()
    assert "planner" in plan.rationale_summary.lower() or "inspect" in plan.rationale_summary
