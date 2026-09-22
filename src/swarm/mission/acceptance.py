"""Generic mission acceptance — review controls outcome, not decoration."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

# Families the current generic runtime can execute. Others must stay unsupported.
SUPPORTED_TASK_FAMILIES = frozenset(
    {"inspect", "implement", "verify", "review", "extract", "triage", "plan"}
)

# Dogfood-only symbols. Mentioning these while reviewing an unrelated diff is stale.
STALE_DOGFOOD_SYMBOLS = frozenset(
    {
        "inclusive_range_count",
        "parser_helper",
        "parser_dogfood",
    }
)

_DIFF_PATH_RE = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)
_DIFF_GIT_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$", re.MULTILINE)
_DEF_RE = re.compile(r"^\+\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
_CLASS_RE = re.compile(r"^\+\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)


@dataclass
class SupportDecision:
    supported: bool
    family: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "supported": self.supported,
            "family": self.family,
            "reason": self.reason,
        }


@dataclass
class ReviewDecision:
    accepted: bool
    reasons: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reasons": list(self.reasons),
            "checks": dict(self.checks),
        }


@dataclass
class ReviewGroundingDecision:
    """Deterministic guard that a semantic review is about the actual diff."""

    grounded: bool
    reasons: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)
    changed_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "grounded": self.grounded,
            "reasons": list(self.reasons),
            "checks": dict(self.checks),
            "changed_paths": list(self.changed_paths),
        }


def changed_paths_from_diff(diff_text: str) -> list[str]:
    """Return unique paths touched by a unified git diff."""
    text = diff_text or ""
    paths: list[str] = []
    for match in _DIFF_PATH_RE.finditer(text):
        path = match.group(1).strip()
        if path and path != "/dev/null":
            paths.append(path)
    if not paths:
        for match in _DIFF_GIT_RE.finditer(text):
            path = match.group(2).strip()
            if path and path != "/dev/null":
                paths.append(path)
    return list(dict.fromkeys(paths))


def symbols_added_in_diff(diff_text: str) -> set[str]:
    """Top-level def/class names introduced on added lines."""
    text = diff_text or ""
    return set(_DEF_RE.findall(text)) | set(_CLASS_RE.findall(text))


def _path_tokens(path: str) -> set[str]:
    pure = PurePosixPath(path)
    tokens = {pure.name.lower(), pure.stem.lower()}
    for part in pure.parts:
        cleaned = part.lower().removesuffix(".py")
        if cleaned and cleaned not in {".", ".."}:
            tokens.add(cleaned)
    return tokens


def _command_blob(verify_commands: list[Any] | None) -> str:
    parts: list[str] = []
    for item in verify_commands or []:
        if isinstance(item, dict):
            argv = item.get("argv") or item.get("command") or item.get("cmd")
            if isinstance(argv, list):
                parts.append(" ".join(str(x) for x in argv))
            elif argv is not None:
                parts.append(str(argv))
            if item.get("cwd"):
                parts.append(str(item["cwd"]))
        else:
            parts.append(str(item))
    return " ".join(parts).lower()


def verify_has_focused_check(
    *,
    changed_paths: list[str],
    verify_commands: list[Any] | None,
    focused_check_paths: list[str] | None = None,
    allow_dogfood_mission_suite: bool = False,
) -> tuple[bool, dict[str, bool], list[str]]:
    """Broad unrelated suites alone are not enough for a claimed defect."""
    checks: dict[str, bool] = {}
    reasons: list[str] = []
    blob = _command_blob(verify_commands)
    focused_paths = [str(p) for p in (focused_check_paths or []) if str(p).strip()]
    if focused_paths:
        ok = all(p.lower() in blob or PurePosixPath(p).name.lower() in blob for p in focused_paths)
        checks["focused_check_paths_executed"] = ok
        if not ok:
            reasons.append("focused_check_missing")
            return False, checks, reasons
        checks["focused_or_target_relevant_verify"] = True
        return True, checks, reasons

    if not changed_paths:
        checks["focused_or_target_relevant_verify"] = False
        reasons.append("no_changed_paths_for_focused_verify")
        return False, checks, reasons

    target_hit = False
    for path in changed_paths:
        tokens = _path_tokens(path)
        if any(token and token in blob for token in tokens):
            target_hit = True
            break
        # tests/<pkg>/test_<stem>.py style relevance
        stem = PurePosixPath(path).stem.lower()
        if stem and f"test_{stem}" in blob:
            target_hit = True
            break

    only_mission_suite = bool(blob) and (
        "tests/mission" in blob
        and not any(
            token in blob
            for path in changed_paths
            for token in _path_tokens(path)
            if token not in {"src", "swarm", "tests", "py"}
        )
    )
    dogfood_target = any(
        "parser_helper" in p or "inclusive_range" in p for p in changed_paths
    ) or allow_dogfood_mission_suite

    if target_hit:
        checks["focused_or_target_relevant_verify"] = True
        checks["broad_unrelated_suite_only"] = False
        return True, checks, reasons

    if only_mission_suite and not dogfood_target:
        checks["focused_or_target_relevant_verify"] = False
        checks["broad_unrelated_suite_only"] = True
        reasons.append("broad_unrelated_suite_only")
        return False, checks, reasons

    if not blob:
        checks["focused_or_target_relevant_verify"] = False
        reasons.append("no_verify_commands")
        return False, checks, reasons

    checks["focused_or_target_relevant_verify"] = False
    reasons.append("verify_not_tied_to_changed_paths")
    return False, checks, reasons


def ground_semantic_review(
    *,
    review_text: str,
    diff_text: str,
    target_paths: list[str] | None = None,
    verify_commands: list[Any] | None = None,
    focused_check_paths: list[str] | None = None,
    allow_dogfood_symbols: bool = False,
) -> ReviewGroundingDecision:
    """Reject stale/unrelated reviewer text and unfocused verification.

    A review is grounded only when:
    1. there is a material diff with changed paths;
    2. review text references at least one changed path token or added symbol;
    3. review does not lean on stale dogfood symbols absent from the diff;
    4. verification includes a focused/target-relevant check (not only a broad
       unrelated suite such as tests/mission for a cost/ledger change).
    """
    reasons: list[str] = []
    checks: dict[str, bool] = {}
    changed = list(target_paths or []) or changed_paths_from_diff(diff_text)
    checks["material_diff_present"] = bool((diff_text or "").strip()) and bool(changed)
    if not checks["material_diff_present"]:
        reasons.append("review_ungrounded:no_material_diff_paths")
        return ReviewGroundingDecision(
            grounded=False, reasons=reasons, checks=checks, changed_paths=changed
        )

    text = review_text or ""
    lowered = text.lower()
    if not text.strip():
        checks["review_references_changed_target"] = False
        reasons.append("review_ungrounded:empty_review_text")
        return ReviewGroundingDecision(
            grounded=False, reasons=reasons, checks=checks, changed_paths=changed
        )

    path_hit = False
    for path in changed:
        tokens = _path_tokens(path)
        if any(token in lowered for token in tokens if len(token) > 2):
            path_hit = True
            break
        if path.lower() in lowered or PurePosixPath(path).name.lower() in lowered:
            path_hit = True
            break

    added_symbols = symbols_added_in_diff(diff_text)
    symbol_hit = any(sym.lower() in lowered for sym in added_symbols)
    checks["review_references_changed_target"] = path_hit or symbol_hit
    if not checks["review_references_changed_target"]:
        reasons.append("review_ungrounded:no_changed_path_or_symbol")

    stale_hits = sorted(
        sym
        for sym in STALE_DOGFOOD_SYMBOLS
        if sym.lower() in lowered
        and sym.lower() not in {s.lower() for s in added_symbols}
        and not any(sym.lower() in p.lower() for p in changed)
    )
    if allow_dogfood_symbols:
        stale_hits = []
    checks["stale_unrelated_symbols_absent"] = not stale_hits
    if stale_hits:
        reasons.append("review_ungrounded:stale_symbols:" + ",".join(stale_hits))

    focused_ok, focused_checks, focused_reasons = verify_has_focused_check(
        changed_paths=changed,
        verify_commands=verify_commands,
        focused_check_paths=focused_check_paths,
        allow_dogfood_mission_suite=allow_dogfood_symbols,
    )
    checks.update(focused_checks)
    reasons.extend(focused_reasons)

    grounded = (
        checks["material_diff_present"]
        and checks["review_references_changed_target"]
        and checks["stale_unrelated_symbols_absent"]
        and focused_ok
    )
    if grounded:
        reasons.append("review_grounded")
    else:
        reasons.append("review_ungrounded")
    return ReviewGroundingDecision(
        grounded=grounded, reasons=reasons, checks=checks, changed_paths=changed
    )


_DEFECT_GOAL_RE = re.compile(r"\b(defect|bug|regression|fix|fixes|fixed|repair)\b", re.IGNORECASE)
_PYTEST_TEST_FAILURE = 1
_PYTEST_NOT_A_CLEAN_FAILURE = {2, 3, 4, 5}


@dataclass
class DefectProofDecision:
    """R02a: proven only by a regression that fails pre-patch and passes post-patch."""

    proven: bool
    reason: str
    regression_tests: list[str] = field(default_factory=list)
    pre_patch: dict[str, Any] = field(default_factory=dict)
    post_patch: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "proven": self.proven,
            "reason": self.reason,
            "regression_tests": list(self.regression_tests),
            "pre_patch": dict(self.pre_patch),
            "post_patch": dict(self.post_patch),
        }


def is_defect_repair_goal(goal: str | None, inputs: dict[str, Any] | None = None) -> bool:
    """Defect-repair missions are gated by red->green proof (R02a)."""
    if inputs and inputs.get("defect_repair") is True:
        return True
    return bool(goal) and bool(_DEFECT_GOAL_RE.search(goal or ""))


def regression_tests_in_diff(diff_text: str) -> list[str]:
    """Test files added or modified by the diff (tests/**/test_*.py)."""
    found: list[str] = []
    for path in changed_paths_from_diff(diff_text):
        pure = PurePosixPath(path)
        is_test = pure.name.startswith("test_") and pure.suffix == ".py"
        if pure.parts and pure.parts[0] == "tests" and is_test:
            found.append(path)
    return found


def _command_summary(result: dict[str, Any]) -> dict[str, Any]:
    stdout = str(result.get("stdout") or "")
    stderr = str(result.get("stderr") or "")
    return {
        "cmd": list(result.get("cmd") or []),
        "exit_code": result.get("exit_code"),
        "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
        "stdout_tail": stdout[-1200:],
        "stderr_tail": stderr[-600:],
    }


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=False
    )


def prove_defect(
    *,
    repo: Path,
    candidate_sha: str,
    worktree: Path,
    diff_text: str,
    run: Callable[[Path, list[str]], dict[str, Any]],
) -> DefectProofDecision:
    """Red->green proof: the patch's own regression tests must fail on a clean
    checkout of ``candidate_sha`` (production files pre-patch) and pass in the
    patched worktree. Collection/usage/internal errors are not "red"; a test
    that cannot be collected proves nothing about pre-patch behavior.
    """
    regressions = regression_tests_in_diff(diff_text)
    if not regressions:
        return DefectProofDecision(
            proven=False, reason="no_regression_test_in_patch", regression_tests=[]
        )
    present = [p for p in regressions if (worktree / p).is_file()]
    if not present:
        return DefectProofDecision(
            proven=False, reason="no_regression_test_in_patch", regression_tests=regressions
        )

    repo = repo.resolve()
    clean = repo / "var" / "defect-proof" / f"clean-{candidate_sha[:12]}-{worktree.name[:24]}"
    if clean.exists():
        shutil.rmtree(clean, ignore_errors=True)
        _git(repo, "worktree", "prune")
    clean.parent.mkdir(parents=True, exist_ok=True)
    added = _git(repo, "worktree", "add", "--detach", str(clean), candidate_sha)
    if added.returncode != 0:
        return DefectProofDecision(
            proven=False,
            reason="clean_worktree_unavailable",
            regression_tests=present,
            pre_patch={"error": (added.stderr or added.stdout).strip()[-600:]},
        )
    try:
        # Only the regression tests cross over; production files stay pre-patch.
        for rel in present:
            target = clean / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(worktree / rel, target)
        pre = run(clean, ["pytest", *present, "-q", "--tb=line"])
        pre_summary = _command_summary(pre)
        code = pre.get("exit_code")
        if code in _PYTEST_NOT_A_CLEAN_FAILURE:
            return DefectProofDecision(
                proven=False,
                reason="pre_patch_not_a_clean_failure",
                regression_tests=present,
                pre_patch=pre_summary,
            )
        if code == 0:
            return DefectProofDecision(
                proven=False,
                reason="regression_passes_without_patch",
                regression_tests=present,
                pre_patch=pre_summary,
            )
        if code != _PYTEST_TEST_FAILURE:
            return DefectProofDecision(
                proven=False,
                reason=f"pre_patch_unexpected_exit:{code}",
                regression_tests=present,
                pre_patch=pre_summary,
            )
        post = run(worktree, ["pytest", *present, "-q", "--tb=line"])
        post_summary = _command_summary(post)
        if post.get("exit_code") != 0:
            return DefectProofDecision(
                proven=False,
                reason="regression_fails_with_patch",
                regression_tests=present,
                pre_patch=pre_summary,
                post_patch=post_summary,
            )
        return DefectProofDecision(
            proven=True,
            reason="red_green_demonstrated",
            regression_tests=present,
            pre_patch=pre_summary,
            post_patch=post_summary,
        )
    finally:
        removed = _git(repo, "worktree", "remove", "--force", str(clean))
        if removed.returncode != 0 and clean.exists():
            shutil.rmtree(clean, ignore_errors=True)
            _git(repo, "worktree", "prune")


def classify_task_support(task_family: str) -> SupportDecision:
    family = (task_family or "").strip().lower()
    if not family:
        return SupportDecision(False, family, "missing_task_family")
    if family not in SUPPORTED_TASK_FAMILIES:
        return SupportDecision(
            False,
            family,
            f"unsupported_task_family:{family}",
        )
    return SupportDecision(True, family, "supported")


def _grade_hidden_acceptance(
    *,
    output_text: str,
    hidden: dict[str, Any],
) -> tuple[bool, dict[str, bool], list[str]]:
    """Grade model output with task-defined rules the worker never sees.

    Supported keys (all optional; at least one must be present for a useful gate):
    - must_contain_all: every substring must appear (case-insensitive)
    - must_contain_any: at least one substring must appear
    - forbid_substrings: none of these may appear
    - min_output_chars: minimum length of output_text
    - required_json_keys: if output looks like JSON object, these keys must exist
    """
    text = output_text or ""
    lowered = text.lower()
    checks: dict[str, bool] = {}
    reasons: list[str] = []

    min_chars = hidden.get("min_output_chars")
    if min_chars is not None:
        ok = len(text) >= int(min_chars)
        checks["min_output_chars"] = ok
        if not ok:
            reasons.append("hidden_failed:min_output_chars")

    must_all = hidden.get("must_contain_all") or []
    if must_all:
        ok = all(str(s).lower() in lowered for s in must_all)
        checks["must_contain_all"] = ok
        if not ok:
            reasons.append("hidden_failed:must_contain_all")

    must_any = hidden.get("must_contain_any") or []
    if must_any:
        ok = any(str(s).lower() in lowered for s in must_any)
        checks["must_contain_any"] = ok
        if not ok:
            reasons.append("hidden_failed:must_contain_any")

    forbid = hidden.get("forbid_substrings") or []
    if forbid:
        ok = not any(str(s).lower() in lowered for s in forbid)
        checks["forbid_substrings"] = ok
        if not ok:
            reasons.append("hidden_failed:forbid_substrings")

    json_keys = hidden.get("required_json_keys") or []
    if json_keys:
        parsed: dict[str, Any] | None = None
        try:
            import json

            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                candidate = json.loads(text[start : end + 1])
                if isinstance(candidate, dict):
                    parsed = candidate
        except Exception:
            parsed = None
        if parsed is None:
            checks["required_json_keys"] = False
            reasons.append("hidden_failed:required_json_keys_not_json")
        else:
            ok = all(str(k) in parsed for k in json_keys)
            checks["required_json_keys"] = ok
            if not ok:
                reasons.append("hidden_failed:required_json_keys")

    if not checks:
        reasons.append("hidden_acceptance_empty")
        return False, checks, reasons
    return all(checks.values()), checks, reasons


def review_attempt(
    *,
    produced: dict[str, Any],
    required_checks: dict[str, Any] | None = None,
    force_wrong: bool = False,
    hidden_acceptance: dict[str, Any] | None = None,
    defect_repair: bool = False,
    defect_proof: dict[str, Any] | None = None,
) -> ReviewDecision:
    """Independent checks control accept/reject. Wrong results cannot be accepted.

    ``required_checks`` maps check_id → expected value. ``produced`` must contain
    matching ``checks`` or top-level fields. ``force_wrong`` simulates an
    intentionally incorrect worker claim that review must reject.

    ``hidden_acceptance`` grades ``produced['output_excerpt']`` (or ``output``)
    with deterministic rules that must not be shown to the worker.
    """
    reasons: list[str] = []
    checks: dict[str, bool] = {}
    required = required_checks or {}
    produced_checks = produced.get("checks")
    if not isinstance(produced_checks, dict):
        produced_checks = produced

    if force_wrong or produced.get("intentionally_wrong") is True:
        reasons.append("wrong_result_rejected")
        checks["wrong_result"] = False
        return ReviewDecision(accepted=False, reasons=reasons, checks=checks)

    if produced.get("unsupported") is True:
        reasons.append(str(produced.get("unsupported_reason") or "unsupported_task"))
        checks["supported"] = False
        return ReviewDecision(accepted=False, reasons=reasons, checks=checks)

    if defect_repair:
        # R02a: a material diff with green existing tests is never enough; the
        # patch's own regression must have failed before it and pass after it.
        proof = defect_proof or {}
        proven = proof.get("proven") is True
        checks["defect_proven"] = proven
        if not proven:
            reasons.append("no_defect_demonstrated")
            if proof.get("reason"):
                reasons.append(f"defect_proof:{proof['reason']}")
            return ReviewDecision(accepted=False, reasons=reasons, checks=checks)

    if not required and not hidden_acceptance:
        # No independent checks ⇒ cannot accept (review must control acceptance).
        reasons.append("no_independent_checks")
        checks["independent_review"] = False
        return ReviewDecision(accepted=False, reasons=reasons, checks=checks)

    all_ok = True
    for key, expected in required.items():
        actual = produced_checks.get(key)
        ok = actual == expected
        checks[str(key)] = ok
        if not ok:
            all_ok = False
            reasons.append(f"check_failed:{key}")

    if hidden_acceptance:
        output = str(
            produced.get("output_excerpt")
            or produced.get("output")
            or produced_checks.get("output_excerpt")
            or ""
        )
        hidden_ok, hidden_checks, hidden_reasons = _grade_hidden_acceptance(
            output_text=output, hidden=hidden_acceptance
        )
        for k, v in hidden_checks.items():
            checks[f"hidden:{k}"] = v
        reasons.extend(hidden_reasons)
        if not hidden_ok:
            all_ok = False

    if all_ok:
        reasons.append("all_independent_checks_passed")
        return ReviewDecision(accepted=True, reasons=reasons, checks=checks)
    reasons.append("wrong_result_rejected")
    return ReviewDecision(accepted=False, reasons=reasons, checks=checks)
