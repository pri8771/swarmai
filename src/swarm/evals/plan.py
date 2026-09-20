"""Bounded evaluation plans and expected consumption estimates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from swarm.evals.dataset import BenchmarkCase, load_dataset


@dataclass
class EvalPlan:
    suite: str
    mode: str
    cells: list[dict[str, Any]]
    case_ids: list[str]
    expected_requests: int
    expected_completion_tokens: int
    remaining_note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite,
            "mode": self.mode,
            "mock_vs_live": "mock" if self.mode == "mock" else "live_requires_broker_envelope",
            "cell_count": len(self.cells),
            "case_count": len(self.case_ids),
            "expected_requests": self.expected_requests,
            "expected_completion_tokens": self.expected_completion_tokens,
            "cells": self.cells,
            "case_ids": self.case_ids,
            "remaining_note": self.remaining_note,
        }


def build_plan(
    dataset_path: Path | str,
    *,
    suite: str = "starter",
    mode: str = "mock",
    max_cases: int = 16,
    families: list[str] | None = None,
    sizes: list[str] | None = None,
    prefer_holdout: bool = True,
    completion_tokens_per_case: int = 128,
) -> EvalPlan:
    cases = load_dataset(dataset_path)
    if families:
        cases = [c for c in cases if c.family in families]
    if sizes:
        cases = [c for c in cases if c.size in sizes]
    # High-value set: one holdout then calibration per cell, bounded.
    selected: list[BenchmarkCase] = []
    cells: dict[tuple[str, str], int] = {}
    ordered = sorted(
        cases,
        key=lambda c: (0 if c.split == "holdout" else 1, c.family, c.size, c.id)
        if prefer_holdout
        else (c.family, c.size, c.id),
    )
    for case in ordered:
        if len(selected) >= max_cases:
            break
        key = (case.family, case.size)
        # Cap per cell to avoid burning quota on one family.
        if cells.get(key, 0) >= 2:
            continue
        selected.append(case)
        cells[key] = cells.get(key, 0) + 1

    cell_rows = [
        {"family": f, "size": s, "cases": n} for (f, s), n in sorted(cells.items())
    ]
    expected_requests = len(selected)
    expected_tokens = expected_requests * completion_tokens_per_case
    note = (
        "mock plan only — no provider calls"
        if mode == "mock"
        else "live plan must reserve via broker benchmark envelope before dispatch"
    )
    return EvalPlan(
        suite=suite,
        mode=mode,
        cells=cell_rows,
        case_ids=[c.id for c in selected],
        expected_requests=expected_requests,
        expected_completion_tokens=expected_tokens,
        remaining_note=note,
    )


def compare_routes(
    *,
    direct_tokens: int,
    direct_quality: float,
    small_tokens: int,
    verify_tokens: int,
    small_quality: float,
) -> dict[str, Any]:
    """Compare direct capable-model vs small-model + verification overhead."""
    small_total = small_tokens + verify_tokens
    return {
        "direct": {"tokens": direct_tokens, "quality": direct_quality},
        "small_plus_verify": {
            "tokens": small_total,
            "quality": small_quality,
            "overhead_tokens": verify_tokens,
        },
        "prefer": (
            "direct"
            if direct_quality >= small_quality and direct_tokens <= small_total
            else "small_plus_verify"
            if small_quality >= direct_quality and small_total < direct_tokens
            else "tie_or_context_dependent"
        ),
    }
