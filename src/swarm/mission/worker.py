"""Real repository workers operating inside git worktrees."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.mission import TaskSpec
from swarm.mission.acceptance import (
    changed_paths_from_diff,
    classify_task_support,
    ground_semantic_review,
    review_attempt,
)
from swarm.mission.inference import InferenceResult, local_chat
from swarm.mission.worktree import WorktreeHandle, create_worktree, worktree_diff

# Known dogfood target inside the SwarmAI repo.
OFF_BY_ONE_REL = Path("sandbox/selfdev_issue/parser_helper.py")
OFF_BY_ONE_TEST_REL = Path("sandbox/selfdev_issue/parser_helper_test.py")

GOOD_FIX = '''\
"""Synthetic buggy helper used by the P19 self-development demo."""

from __future__ import annotations


def inclusive_range_count(start: int, end: int) -> int:
    """Count integers from start to end inclusive."""
    return end - start + 1
'''


@dataclass
class WorkerResult:
    worker_id: str
    task_id: str
    task_family: str
    ok: bool
    summary: str
    artifacts: dict[str, Any] = field(default_factory=dict)
    inference: dict[str, Any] | None = None
    cost_usd: float = 0.0
    started_at: str = field(default_factory=lambda: utc_now().isoformat())
    finished_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "task_id": self.task_id,
            "task_family": self.task_family,
            "ok": self.ok,
            "summary": self.summary,
            "artifacts": self.artifacts,
            "inference": self.inference,
            "cost_usd": self.cost_usd,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


def _run_cmd(cwd: Path, cmd: list[str], *, timeout: float = 120.0) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "cmd": cmd,
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout": (proc.stdout or "")[-8000:],
        "stderr": (proc.stderr or "")[-4000:],
    }


def _looks_like_python_source(text: str) -> bool:
    """Heuristic for full-file Python responses (no Markdown required)."""
    s = text.lstrip()
    if not s:
        return False
    starts_ok = s.startswith(
        (
            '"""',
            "'''",
            "#",
            "from ",
            "import ",
            "def ",
            "class ",
            "async def ",
            "@",
            "#!/",
        )
    )
    if not starts_ok:
        return False
    return any(token in s for token in ("def ", "class ", "import ", "from "))


def _normalize_python_source(text: str) -> str:
    body = text.strip() + "\n"
    return body


def _valid_python_syntax(text: str) -> bool:
    try:
        compile(text, "<mission-implement>", "exec")
    except SyntaxError:
        return False
    return True


def _top_level_defs(text: str) -> set[str]:
    """Names of top-level def/class statements (best-effort, indentation-based)."""
    names: set[str] = set()
    for line in text.splitlines():
        if not line or line[0].isspace():
            continue
        m = re.match(r"^(?:async\s+)?def\s+(\w+)\s*\(", line)
        if m:
            names.add(m.group(1))
            continue
        m = re.match(r"^class\s+(\w+)\s*[:\(]", line)
        if m:
            names.add(m.group(1))
    return names


def _looks_truncated_rewrite(original: str, patched: str) -> bool:
    """Reject incomplete full-file rewrites that drop most of the original API.

    Truncation at max_tokens often yields a syntactically-invalid file (caught
    elsewhere) or a shorter valid-looking prefix that omits trailing defs.
    """
    if not original.strip():
        return False
    orig_lines = [ln for ln in original.splitlines() if ln.strip()]
    patch_lines = [ln for ln in patched.splitlines() if ln.strip()]
    if len(orig_lines) >= 40 and len(patch_lines) < max(20, int(0.6 * len(orig_lines))):
        return True
    orig_defs = _top_level_defs(original)
    patch_defs = _top_level_defs(patched)
    if len(orig_defs) >= 3 and len(patch_defs) < max(1, int(0.6 * len(orig_defs))):
        missing = orig_defs - patch_defs
        if len(missing) >= max(2, int(0.4 * len(orig_defs))):
            return True
    return False


