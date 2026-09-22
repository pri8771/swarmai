#!/usr/bin/env python3
"""SwarmAI hourly check-in worker (FIX-004).

Single-instance lease, bounded wall time, sanitized evidence.
Does not spend money. Does not invent live acceptance.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOST_ALIAS = os.environ.get("SWARM_HOST_ALIAS", "mac-local")
STATE_DIR = Path(
    os.environ.get(
        "SWARM_HOURLY_STATE_DIR",
        Path.home() / "Library/Application Support/SwarmAI/hourly-runner",
    )
)
LOCK_PATH = STATE_DIR / "hourly.lock"
STATE_PATH = STATE_DIR / "state.json"
LOG_PATH = STATE_DIR / "checkins.jsonl"
DEFAULT_MAX_SECONDS = int(os.environ.get("SWARM_HOURLY_MAX_SECONDS", "3000"))
STALE_LOCK_SECONDS = int(os.environ.get("SWARM_HOURLY_STALE_LOCK_SECONDS", "3600"))


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()  # noqa: UP017


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire_lock() -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    now = time.time()
    if LOCK_PATH.exists():
        try:
            existing = json.loads(LOCK_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            existing = {}
        pid = int(existing.get("pid") or 0)
        started = float(existing.get("started_epoch") or 0)
        if _pid_alive(pid) and now - started < STALE_LOCK_SECONDS:
            raise SystemExit(
                f"busy: another hourly worker holds the lease (pid={pid})"
            )
        # Stale lock recovery
        LOCK_PATH.unlink(missing_ok=True)

    payload = {
        "pid": os.getpid(),
        "started_epoch": now,
        "started_at": utc_now(),
        "host_alias": HOST_ALIAS,
    }
    fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    return payload


def release_lock() -> None:
    try:
        data = json.loads(LOCK_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        LOCK_PATH.unlink(missing_ok=True)
        return
    if int(data.get("pid") or 0) == os.getpid():
        LOCK_PATH.unlink(missing_ok=True)


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {
            "invocation_count": 0,
            "scheduler_checkins": 0,
            "manual_checkins": 0,
            "last_run_at": None,
            "cursor_agent_auth": "unknown",
            "recurring_verified": False,
        }
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


def run_cmd(argv: list[str], timeout: int = 60) -> dict:
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "argv": argv,
            "returncode": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-800:],
            "stderr_tail": (proc.stderr or "")[-800:],
        }
    except FileNotFoundError as exc:
        return {"argv": argv, "error": str(exc)}
    except subprocess.TimeoutExpired:
        return {"argv": argv, "error": "timeout"}


def probe_cursor_agent() -> dict:
    if os.environ.get("SWARM_HOURLY_SKIP_CURSOR_PROBE", "0") == "1":
        return {
            "auth_status": "skipped",
            "which": {"skipped": True},
            "version": {"skipped": True},
            "agent_probe": {"skipped": True},
        }
    which = run_cmd(["/usr/bin/which", "cursor"], timeout=5)
    version = run_cmd(["cursor", "--version"], timeout=10)
    # Keep agent probe short so launchd jobs cannot hang the lease.
    agent = run_cmd(["cursor", "agent", "--list-models"], timeout=15)
    auth = "authenticated"
    if agent.get("returncode") not in (0, None):
        err = (agent.get("stderr_tail") or "") + (agent.get("stdout_tail") or "")
        if "Authentication required" in err or "api-key" in err.lower():
            auth = "auth_required"
        else:
            auth = "probe_failed"
    elif agent.get("error"):
        auth = "unavailable"
    return {
        "which": which,
        "version": version,
        "agent_probe": agent,
        "auth_status": auth,
    }


def git_tips(repo: Path) -> dict:
    if os.environ.get("SWARM_HOURLY_SKIP_REPO", "0") == "1":
        return {"skipped": True, "reason": "SWARM_HOURLY_SKIP_REPO=1", "repo": str(repo)}
    tips: dict = {}
    if not (repo / ".git").exists():
        return {"error": "no_git_or_unreadable", "repo": str(repo)}
    for label, argv in (
        ("head", ["git", "-C", str(repo), "rev-parse", "HEAD"]),
        ("branch", ["git", "-C", str(repo), "branch", "--show-current"]),
        ("origin_main", ["git", "-C", str(repo), "rev-parse", "origin/main"]),
        (
            "origin_coord",
            [
                "git",
                "-C",
                str(repo),
                "rev-parse",
                "origin/coordination/swarm-control",
            ],
        ),
    ):
        tips[label] = run_cmd(argv, timeout=15)
    # Scheduler jobs skip network fetch by default to stay bounded/offline-safe.
    if os.environ.get("SWARM_HOURLY_FETCH", "0") == "1":
        tips["fetch"] = run_cmd(
            [
                "git",
                "-C",
                str(repo),
                "fetch",
                "origin",
                "main",
                "coordination/swarm-control",
            ],
            timeout=60,
        )
    else:
        tips["fetch"] = {"skipped": True, "reason": "SWARM_HOURLY_FETCH!=1"}
    return tips


def append_log(entry: dict) -> None:
    with LOG_PATH.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="SwarmAI hourly check-in")
    parser.add_argument(
        "--repo",
        default=os.environ.get(
            "SWARM_HOURLY_REPO",
            str(Path(__file__).resolve().parents[2]),
        ),
    )
    parser.add_argument(
        "--trigger",
        choices=("manual", "scheduler", "install-verify"),
        default="manual",
    )
    parser.add_argument(
        "--max-seconds",
        type=int,
        default=DEFAULT_MAX_SECONDS,
    )
    parser.add_argument(
        "--spawn-agent",
        action="store_true",
        help="Attempt cursor agent -p only if auth is verified (default: probe only)",
    )
    args = parser.parse_args()
    started = time.time()
    lock = acquire_lock()
    try:
        repo = Path(args.repo).resolve()
        state = load_state()
        cursor = probe_cursor_agent()
        try:
            tips = git_tips(repo)
        except OSError as exc:
            tips = {"error": f"repo_unreadable:{exc}"}
        state["invocation_count"] = int(state.get("invocation_count") or 0) + 1
        if args.trigger == "scheduler":
            state["scheduler_checkins"] = int(state.get("scheduler_checkins") or 0) + 1
        elif args.trigger == "manual":
            state["manual_checkins"] = int(state.get("manual_checkins") or 0) + 1
        state["last_run_at"] = utc_now()
        state["last_trigger"] = args.trigger
        state["cursor_agent_auth"] = cursor["auth_status"]
        state["host_alias"] = HOST_ALIAS
        state["repo"] = str(repo)
        # Recurring verified only after 1 any + 2 scheduler check-ins observed.
        if int(state.get("scheduler_checkins") or 0) >= 2 and int(
            state.get("invocation_count") or 0
        ) >= 3:
            state["recurring_verified"] = True
        agent_spawn = {
            "attempted": False,
            "reason": "probe_only_default",
        }
        if args.spawn_agent:
            if cursor["auth_status"] != "authenticated":
                agent_spawn = {
                    "attempted": False,
                    "reason": f"blocked:{cursor['auth_status']}",
                    "operator_action": "cursor agent login (zero-spend entitlement required)",
                }
            else:
                # Bounded: ask mode only — no unpaid cloud spend assumed.
                agent_spawn = {
                    "attempted": True,
                    "result": run_cmd(
                        [
                            "cursor",
                            "agent",
                            "-p",
                            "--mode",
                            "ask",
                            "SwarmAI hourly heartbeat only. "
                            "Report current branch SHA; do not modify files.",
                        ],
                        timeout=min(120, args.max_seconds),
                    ),
                }
        elapsed = time.time() - started
        entry = {
            "at": utc_now(),
            "trigger": args.trigger,
            "host_alias": HOST_ALIAS,
            "pid": os.getpid(),
            "lock_started_at": lock.get("started_at"),
            "elapsed_seconds": round(elapsed, 3),
            "max_seconds": args.max_seconds,
            "bounded_ok": elapsed < args.max_seconds,
            "cursor": {
                "auth_status": cursor["auth_status"],
                "version_stdout": (cursor.get("version") or {}).get("stdout_tail"),
            },
            "git": tips,
            "agent_spawn": agent_spawn,
            "state_snapshot": {
                "invocation_count": state["invocation_count"],
                "scheduler_checkins": state.get("scheduler_checkins"),
                "manual_checkins": state.get("manual_checkins"),
                "recurring_verified": state.get("recurring_verified"),
            },
        }
        save_state(state)
        append_log(entry)
        # Sanitized evidence copy into repo when writable (may fail under TCC).
        # Tests set SWARM_HOURLY_REPO_EVIDENCE=0 so a check-in never dirties a checkout.
        if os.environ.get("SWARM_HOURLY_REPO_EVIDENCE", "1") != "0":
            evidence_dir = repo / "docs" / "evidence" / "fix-004"
            try:
                evidence_dir.mkdir(parents=True, exist_ok=True)
                (evidence_dir / "last-checkin.json").write_text(
                    json.dumps(entry, indent=2) + "\n"
                )
                (evidence_dir / "runner-state.json").write_text(
                    json.dumps(state, indent=2) + "\n"
                )
            except OSError as exc:
                entry["repo_evidence_error"] = str(exc)
        else:
            entry["repo_evidence_skipped"] = True
        # Always mirror evidence under Application Support (LaunchAgent-safe).
        try:
            local_ev = STATE_DIR / "evidence"
            local_ev.mkdir(parents=True, exist_ok=True)
            (local_ev / "last-checkin.json").write_text(
                json.dumps(entry, indent=2) + "\n"
            )
            (local_ev / "runner-state.json").write_text(
                json.dumps(state, indent=2) + "\n"
            )
        except OSError:
            pass
        print(json.dumps(entry, indent=2))
        if not entry["bounded_ok"]:
            return 2
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    sys.exit(main())
