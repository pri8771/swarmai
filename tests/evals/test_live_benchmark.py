"""P28 live benchmark helpers (offline unit coverage)."""

from __future__ import annotations

from swarm.evals.live_benchmark import (
    BenchmarkTrial,
    FAMILY_MAP,
    _aggregate_cells,
    best_models_by_family,
    select_benchmark_models,
)


def test_family_map_covers_kit_roles() -> None:
    assert set(FAMILY_MAP) >= {
        "planning",
        "coding",
        "extraction",
        "reasoning",
        "review",
        "summarization",
    }


def test_select_benchmark_models_prefers_known() -> None:
    available = ["gemma3:4b", "deepseek-coder-v2:16b", "qwen3.5:4b", "other:1b"]
    chosen = select_benchmark_models(available=available, limit=2)
    assert chosen == ["gemma3:4b", "qwen3.5:4b"]


def test_select_benchmark_models_respects_request() -> None:
    available = ["gemma3:4b", "qwen3.5:9b"]
    chosen = select_benchmark_models(
        available=available, requested=["qwen3.5:9b", "missing"], limit=3
    )
    assert chosen == ["qwen3.5:9b"]


def test_aggregate_cells_and_best_by_family() -> None:
    trials = [
        BenchmarkTrial(
            case_id="a",
            family="extraction",
            size="S",
            model="m1",
            route_id="rt_m1",
            correct=True,
            latency_ms=100,
            detail="ok",
        ),
        BenchmarkTrial(
            case_id="b",
            family="extraction",
            size="S",
            model="m1",
            route_id="rt_m1",
            correct=False,
            latency_ms=200,
            detail="bad",
        ),
        BenchmarkTrial(
            case_id="c",
            family="extraction",
            size="S",
            model="m2",
            route_id="rt_m2",
            correct=True,
            latency_ms=50,
            detail="ok",
        ),
        BenchmarkTrial(
            case_id="d",
            family="extraction",
            size="S",
            model="m2",
            route_id="rt_m2",
            correct=True,
            latency_ms=60,
            detail="ok",
        ),
    ]
    cells = _aggregate_cells(trials)
    assert len(cells) == 2
    report = {"cells": cells}
    best = best_models_by_family(report)
    assert best["extraction"] == "m2"