def _extract_python_file(text: str) -> str | None:
    """Extract full-file Python from a model response.

    Accepts Markdown fences or raw source matching the implement prompt contract
    ("Return ONLY the full corrected file contents"). Fixture-specific
    ``inclusive_range_count`` recovery remains for the dogfood sample only.

    Unclosed/truncated fences (common when generation hits max_tokens) are accepted
    when the body still looks like Python; callers must still require a material
    git diff before success.
    """
    if not text or not str(text).strip():
        return None
    raw = str(text)
    fence = re.search(r"```(?:python)?\n(.*?)```", raw, re.S)
    if fence:
        body = _normalize_python_source(fence.group(1))
        return body if _looks_like_python_source(body) else None
    open_fence = re.search(r"```(?:python)?\n(.*)\Z", raw, re.S)
    if open_fence:
        body = _normalize_python_source(open_fence.group(1))
        return body if _looks_like_python_source(body) else None
    stripped = raw.strip()
    if _looks_like_python_source(stripped):
        return _normalize_python_source(stripped)
    if "def inclusive_range_count" in raw and "return" in raw:
        # Fixture-only best-effort: take from module docstring/import through end.
        start = raw.find('"""')
        if start < 0:
            start = raw.find("def inclusive_range_count")
        if start >= 0:
            body = _normalize_python_source(raw[start:])
            return body if _looks_like_python_source(body) else None
    return None


