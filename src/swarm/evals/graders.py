"""Deterministic graders for benchmark cases."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from swarm.evals.dataset import BenchmarkCase
from swarm.tools.sandbox_runner import IsolatedCodeRunner


class GradeResult:
    def __init__(
        self,
        *,
        correct: bool,
        policy_violation: bool = False,
        detail: str = "",
        score_components: dict[str, float] | None = None,
    ) -> None:
        self.correct = correct
        self.policy_violation = policy_violation
        self.detail = detail
        self.score_components = score_components or {}


def _parse_json_output(output: Any) -> Any:
    if isinstance(output, str):
        text = output.strip()
        # Allow fenced code blocks.
        if text.startswith("```"):
            lines = text.splitlines()
            lines = [ln for ln in lines if not ln.startswith("```")]
            text = "\n".join(lines).strip()
        return json.loads(text)
    return output


def grade_json_exact(case: BenchmarkCase, output: Any) -> GradeResult:
    try:
        got = _parse_json_output(output)
    except Exception as exc:
        return GradeResult(correct=False, detail=f"json_parse_error:{exc}")
    expected = case.expected_output
    # Context compaction may enforce max length on serialized compact form.
    max_chars = case.grader.get("max_compact_chars")
    if max_chars is not None:
        serialized = json.dumps(got, sort_keys=True, separators=(",", ":"))
        if len(serialized) > int(max_chars):
            return GradeResult(
                correct=False,
                detail=f"compact_too_long:{len(serialized)}>{max_chars}",
                score_components={"length_ok": 0.0},
            )
    ok = got == expected
    return GradeResult(
        correct=ok,
        detail="match" if ok else "mismatch",
        score_components={"exact": 1.0 if ok else 0.0},
    )


def _is_valid_topo(order: list[str], nodes: list[str], edges: list[list[str]]) -> bool:
    if sorted(order) != sorted(nodes):
        return False
    if len(order) != len(set(order)):
        return False
    index = {n: i for i, n in enumerate(order)}
    for edge in edges:
        a, b = edge[0], edge[1]
        if index[a] >= index[b]:
            return False
    return True


def grade_topological_order(case: BenchmarkCase, output: Any) -> GradeResult:
    try:
        got = _parse_json_output(output)
    except Exception as exc:
        return GradeResult(correct=False, detail=f"json_parse_error:{exc}")
    if isinstance(got, dict) and "order" in got:
        order = list(got["order"])
    elif isinstance(got, list):
        order = list(got)
    else:
        return GradeResult(correct=False, detail="missing_order")
    nodes = list(case.grader.get("nodes") or [])
    edges = list(case.grader.get("edges") or [])
    # Accept any valid topological order, not only the fixture's example order.
    ok = _is_valid_topo([str(x) for x in order], [str(n) for n in nodes], edges)
    return GradeResult(
        correct=ok,
        detail="valid_topo" if ok else "invalid_topo",
        score_components={"topo": 1.0 if ok else 0.0},
    )


def grade_python_unit(case: BenchmarkCase, output: Any) -> GradeResult:
    """Run model code against grader tests in IsolatedCodeRunner (network off)."""
    entry = str(case.grader.get("entrypoint") or "solve")
    tests = list(case.grader.get("tests") or [])
    if isinstance(output, dict) and "code" in output:
        code = str(output["code"])
    else:
        code = str(output)
    if "import os" in code or "socket" in code or "subprocess" in code:
        # Soft policy flag — still run under sandbox limits.
        policy = True
    else:
        policy = False

    harness = f'''
import json, copy, sys
NS = {{}}
CODE = {code!r}
exec(CODE, NS, NS)
fn = NS.get({entry!r})
if fn is None:
    print(json.dumps({{"ok": False, "error": "missing_entrypoint"}}))
    raise SystemExit(2)
tests = json.loads(sys.argv[1])
results = []
for t in tests:
    args = t.get("args") or []
    expected = t.get("expected")
    originals = copy.deepcopy(args)
    try:
        got = fn(*args)
        ok = got == expected
        if t.get("assert_inputs_unchanged") and originals != args:
            ok = False
            err = "inputs_mutated"
        else:
            err = None
    except Exception as exc:
        ok = False
        err = str(exc)
        got = None
    results.append({{"ok": ok, "error": err, "got": got}})
print(json.dumps({{"ok": all(r["ok"] for r in results), "results": results}}))
'''
    with tempfile.TemporaryDirectory(prefix="swarm-eval-") as tmp:
        work = Path(tmp)
        script = work / "harness.py"
        script.write_text(harness, encoding="utf-8")
        runner = IsolatedCodeRunner(work, network=False, timeout_seconds=5.0, memory_mb=256)
        result = runner.run_python("harness.py", [json.dumps(tests)])
        if result.timed_out or result.exit_code != 0:
            return GradeResult(
                correct=False,
                policy_violation=policy,
                detail=f"sandbox_fail:exit={result.exit_code}:stderr={result.stderr[:200]}",
            )
        try:
            payload = json.loads(result.stdout.strip().splitlines()[-1])
        except Exception as exc:
            return GradeResult(correct=False, policy_violation=policy, detail=f"bad_harness:{exc}")
        ok = bool(payload.get("ok"))
        return GradeResult(
            correct=ok,
            policy_violation=policy and not ok,
            detail="unit_pass" if ok else "unit_fail",
            score_components={"unit": 1.0 if ok else 0.0},
        )


def grade_case(case: BenchmarkCase, output: Any) -> GradeResult:
    kind = str(case.grader.get("kind"))
    if kind == "json_exact":
        return grade_json_exact(case, output)
    if kind == "topological_order":
        return grade_topological_order(case, output)
    if kind == "python_unit":
        return grade_python_unit(case, output)
    return GradeResult(correct=False, detail=f"unsupported_grader:{kind}")
