#!/usr/bin/env python3
"""Repo-driven bounded Cursor worker.

Polls a canonical GitHub assignment and invokes Cursor CLI non-interactively
for exactly one assignment generation. It never selects its own next packet.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

COORD_BRANCH = "coordination/swarm-control"
DEFAULT_REPO = "pri8771/swarmai"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def run(argv: list[str], *, cwd: Path | None = None, timeout: int = 60, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, input=stdin, text=True, capture_output=True, timeout=timeout, check=False)


def require_ok(proc: subprocess.CompletedProcess[str], label: str) -> str:
    if proc.returncode != 0:
        tail = ((proc.stderr or "") + (proc.stdout or ""))[-600:]
        raise RuntimeError(f"{label}_failed:{proc.returncode}:{tail}")
    return proc.stdout or ""


def gh_bin() -> str:
    return os.environ.get("SWARM_GH_PATH") or "gh"


def gh_api(endpoint: str) -> dict:
    proc = run([gh_bin(), "api", endpoint], timeout=45)
    out = require_ok(proc, "gh_api")
    data = json.loads(out or "{}")
    if not isinstance(data, dict):
        raise RuntimeError("github_api_non_object")
    return data


def read_coord_json(repo_slug: str, path: str) -> dict:
    ep = f"repos/{repo_slug}/contents/{quote(path, safe='/')}?ref={quote(COORD_BRANCH, safe='')}"
    data = gh_api(ep)
    raw = base64.b64decode(str(data["content"]).encode()).decode()
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise RuntimeError(f"coord_json_not_object:{path}")
    return obj


def state_root(host: str) -> Path:
    override = os.environ.get("SWARM_AUTONOMOUS_STATE_DIR")
    if override:
        return Path(override).expanduser()
    home = Path.home()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or (home / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = home / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_STATE_HOME") or (home / ".local" / "state"))
    return base / "SwarmAI" / f"autonomous-worker-{host}"


def load_json(path: Path, default: dict) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(default)
    return data if isinstance(data, dict) else dict(default)


def write_private(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    if os.name != "nt":
        os.chmod(path, 0o600)


def acquire_lock(path: Path, stale_seconds: int) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            age = time.time() - path.stat().st_mtime
        except OSError:
            age = 0
        if age < stale_seconds:
            return False
        path.unlink(missing_ok=True)
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w") as fh:
        fh.write(json.dumps({"pid": os.getpid(), "started_at": utc_now()}) + "\n")
    return True


def heartbeat(workspace: Path, *, host: str, session: str, branch: str, assignment: dict, status: str, note: str) -> None:
    hb = workspace / "scripts" / "coordination" / "heartbeat.py"
    if not hb.exists():
        return
    argv = [
        sys.executable, str(hb),
        "--host", host, "--session", session, "--branch", branch,
        "--packet", str(assignment.get("packet_id") or assignment.get("assignment_id") or "autonomous"),
        "--artifact", str(assignment.get("artifact_id") or "ART-OPS-AUTONOMY"),
        "--status", status, "--note", note[:280], "--force",
    ]
    run(argv, cwd=workspace, timeout=60)


def git(workspace: Path, *args: str, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return run(["git", "-C", str(workspace), *args], timeout=timeout)


def build_prompt(assignment: dict, host: str, session: str, branch: str) -> str:
    instruction = str(assignment.get("instruction_path") or "docs/coordination/WORKER_PACKET_BACKLOG.md")
    return f"""You are SwarmAI Cursor Session {session} on {host}. Execute exactly ONE repo-assigned packet and then stop.

ASSIGNMENT ID: {assignment.get('assignment_id')}
GENERATION: {assignment.get('generation')}
PACKET: {assignment.get('packet_id')}
ARTIFACT: {assignment.get('artifact_id')}
BRANCH: {branch}
INSTRUCTION PATH: {instruction}

Start by reading SESSION_INSTRUCTIONS.md in this branch and fetching current coordination state. Read the assignment source with:
git show origin/{COORD_BRANCH}:{instruction}
Also read current ARTIFACT_REGISTRY.json, WORK_QUEUE.md, WORKER_PACKET_BACKLOG.md, HEARTBEAT_STATE.json, and newest AGENT_MESSAGES.md from origin/{COORD_BRANCH}.

Rules:
- execute exactly this assignment generation; do not choose a second packet;
- preserve existing work and ownership boundaries;
- no main merge, force push, public deploy, release, paid fallback or additional spend;
- no mock success, known-answer substitution, hidden-answer leakage or fabricated evidence;
- run the focused checks/tests required by the packet;
- if a human-only login/MFA/consent barrier exists, do not bypass it; report the precise blocker;
- do not self-accept any artifact;
- commit only owned files with artifact/packet in the commit message;
- push to the assigned branch {branch};
- leave the worktree clean after a successful push;
- produce exact source/evidence refs in your final response.

