"""Real repository workers operating inside git worktrees."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.mission import TaskSpec
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


def _extract_python_file(text: str) -> str | None:
    fence = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
    if fence:
        return fence.group(1).strip() + "\n"
    if "def inclusive_range_count" in text and "return" in text:
        # Best-effort: take from module docstring/import through end.
        start = text.find('"""')
        if start < 0:
            start = text.find("def inclusive_range_count")
        if start >= 0:
            return text[start:].strip() + "\n"
    return None


class RepoWorker:
    """Reads/searches/edits files and runs approved local commands in a worktree."""

    def __init__(
        self,
        repo: Path,
        *,
        model: str = "gemma3:4b",
        worktree_root: Path | None = None,
    ) -> None:
        self.repo = repo.resolve()
        self.model = model
        self.worktree_root = worktree_root
        self.worker_id = new_id("wrk_")

    def run_task(
        self,
        task: TaskSpec,
        *,
        mission_id: str,
        prior: dict[str, WorkerResult],
        shared_worktree: WorktreeHandle | None = None,
    ) -> tuple[WorkerResult, WorktreeHandle | None]:
        family = task.task_family
        if family == "inspect":
            return self._inspect(task, mission_id=mission_id), shared_worktree
        if family == "implement":
            return self._implement(task, mission_id=mission_id, shared=shared_worktree)
        if family == "verify":
            assert shared_worktree is not None
            return self._verify(task, handle=shared_worktree), shared_worktree
        if family == "review":
            assert shared_worktree is not None
            return (
                self._review(task, handle=shared_worktree, prior=prior),
                shared_worktree,
            )
        result = WorkerResult(
            worker_id=self.worker_id,
            task_id=task.id,
            task_family=family,
            ok=False,
            summary=f"unsupported_task_family:{family}",
            finished_at=utc_now().isoformat(),
        )
        return result, shared_worktree

    def _inspect(self, task: TaskSpec, *, mission_id: str) -> WorkerResult:
        target = self.repo / OFF_BY_ONE_REL
        findings = {
            "mission_id": mission_id,
            "goal": task.inputs.get("goal"),
            "candidate_files": [],
            "strategy": "structured_scan",
        }
        if target.exists():
            text = target.read_text(encoding="utf-8")
            findings["candidate_files"].append(str(OFF_BY_ONE_REL))
            findings["off_by_one_suspected"] = "end - start" in text and "+ 1" not in text
            findings["file_preview"] = text[:500]
        # Also detect missing cost CLI as optional improvement signal.
        cost_cli_hint = not (self.repo / "src" / "swarm" / "cost" / "ledger.py").exists()
        findings["missing_cost_ledger"] = cost_cli_hint
        ok = bool(findings["candidate_files"]) or cost_cli_hint
        return WorkerResult(
            worker_id=self.worker_id,
            task_id=task.id,
            task_family="inspect",
            ok=ok,
            summary="inspection_complete",
            artifacts={"findings": findings},
            finished_at=utc_now().isoformat(),
        )

    def _implement(
        self, task: TaskSpec, *, mission_id: str, shared: WorktreeHandle | None
    ) -> tuple[WorkerResult, WorktreeHandle]:
        handle = shared or create_worktree(
            self.repo,
            mission_id=mission_id,
            task_id=task.id,
            worker_id=self.worker_id,
            base_dir=self.worktree_root,
        )
        target = handle.path / OFF_BY_ONE_REL
        original = target.read_text(encoding="utf-8") if target.exists() else ""
        prompt = (
            "You are fixing a Python bug in SwarmAI. Return ONLY the full corrected "
            "file contents for parser_helper.py. Function inclusive_range_count(start, end) "
            "must count integers from start to end inclusive. Current file:\n\n"
            f"{original}"
        )
        inference = local_chat(
            messages=[
                {"role": "system", "content": "Return only valid Python source for the file."},
                {"role": "user", "content": prompt},
            ],
            model=self.model,
            repo_root=self.repo,
        )
        patched = _extract_python_file(inference.text) if inference.ok else None
        # Deterministic fallback keeps zero-spend dogfood reliable if model drifts.
        if patched is None or "end - start + 1" not in patched:
            patched = GOOD_FIX
            used_fallback = True
        else:
            used_fallback = False
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(patched, encoding="utf-8")
        diff = worktree_diff(handle)
        result = WorkerResult(
            worker_id=self.worker_id,
            task_id=task.id,
            task_family="implement",
            ok=bool(diff.strip()) or patched != original,
            summary="implement_applied",
            artifacts={
                "worktree": handle.to_dict(),
                "changed_files": [str(OFF_BY_ONE_REL)],
                "diff": diff[-12000:],
                "used_model_fallback": used_fallback,
            },
            inference=inference.to_dict(),
            cost_usd=inference.cost_usd,
            finished_at=utc_now().isoformat(),
        )
        return result, handle

    def _verify(self, task: TaskSpec, *, handle: WorktreeHandle) -> WorkerResult:
        commands: list[dict[str, Any]] = []
        # Unit test for the touched sample (no network).
        test_file = handle.path / OFF_BY_ONE_TEST_REL
        if test_file.exists():
            commands.append(
                _run_cmd(
                    handle.path / "sandbox" / "selfdev_issue",
                    ["python", "parser_helper_test.py"],
                    timeout=30,
                )
            )
        mission_tests = handle.path / "tests" / "mission"
        if mission_tests.is_dir() and (handle.path / "pyproject.toml").exists():
            commands.append(
                _run_cmd(
                    handle.path,
                    ["uv", "run", "pytest", "tests/mission", "-q", "--tb=line"],
                    timeout=180,
                )
            )
        ok = all(c.get("ok") for c in commands) if commands else False
        return WorkerResult(
            worker_id=self.worker_id,
            task_id=task.id,
            task_family="verify",
            ok=ok,
            summary="verify_complete" if ok else "verify_failed",
            artifacts={"commands": commands, "worktree": handle.to_dict()},
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
        if verify is None or not verify.ok:
            decision = "reject"
            reasons.append("verification_failed")
        if implement is None or not implement.ok:
            decision = "reject"
            reasons.append("implementation_missing")
        if decision == "accept":
            reasons.append("verification_passed_and_diff_clean")

        review_inference: InferenceResult | None = None
        if decision == "accept":
            review_inference = local_chat(
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Summarize in 2 sentences whether this inclusive_range_count "
                            "fix is correct. Diff:\n"
                            f"{diff[:3000]}"
                        ),
                    }
                ],
                model=self.model,
                max_tokens=120,
                repo_root=self.repo,
            )

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
                "competing_solutions": [
                    {
                        "worker_id": implement.worker_id if implement else None,
                        "ok": implement.ok if implement else False,
                    }
                ],
                "review_notes": review_inference.to_dict() if review_inference else None,
            },
            inference=review_inference.to_dict() if review_inference else None,
            cost_usd=(review_inference.cost_usd if review_inference else 0.0),
            finished_at=utc_now().isoformat(),
        )
