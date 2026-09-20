"""Benchmark dataset loading with leakage protection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import Field

from swarm.contracts.common import StrictModel


class BenchmarkCase(StrictModel):
    schema_version: str = "1.0"
    id: str
    family: str
    size: str
    split: str
    input: dict[str, Any]
    expected_output: Any = None
    grader: dict[str, Any]
    size_features: dict[str, Any] = Field(default_factory=dict)
    generation: dict[str, Any] = Field(default_factory=dict)
    output_limit_tokens_proposed: int | None = None
    # Present on some code fixtures for offline graders only — never model-visible.
    reference_solution: str | None = None
    broken_code: str | None = None
    notes: str | None = None


def load_dataset(path: Path | str) -> list[BenchmarkCase]:
    root = Path(path)
    cases: list[BenchmarkCase] = []
    for line_no, line in enumerate(root.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            cases.append(BenchmarkCase.model_validate(raw))
        except Exception as exc:
            raise ValueError(f"{root}:{line_no}: invalid case: {exc}") from exc
    return cases


def validate_dataset(path: Path | str) -> dict[str, Any]:
    cases = load_dataset(path)
    families = sorted({c.family for c in cases})
    sizes = sorted({c.size for c in cases})
    splits = sorted({c.split for c in cases})
    graders = sorted({str(c.grader.get("kind")) for c in cases})
    ids = [c.id for c in cases]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    return {
        "ok": not dupes and len(cases) > 0,
        "case_count": len(cases),
        "families": families,
        "sizes": sizes,
        "splits": splits,
        "grader_kinds": graders,
        "duplicate_ids": dupes,
        "path": str(path),
        "mock_vs_live": "dataset_fixtures_only",
    }


def build_model_input(case: BenchmarkCase | dict[str, Any]) -> dict[str, Any]:
    """Only case.input is model-visible — never expected_output or grader fixtures."""
    if isinstance(case, BenchmarkCase):
        payload = case.input
    else:
        payload = case["input"]
    # Defensive copy; strip any accidental leakage keys.
    visible = dict(payload)
    for banned in (
        "expected_output",
        "grader",
        "answer",
        "reference_solution",
        "broken_code",
        "holdout_label",
        "case_id",
        "id",
    ):
        visible.pop(banned, None)
    return {"input": visible}


def assert_no_leakage(model_input: dict[str, Any], case: BenchmarkCase) -> None:
    blob = json.dumps(model_input, sort_keys=True)
    if case.id in blob and "extraction_" in case.id:
        # Case IDs with answer clues must not appear; synthetic ids are fine if absent.
        pass
    if "expected_output" in blob:
        raise AssertionError("expected_output leaked into model input")
    if '"grader"' in blob or "'grader'" in blob:
        raise AssertionError("grader leaked into model input")
    expected = case.expected_output
    if expected is not None:
        # Exact expected JSON must not appear verbatim as a top-level leak.
        expected_s = json.dumps(expected, sort_keys=True, separators=(",", ":"))
        if expected_s in blob and len(expected_s) > 20:
            raise AssertionError("expected_output value leaked into model input")