Do not ask the operator routine questions. Make the best bounded implementation possible and stop after this one packet."""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-slug", default=DEFAULT_REPO)
    p.add_argument("--workspace", required=True)
    p.add_argument("--host", required=True)
    p.add_argument("--session", required=True)
    p.add_argument("--branch", required=True)
    args = p.parse_args()

    workspace = Path(args.workspace).resolve()
    root = state_root(args.host)
    state_path = root / "state.json"
    lock_path = root / "runner.lock"
    log_path = root / "last-agent-output.json"
    state = load_json(state_path, {})

    assignment_path = f"docs/coordination/assignments/{args.host}.json"
    root_assignment = read_coord_json(args.repo_slug, assignment_path)
    if not root_assignment.get("enabled"):
        return 0
    if root_assignment.get("host_alias") != args.host or root_assignment.get("session_id") != args.session or root_assignment.get("branch") != args.branch:
        raise RuntimeError("assignment_identity_mismatch")

    completed_items = set(state.get("completed_item_keys") or [])
    items = root_assignment.get("items")
    if isinstance(items, list) and items:
        assignment = None
        key = None
        for item in items:
            if not isinstance(item, dict):
                continue
            candidate = f"{root_assignment.get('assignment_id')}:{root_assignment.get('generation')}:{item.get('packet_id')}"
            if candidate in completed_items:
                continue
            if state.get("last_started_key") == candidate and state.get("last_completed_key") != candidate:
                # A failed/blocked item requires an explicit new assignment generation.
                return 0
            assignment = {**root_assignment, **item}
            key = candidate
            break
        if assignment is None or key is None:
            return 0
    else:
        assignment = root_assignment
        key = f"{assignment.get('assignment_id')}:{assignment.get('generation')}"
        if state.get("last_completed_key") == key or state.get("last_started_key") == key:
            return 0

    max_seconds = int(assignment.get("max_runtime_seconds") or root_assignment.get("max_runtime_seconds") or 1800)
    if not acquire_lock(lock_path, max_seconds + 900):
        return 0

    try:
        branch_now = require_ok(git(workspace, "branch", "--show-current"), "git_branch").strip()
        if branch_now != args.branch:
            heartbeat(workspace, host=args.host, session=args.session, branch=args.branch, assignment=assignment, status="blocked", note=f"wrong_branch:{branch_now}")
            return 2

        dirty = require_ok(git(workspace, "status", "--porcelain"), "git_status").strip()
        if dirty:
            heartbeat(workspace, host=args.host, session=args.session, branch=args.branch, assignment=assignment, status="blocked", note="autonomous_runner_dirty_worktree")
            return 2

        require_ok(git(workspace, "fetch", "--all", "--prune", timeout=120), "git_fetch")
        require_ok(git(workspace, "pull", "--ff-only", "origin", args.branch, timeout=120), "git_pull")
        before = require_ok(git(workspace, "rev-parse", f"origin/{args.branch}"), "git_before").strip()

        agent = os.environ.get("SWARM_AGENT_PATH") or shutil.which("agent") or shutil.which("cursor-agent")
        if not agent:
            heartbeat(workspace, host=args.host, session=args.session, branch=args.branch, assignment=assignment, status="blocked", note="cursor_cli_missing_run_agent_install")
            return 3

        state.update({"last_started_key": key, "last_started_at": utc_now(), "assignment": assignment})
        write_private(state_path, state)
        heartbeat(workspace, host=args.host, session=args.session, branch=args.branch, assignment=assignment, status="autonomous_working", note=f"assignment={key}")

        prompt = build_prompt(assignment, args.host, args.session, args.branch)
        proc = run([agent, "-p", "--workspace", str(workspace), "--output-format", "json", prompt], cwd=workspace, timeout=max_seconds)
        write_private(log_path, {"at": utc_now(), "returncode": proc.returncode, "stdout": (proc.stdout or "")[-12000:], "stderr": (proc.stderr or "")[-4000:]})

        if proc.returncode != 0:
            state.update({"last_exit_code": proc.returncode, "last_failed_at": utc_now()})
            write_private(state_path, state)
            heartbeat(workspace, host=args.host, session=args.session, branch=args.branch, assignment=assignment, status="blocked", note=f"cursor_agent_exit_{proc.returncode}; check local runner log; lead may increment generation")
            return proc.returncode or 4

        # The agent is responsible for committing/pushing. Verify that it left a clean
        # worktree and that the remote worker branch advanced.
        require_ok(git(workspace, "fetch", "origin", args.branch, timeout=120), "git_fetch_after")
        after = require_ok(git(workspace, "rev-parse", f"origin/{args.branch}"), "git_after").strip()
        dirty_after = require_ok(git(workspace, "status", "--porcelain"), "git_status_after").strip()

        if dirty_after:
            heartbeat(workspace, host=args.host, session=args.session, branch=args.branch, assignment=assignment, status="blocked", note="agent_left_uncommitted_changes; manual_or_lead_review_required")
            state.update({"last_exit_code": 0, "last_blocked_at": utc_now(), "blocked_reason": "dirty_after_agent"})
            write_private(state_path, state)
            return 5

        if after == before:
            heartbeat(workspace, host=args.host, session=args.session, branch=args.branch, assignment=assignment, status="blocked", note="agent_completed_without_remote_branch_change")
            state.update({"last_exit_code": 0, "last_blocked_at": utc_now(), "blocked_reason": "no_remote_change"})
            write_private(state_path, state)
            return 6

        completed_items = list(state.get("completed_item_keys") or [])
        if key not in completed_items:
            completed_items.append(key)
        state.update({
            "last_completed_key": key,
            "completed_item_keys": completed_items,
            "last_completed_at": utc_now(),
            "remote_sha": after,
            "last_exit_code": 0,
        })
        write_private(state_path, state)
        heartbeat(workspace, host=args.host, session=args.session, branch=args.branch, assignment=assignment, status="review_requested", note=f"autonomous assignment complete remote_sha={after[:12]}")
        return 0
    finally:
        lock_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
