"""EVAL-131 denser holdout case selection (no model calls)."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from swarm.evals.live_benchmark import DEFAULT_FAMILIES, _select_cases


def _dataset() -> Path:
    return Path(__file__).resolve().parents[2] / "benchmarks" / "starter.jsonl"


def test_select_cases_allows_five_holdout_per_cell() -> None:
    cases = _select_cases(
        _dataset(),
        families=DEFAULT_FAMILIES,
        sizes=["S"],
        max_cases=30,
        max_per_cell=5,
    )
    assert len(cases) == 30
    counts = Counter((c.family, c.size) for c in cases)
    assert all(v == 5 for v in counts.values())
    assert all(c.split == "holdout" for c in cases)


def test_select_cases_respects_lower_cap() -> None:
    cases = _select_cases(
        _dataset(), families=DEFAULT_FAMILIES, sizes=["S"], max_cases=12, max_per_cell=2
    )
    assert len(cases) == 12
    counts = Counter((c.family, c.size) for c in cases)
    assert all(v == 2 for v in counts.values())


def test_select_cases_prefers_holdout_before_calibration() -> None:
    cases = _select_cases(
        _dataset(), families=["code_generation"], sizes=["S"], max_cases=2
    )
    assert len(cases) == 2
    assert all(c.split == "holdout" for c in cases)


def test_dataset_has_five_holdouts_per_cell() -> None:
    from swarm.evals.dataset import load_dataset

    cases = load_dataset(_dataset())
    counts = Counter(
        (c.family, c.size) for c in cases if c.split == "holdout"
    )
    assert counts
    assert min(counts.values()) >= 5
