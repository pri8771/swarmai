"""Deterministic graders for benchmark cases."""

from __future__ import annotations

import hashlib
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
    """Run model code against grader tests in IsolatedCodeRunner (network off).

    Submitted code is loaded as a module file. The harness alone emits the
    verdict JSON with a nonce — forged stdout from the submission cannot pass (R5).
    """
    entry = str(case.grader.get("entrypoint") or "solve")
    tests = list(case.grader.get("tests") or [])
    if isinstance(output, dict) and "code" in output:
        code = str(output["code"])
    else:
        code = str(output)
    if "import os" in code or "socket" in code or "subprocess" in code:
        policy = True
    else:
        policy = False

    nonce = hashlib.sha256(f"{case.id}:{entry}:{len(tests)}".encode()).hexdigest()[:16]
    harness = f'''
import importlib.util
import json
import sys
from pathlib import Path

nonce = {nonce!r}
entry = {entry!r}
work = Path(__file__).resolve().parent
solution_path = work / "solution.py"
spec = importlib.util.spec_from_file_location("swarm_solution", solution_path)
if spec is None or spec.loader is None:
    print(
        json.dumps(
            {{"ok": False, "error": "load_failed", "harness_nonce": nonce, "results": []}}
        )
    )
    raise SystemExit(2)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except SystemExit as exc:
    print(
        json.dumps(
            {{
                "ok": False,
                "error": "solution_systemexit",
                "harness_nonce": nonce,
                "results": [],
            }}
        )
    )
    raise SystemExit(2) from exc
except Exception as exc:
    print(
        json.dumps(
            {{
                "ok": False,
                "error": f"import_error:{{exc}}",
                "harness_nonce": nonce,
                "results": [],
            }}
        )
    )
    raise SystemExit(2) from exc
fn = getattr(mod, entry, None)
if fn is None:
    print(
        json.dumps(
            {{
                "ok": False,
                "error": "missing_entrypoint",
                "harness_nonce": nonce,
                "results": [],
            }}
        )
    )
    raise SystemExit(2)
tests = json.loads(sys.argv[1])
results = []
import copy
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
    results.append({{"ok": ok, "error": err}})
payload = {{
    "ok": all(r["ok"] for r in results) and len(results) == len(tests),
    "results": results,
    "harness_nonce": nonce,
    "test_count": len(tests),
}}
print(json.dumps(payload))
'''
    with tempfile.TemporaryDirectory(prefix="swarm-eval-") as tmp:
        work = Path(tmp)
        (work / "solution.py").write_text(code, encoding="utf-8")
        script = work / "harness.py"
        script.write_text(harness, encoding="utf-8")
        runner = IsolatedCodeRunner(work, network=False, timeout_seconds=5.0, memory_mb=256)
        result = runner.run_python("harness.py", [json.dumps(tests)])
        if result.timed_out:
            return GradeResult(
                correct=False,
                policy_violation=policy,
                detail="sandbox_timeout",
            )
        try:
            lines = [ln for ln in result.stdout.strip().splitlines() if ln.strip()]
            payload = json.loads(lines[-1]) if lines else {}
        except Exception as exc:
            return GradeResult(
                correct=False,
                policy_violation=policy,
                detail=f"bad_harness:{exc}",
            )
        if payload.get("harness_nonce") != nonce:
            return GradeResult(
                correct=False,
                policy_violation=True,
                detail="forged_or_missing_harness_nonce",
            )
        if not isinstance(payload.get("results"), list):
            return GradeResult(correct=False, detail="missing_results")
        if len(payload["results"]) != len(tests):
            return GradeResult(correct=False, detail="test_count_mismatch")
        if result.exit_code != 0 and not payload.get("ok"):
            return GradeResult(
                correct=False,
                policy_violation=policy,
                detail=f"sandbox_fail:exit={result.exit_code}:{payload.get('error')}",
            )
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