class RepoWorker:
    """Reads/searches/edits files and runs approved local commands in a worktree.

    The off-by-one parser sample is fixture-only (LEAD-009 #6). Normal mission
    runs must opt in via ``parser_dogfood_fixture=True`` or supply task inputs
    (``target_file`` / ``test_file``). Hard-wiring the dogfood path as the
    default operational mission is forbidden.
    """

    def __init__(
        self,
        repo: Path,
        *,
        model: str = "gemma3:4b",
        worktree_root: Path | None = None,
        model_by_family: dict[str, str] | None = None,
        broker: Any | None = None,
        project_id: str = "proj_demo",
        parser_dogfood_fixture: bool = False,
        require_broker: bool = False,
    ) -> None:
        self.repo = repo.resolve()
        self.model = model
        self.model_by_family = model_by_family or {}
        self.worktree_root = worktree_root
        self.worker_id = new_id("wrk_")
        self.broker = broker
        self.project_id = project_id
        self.parser_dogfood_fixture = parser_dogfood_fixture
        # Operational API/CLI paths must set this so model calls cannot bypass
        # the governed project-scoped broker via direct local_chat.
        self.require_broker = require_broker

    def _model_for(self, task_family: str) -> str:
        return self.model_by_family.get(task_family) or self.model

    def _resolve_target_rel(self, task: TaskSpec) -> Path | None:
        raw = task.inputs.get("target_file") or task.inputs.get("target_path")
        if isinstance(raw, str) and raw.strip():
            return Path(raw.strip())
        if self.parser_dogfood_fixture:
            return OFF_BY_ONE_REL
        return None

    def _resolve_test_rel(self, task: TaskSpec) -> Path | None:
        raw = task.inputs.get("test_file") or task.inputs.get("test_path")
        if isinstance(raw, str) and raw.strip():
            return Path(raw.strip())
        if self.parser_dogfood_fixture:
            return OFF_BY_ONE_TEST_REL
        return None

    def _chat(
        self,
        *,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int = 800,
    ) -> InferenceResult:
        """Prefer brokered path; fail closed when broker is required but missing."""
        if self.broker is not None:
            from swarm.mission.brokered_inference import brokered_local_chat_sync

            return brokered_local_chat_sync(
                broker=self.broker,
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                project_id=self.project_id,
                purpose="mission",
            )
        if self.require_broker:
            return InferenceResult(
                ok=False,
                text="",
                model=model,
                route_id=f"rt_ollama_{model}",
                error="broker_required_but_missing",
            )
        return local_chat(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            repo_root=self.repo,
        )

    def run_task(
        self,
        task: TaskSpec,
        *,
        mission_id: str,
        prior: dict[str, WorkerResult],
        shared_worktree: WorktreeHandle | None = None,
    ) -> tuple[WorkerResult, WorktreeHandle | None]:
        family = task.task_family
        support = classify_task_support(family)
        if not support.supported:
            result = WorkerResult(
                worker_id=self.worker_id,
                task_id=task.id,
                task_family=family,
                ok=False,
                summary=support.reason,
                artifacts={"support": support.to_dict(), "unsupported": True},
                finished_at=utc_now().isoformat(),
            )
            return result, shared_worktree
        if family == "inspect":
            return self._inspect(task, mission_id=mission_id), shared_worktree
        if family == "implement":
            return self._implement(
                task, mission_id=mission_id, shared=shared_worktree, prior=prior
            )
        if family == "verify":
            assert shared_worktree is not None
            return self._verify(task, handle=shared_worktree), shared_worktree
        if family == "review":
            assert shared_worktree is not None
            return (
                self._review(task, handle=shared_worktree, prior=prior),
                shared_worktree,
            )
        if family == "extract":
            return self._extract_or_triage(task, family="extract"), shared_worktree
        if family == "triage":
            return self._extract_or_triage(task, family="triage"), shared_worktree
        if family == "plan":
            return self._extract_or_triage(task, family="plan"), shared_worktree
        # Supported families without dedicated handlers stay honest incomplete.
        result = WorkerResult(
            worker_id=self.worker_id,
            task_id=task.id,
            task_family=family,
            ok=False,
            summary=f"handler_not_implemented:{family}",
            artifacts={"support": support.to_dict(), "handler_missing": True},
            finished_at=utc_now().isoformat(),
        )
        return result, shared_worktree

    def _extract_or_triage(self, task: TaskSpec, *, family: str) -> WorkerResult:
        """Generic extract/triage/plan via local zero-spend inference — no known answers."""
        goal = str(task.inputs.get("goal") or task.objective or "")
        if family == "extract":
            system = (
                "You extract structured fields from unfamiliar text. "
                "Return concise JSON with keys you can justify from the input. "
                "Do not invent facts not present in the objective."
            )
            user = f"Extract structured fields for this unfamiliar task:\n{goal}"
        elif family == "triage":
            system = (
                "You triage unfamiliar operational incidents. "
                "Return concise JSON with keys: hypothesis, evidence_needed, next_checks. "
                "Do not claim a definitive root cause without evidence."
            )
            user = f"Triage this unfamiliar incident:\n{goal}"
        else:
            system = (
                "You produce a short actionable plan. "
                "Return concise JSON with keys: steps (array), risks, unknowns."
            )
            user = f"Plan this unfamiliar task:\n{goal}"
        inference = self._chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            model=self._model_for(family),
            max_tokens=600,
        )
        text = (inference.text or "").strip()
        ok = bool(inference.ok and len(text) >= 20)
        summary = f"{family}_complete" if ok else f"{family}_failed_or_empty"
        checks: dict[str, bool] = {
            "inference_ok": bool(inference.ok),
            "nonempty_output": len(text) >= 20,
            "no_known_answer_path": True,
        }
        # Independent check for extract family when required by mission plan.
        if family == "extract":
            checks["fields_extracted"] = ok and ("{" in text or ":" in text)
        if family == "triage":
            checks["hypothesis_present"] = ok and (
                "hypothesis" in text.lower() or "check" in text.lower() or len(text) >= 40
            )
        return WorkerResult(
            worker_id=self.worker_id,
            task_id=task.id,
            task_family=family,
            ok=ok,
            summary=summary,
            artifacts={
                "output_excerpt": text[:2000],
                "checks": checks,
                "known_answer_forbidden": True,
            },
            inference=inference.to_dict(),
            finished_at=utc_now().isoformat(),
        )

    def _inspect(self, task: TaskSpec, *, mission_id: str) -> WorkerResult:
        findings: dict[str, Any] = {
            "mission_id": mission_id,
            "goal": task.inputs.get("goal"),
            "candidate_files": [],
            "strategy": (
                "parser_dogfood_fixture" if self.parser_dogfood_fixture else "task_provided_paths"
            ),
            "parser_dogfood_fixture": self.parser_dogfood_fixture,
        }
        target_rel = self._resolve_target_rel(task)
        if target_rel is not None:
            target = self.repo / target_rel
            if target.exists():
                text = target.read_text(encoding="utf-8")
                findings["candidate_files"].append(str(target_rel))
                findings["file_preview"] = text[:500]
                if self.parser_dogfood_fixture:
                    findings["off_by_one_suspected"] = (
                        "end - start" in text and "+ 1" not in text
                    )
        elif not self.parser_dogfood_fixture:
            # Generic path: accept explicit goal path mentions, never invent dogfood.
            goal = str(task.inputs.get("goal") or "")
            for match in re.findall(
                r"(?:[\w.-]+/)+[\w.-]+\.py",
                goal,
            ):
                cand = Path(match)
                if (self.repo / cand).exists():
                    findings["candidate_files"].append(str(cand))
            findings["strategy"] = "goal_path_scan"
        # Optional improvement signal (not a dogfood substitute).
        cost_cli_hint = not (self.repo / "src" / "swarm" / "cost" / "ledger.py").exists()
        findings["missing_cost_ledger"] = cost_cli_hint
        ok = bool(findings["candidate_files"]) or cost_cli_hint
        return WorkerResult(
            worker_id=self.worker_id,
            task_id=task.id,
            task_family="inspect",
            ok=ok,
            summary="inspection_complete" if ok else "inspection_no_candidates",
            artifacts={"findings": findings},
            finished_at=utc_now().isoformat(),
        )

    def _implement(
        self,
        task: TaskSpec,
        *,
        mission_id: str,
        shared: WorktreeHandle | None,
        prior: dict[str, WorkerResult] | None = None,
    ) -> tuple[WorkerResult, WorktreeHandle]:
        handle = shared or create_worktree(
            self.repo,
            mission_id=mission_id,
            task_id=task.id,
            worker_id=self.worker_id,
            base_dir=self.worktree_root,
        )
        target_rel = self._resolve_target_rel(task)
        if target_rel is None and prior:
            for prev in prior.values():
                if prev.task_family != "inspect":
                    continue
                cands = (prev.artifacts.get("findings") or {}).get("candidate_files") or []
                if cands:
                    target_rel = Path(str(cands[0]))
                    break
        if target_rel is None:
            result = WorkerResult(
                worker_id=self.worker_id,
                task_id=task.id,
                task_family="implement",
                ok=False,
                summary="implement_requires_target_or_fixture_parser_dogfood",
                artifacts={
                    "worktree": handle.to_dict(),
                    "changed_files": [],
                    "diff": "",
                    "parser_dogfood_fixture": self.parser_dogfood_fixture,
                    "hint": (
                        "Pass --fixture-parser-dogfood for the sandbox off-by-one sample, "
                        "or set task inputs target_file for a generic mission path."
                    ),
                },
                finished_at=utc_now().isoformat(),
            )
            return result, handle

        target = handle.path / target_rel
        original = target.read_text(encoding="utf-8") if target.exists() else ""
        if self.parser_dogfood_fixture:
            prompt = (
                "You are fixing a Python bug in SwarmAI. Return ONLY the full corrected "
                "file contents for parser_helper.py. Function inclusive_range_count(start, end) "
                "must count integers from start to end inclusive. Current file:\n\n"
                f"{original}"
            )
            require_inclusive = True
        else:
            goal = str(task.inputs.get("goal") or task.objective or "")
            prompt = (
                f"You are editing {target_rel} in a software mission. "
                f"Goal: {goal}\n"
                "Return ONLY the COMPLETE corrected file contents as valid Python. "
                "Do not truncate. Do not omit trailing functions or classes. "
                "Do not wrap the answer in commentary outside a single optional "
                "```python fenced block.\n\n"
                f"Current file:\n{original}"
            )
            require_inclusive = False
        inference = self._chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Return only complete, syntactically valid Python source for the "
                        "entire file. Never truncate mid-function."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            model=self._model_for("implement"),
            # Full-file rewrites need headroom; 800 often truncates mid-fence.
            max_tokens=4096,
        )
        patched = _extract_python_file(inference.text) if inference.ok else None
        # Operational path: never substitute a known-answer GOOD_FIX. Failed or
        # non-matching model output is a real failure for bounded repair/escalation.
        used_fallback = False
        if patched is None or (require_inclusive and "end - start + 1" not in patched):
            result = WorkerResult(
                worker_id=self.worker_id,
                task_id=task.id,
                task_family="implement",
                ok=False,
                summary="implement_failed_no_known_answer_fallback",
                artifacts={
                    "worktree": handle.to_dict(),
                    "changed_files": [],
                    "diff": "",
                    "used_model_fallback": False,
                    "known_answer_forbidden": True,
                    "parser_dogfood_fixture": self.parser_dogfood_fixture,
                    "target_file": str(target_rel),
                    "model_output_excerpt": (inference.text or "")[:500],
                },
                inference=inference.to_dict(),
                finished_at=utc_now().isoformat(),
            )
            return result, handle
        if not _valid_python_syntax(patched):
            result = WorkerResult(
                worker_id=self.worker_id,
                task_id=task.id,
                task_family="implement",
                ok=False,
                summary="implement_invalid_python_syntax",
                artifacts={
                    "worktree": handle.to_dict(),
                    "changed_files": [],
                    "diff": "",
                    "used_model_fallback": False,
                    "known_answer_forbidden": True,
                    "parser_dogfood_fixture": self.parser_dogfood_fixture,
                    "target_file": str(target_rel),
                    "model_output_excerpt": (inference.text or "")[:500],
                },
                inference=inference.to_dict(),
                finished_at=utc_now().isoformat(),
            )
            return result, handle
        if _looks_truncated_rewrite(original, patched):
            result = WorkerResult(
                worker_id=self.worker_id,
                task_id=task.id,
                task_family="implement",
                ok=False,
                summary="implement_truncated_rewrite",
                artifacts={
                    "worktree": handle.to_dict(),
                    "changed_files": [],
                    "diff": "",
                    "used_model_fallback": False,
                    "known_answer_forbidden": True,
                    "parser_dogfood_fixture": self.parser_dogfood_fixture,
                    "target_file": str(target_rel),
                    "original_top_level_defs": sorted(_top_level_defs(original)),
                    "patched_top_level_defs": sorted(_top_level_defs(patched)),
                    "model_output_excerpt": (inference.text or "")[:500],
                },
                inference=inference.to_dict(),
                finished_at=utc_now().isoformat(),
            )
            return result, handle
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(patched, encoding="utf-8")
        # Material git diff is the sole authority for "work changed". In-memory
        # inequality or a write attempt must never count as success alone.
        diff = worktree_diff(handle)
        if not diff.strip():
            if patched != original and target.exists():
                target.write_text(original, encoding="utf-8")
            result = WorkerResult(
                worker_id=self.worker_id,
                task_id=task.id,
                task_family="implement",
                ok=False,
                summary="implement_no_material_diff",
                artifacts={
                    "worktree": handle.to_dict(),
                    "changed_files": [],
                    "diff": "",
                    "used_model_fallback": used_fallback,
                    "known_answer_forbidden": True,
                    "parser_dogfood_fixture": self.parser_dogfood_fixture,
                    "target_file": str(target_rel),
                    "noop_or_untracked": patched == original,
                    "model_output_excerpt": (inference.text or "")[:500],
                },
                inference=inference.to_dict(),
                cost_usd=inference.cost_usd,
                finished_at=utc_now().isoformat(),
            )
            return result, handle
        result = WorkerResult(
            worker_id=self.worker_id,
            task_id=task.id,
            task_family="implement",
            ok=True,
            summary="implement_applied",
            artifacts={
                "worktree": handle.to_dict(),
                "changed_files": [str(target_rel)],
                "diff": diff[-12000:],
                "used_model_fallback": used_fallback,
                "known_answer_forbidden": True,
                "parser_dogfood_fixture": self.parser_dogfood_fixture,
            },
            inference=inference.to_dict(),
            cost_usd=inference.cost_usd,
            finished_at=utc_now().isoformat(),
        )
        return result, handle

    def _verify(self, task: TaskSpec, *, handle: WorktreeHandle) -> WorkerResult:
        commands: list[dict[str, Any]] = []
        test_rel = self._resolve_test_rel(task)
        goal = str(task.inputs.get("goal") or "")
        if test_rel is None and goal:
            for match in re.findall(r"(?:[\w.-]+/)+[\w.-]+\.py", goal):
                cand = Path(match)
                name = cand.name.lower()
                if (
                    "test" in name or cand.parts[0] == "tests"
                ) and (handle.path / cand).exists():
                    test_rel = cand
                    break
        if test_rel is not None:
            test_file = handle.path / test_rel
            if test_file.exists():
                if test_rel.parts[:1] == ("tests",) and (handle.path / "pyproject.toml").exists():
                    commands.append(
                        _run_cmd(
                            handle.path,
                            [
                                "uv",
                                "run",
                                "pytest",
                                str(test_rel),
                                "-q",
                                "--tb=line",
                            ],
                            timeout=180,
                        )
                    )
                else:
                    commands.append(
                        _run_cmd(
                            test_file.parent,
                            ["python", test_file.name],
                            timeout=30,
                        )
                    )
        # Prefer package-focused suite when goal names src/swarm/<pkg>/...
        if (handle.path / "pyproject.toml").exists():
            for match in re.findall(r"src/swarm/([\w-]+)/", goal):
                pkg_tests = handle.path / "tests" / match
                if pkg_tests.is_dir():
                    commands.append(
                        _run_cmd(
                            handle.path,
                            [
                                "uv",
                                "run",
                                "pytest",
                                f"tests/{match}",
                                "-q",
                                "--tb=line",
                            ],
                            timeout=180,
                        )
                    )
                    break
        # Dogfood / fallback: mission unit tests when present.
        mission_tests = handle.path / "tests" / "mission"
        if (
            mission_tests.is_dir()
            and (handle.path / "pyproject.toml").exists()
            and (self.parser_dogfood_fixture or not commands)
        ):
            commands.append(
                _run_cmd(
                    handle.path,
                    ["uv", "run", "pytest", "tests/mission", "-q", "--tb=line"],
                    timeout=180,
                )
            )
        if not commands and not self.parser_dogfood_fixture and test_rel is None:
            return WorkerResult(
                worker_id=self.worker_id,
                task_id=task.id,
                task_family="verify",
                ok=False,
                summary="verify_requires_test_file_or_fixture_parser_dogfood",
                artifacts={
                    "commands": [],
                    "worktree": handle.to_dict(),
                    "parser_dogfood_fixture": self.parser_dogfood_fixture,
                },
                finished_at=utc_now().isoformat(),
            )
        ok = all(c.get("ok") for c in commands) if commands else False
        return WorkerResult(
            worker_id=self.worker_id,
            task_id=task.id,
            task_family="verify",
            ok=ok,
            summary="verify_complete" if ok else "verify_failed",
            artifacts={
                "commands": commands,
                "worktree": handle.to_dict(),
                "parser_dogfood_fixture": self.parser_dogfood_fixture,
                "focused_check_paths": (
                    [str(test_rel)] if test_rel is not None else []
                ),
            },
            finished_at=utc_now().isoformat(),
        )

    def _review(
        self,
        task: TaskSpec,
        *,
        handle: WorktreeHandle,
        prior: dict[str, WorkerResult],
    ) -> WorkerResult:
        diff = worktree_diff(handle)
        verify = next((r for r in prior.values() if r.task_family == "verify"), None)
        implement = next((r for r in prior.values() if r.task_family == "implement"), None)
        banned = any(
            token in diff.lower()
            for token in ("api_key", "begin private key", "aws_secret", ".env=")
        )
        decision = "accept"
        reasons: list[str] = []
        if banned:
            decision = "reject"
            reasons.append("secret_like_content_in_diff")
        if not diff.strip():
            decision = "reject"
            reasons.append("no_material_diff")
        if verify is None or not verify.ok:
            decision = "reject"
            reasons.append("verification_failed")
        if implement is None or not implement.ok:
            decision = "reject"
            reasons.append("implementation_missing")
        if decision == "accept":
            reasons.append("verification_passed_and_diff_clean")

        changed_paths = changed_paths_from_diff(diff)
        if implement is not None:
            impl_files = implement.artifacts.get("changed_files") or []
            for item in impl_files:
                path = str(item)
                if path and path not in changed_paths:
                    changed_paths.append(path)
        target_hint = ", ".join(changed_paths[:5]) if changed_paths else "the changed file"
        verify_commands = (
            list((verify.artifacts or {}).get("commands") or []) if verify else []
        )
        focused_raw = task.inputs.get("focused_check_paths") or task.inputs.get(
            "test_file"
        )
        focused_paths: list[str] = []
        if isinstance(focused_raw, list):
            focused_paths = [str(x) for x in focused_raw if str(x).strip()]
        elif isinstance(focused_raw, str) and focused_raw.strip():
            focused_paths = [focused_raw.strip()]
        if verify is not None:
            for item in (verify.artifacts or {}).get("focused_check_paths") or []:
                path = str(item)
                if path and path not in focused_paths:
                    focused_paths.append(path)
            for cmd in verify_commands:
                if not isinstance(cmd, dict):
                    continue
                argv = cmd.get("cmd") or cmd.get("argv") or []
                if isinstance(argv, list):
                    for token in argv:
                        text = str(token)
                        if text.startswith("tests/") and text not in focused_paths:
                            focused_paths.append(text)

        review_inference: InferenceResult | None = None
        if decision == "accept":
            review_inference = self._chat(
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Summarize in 2 sentences whether the patch to "
                            f"{target_hint} is correct for THIS diff only. "
                            "Name the changed file(s) and the defect being fixed. "
                            "Do not discuss unrelated modules or prior missions.\n"
                            f"Diff:\n{diff[:3000]}"
                        ),
                    }
                ],
                model=self._model_for("review"),
                max_tokens=160,
            )

        review_text = ""
        if review_inference is not None:
            review_text = str(review_inference.text or "")

        grounding = ground_semantic_review(
            review_text=review_text,
            diff_text=diff,
            target_paths=changed_paths or None,
            verify_commands=verify_commands,
            focused_check_paths=focused_paths or None,
            allow_dogfood_symbols=bool(self.parser_dogfood_fixture),
        )
        if decision == "accept" and not grounding.grounded:
            decision = "reject"
            reasons = list(dict.fromkeys([*reasons, *grounding.reasons]))

        # Independent checks control acceptance — not the worker claim alone.
        produced = {
            "checks": {
                "verification_passed": verify is not None and bool(verify.ok),
                "implementation_present": implement is not None and bool(implement.ok),
                "diff_clean": not banned,
                "review_grounded": grounding.grounded,
            },
            "intentionally_wrong": decision != "accept",
        }
        independent = review_attempt(
            produced=produced,
            required_checks={
                "verification_passed": True,
                "implementation_present": True,
                "diff_clean": True,
                "review_grounded": True,
            },
        )
        if not independent.accepted:
            decision = "reject"
            reasons = list(dict.fromkeys([*reasons, *independent.reasons]))

        return WorkerResult(
            worker_id=self.worker_id,
            task_id=task.id,
            task_family="review",
            ok=decision == "accept",
            summary=decision,
            artifacts={
                "decision": decision,
                "reasons": reasons,
                "diff_excerpt": diff[:4000],
                "changed_paths": changed_paths,
                "competing_solutions": [
                    {
                        "worker_id": implement.worker_id if implement else None,
                        "ok": implement.ok if implement else False,
                    }
                ],
                "review_notes": review_inference.to_dict() if review_inference else None,
                "independent_review": independent.to_dict(),
                "review_grounding": grounding.to_dict(),
            },
            inference=review_inference.to_dict() if review_inference else None,
            cost_usd=(review_inference.cost_usd if review_inference else 0.0),
            finished_at=utc_now().isoformat(),
        )
