#!/usr/bin/env python3
"""SwarmAI single-session coordination heartbeat (CURSOR-V17-SINGLE).

Publishes sanitized progress to coordination/swarm-control via the
authenticated GitHub CLI. Exactly one producer is allowed. Does not write
legacy HOST-MAC-DEV / HOST-WIN-DEV ledgers.
"""

from __future__ import annotations

import argparse
import base64
import fcntl
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

COORD_BRANCH = "coordination/swarm-control"
DEFAULT_REPO = "pri8771/swarmai"
SESSION_ID = "CURSOR-V17-SINGLE"
SESSION_EPOCH = "single-v17-20260921-01"
DEFAULT_BRANCH = "cursor/v17-single-session"
LEDGER_PATH = "docs/coordination/heartbeats/CURSOR-V17-SINGLE.json"
STATUS_PATH = "docs/coordination/status/CURSOR-V17-SINGLE.md"
HB_STATE_PATH = "docs/coordination/HEARTBEAT_STATE.json"
LOCK_NAME = "heartbeat.lock"
PID_NAME = "heartbeat.pid"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(argv: list[str], *, stdin: str | None = None, timeout: int = 60) -> str:
    proc = subprocess.run(
        argv,
        input=stdin,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"command_failed:{argv[0]}:{proc.returncode}:"
            f"{(proc.stderr or proc.stdout or '')[-500:]}"
        )
    return proc.stdout


def gh_bin() -> str:
    return os.environ.get("SWARM_GH_PATH") or "gh"


def gh_api(endpoint: str, *, method: str = "GET", payload: dict | None = None) -> dict:
    argv = [gh_bin(), "api"]
    stdin = None
    if method != "GET":
        argv += ["--method", method, "--input", "-"]
        stdin = json.dumps(payload or {})
    argv.append(endpoint)
    out = run(argv, stdin=stdin)
    data = json.loads(out or "{}")
    if not isinstance(data, dict):
        raise RuntimeError("github_api_non_object")
    return data


def contents_endpoint(repo: str, path: str, *, ref: str | None = None) -> str:
    ep = f"repos/{repo}/contents/{quote(path, safe='/')}"
    if ref:
        ep += f"?ref={quote(ref, safe='')}"
    return ep


def read_file(repo: str, path: str) -> tuple[str, str]:
    data = gh_api(contents_endpoint(repo, path, ref=COORD_BRANCH))
    raw = base64.b64decode(str(data["content"]).encode()).decode()
    return str(data["sha"]), raw


def read_json_file(repo: str, path: str) -> tuple[str, dict]:
    blob_sha, raw = read_file(repo, path)
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"coord_json_not_object:{path}")
    return blob_sha, parsed


def put_file(repo: str, path: str, *, content: str, message: str, blob_sha: str) -> dict:
    encoded = base64.b64encode(content.encode()).decode()
    return gh_api(
        contents_endpoint(repo, path),
        method="PUT",
        payload={
            "message": message,
            "content": encoded,
            "branch": COORD_BRANCH,
            "sha": blob_sha,
        },
    )


def remote_sha(repo: str, ref: str) -> str:
    data = gh_api(f"repos/{repo}/commits/{quote(ref, safe='')}")
    return str(data["sha"])


def state_root() -> Path:
    override = os.environ.get("SWARM_COORD_HEARTBEAT_STATE_DIR")
    if override:
        return Path(override).expanduser()
    home = Path.home()
    if sys.platform == "darwin":
        base = home / "Library" / "Application Support"
    elif os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or (home / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_STATE_HOME") or (home / ".local" / "state"))
    return base / "SwarmAI" / "coord-heartbeat-v17"


def load_json(path: Path, default: dict) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(default)
    return data if isinstance(data, dict) else dict(default)


def write_json_private(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    if os.name != "nt":
        os.chmod(path, 0o600)


def acquire_lock(root: Path) -> object:
    """Exclusive flock + PID guard. Caller must keep the returned handle alive."""
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / LOCK_NAME
    handle = open(lock_path, "a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise RuntimeError("duplicate_heartbeat_producer_lock_held") from exc
    handle.seek(0)
    handle.truncate()
    handle.write(f"pid={os.getpid()} started={utc_now()}\n")
    handle.flush()
    (root / PID_NAME).write_text(str(os.getpid()) + "\n", encoding="utf-8")
    return handle


def render_status(entry: dict) -> str:
    blocker = entry.get("blocker") or "none"
    note = entry.get("short_note") or "No additional note."
    packet = entry.get("current_packet") or "none"
    artifact = entry.get("current_artifact") or "none"
    activity = entry.get("last_meaningful_activity_at") or "none recorded"
    return f"""# CURSOR-V17-SINGLE status

- Session: `{entry["session_id"]}`
- Epoch: `{entry["session_epoch"]}`
- Branch: `{entry["branch"]}`
- Branch SHA: `{entry["branch_sha"]}`
- Coordination SHA: `{entry.get("coordination_sha") or "unknown"}`
- Updated: `{entry["timestamp_utc"]}`
- Trigger: `{entry["trigger"]}`
- Status: **{entry.get("status") or "unknown"}**
- Current packet: `{packet}`
- Current artifact: `{artifact}`
- Last meaningful activity: `{activity}`
- Spend USD: `{entry.get("spend_usd", 0)}`
- Blocker: {blocker}

## Update

{note}

## Next

Continue single-session queue toward V1.7 implementation-complete/reviewable candidate.
"""


def update_heartbeat_state(
    repo: str,
    *,
    status: str,
    timestamp_utc: str,
    register: bool,
) -> None:
    blob_sha, state = read_json_file(repo, HB_STATE_PATH)
    session = dict(state.get("session") or {})
    session["session_id"] = SESSION_ID
    session["branch"] = DEFAULT_BRANCH
    session["ledger"] = LEDGER_PATH
    session["status_page"] = STATUS_PATH
    if register or session.get("registered") is True:
        session["registered"] = True
    session["last_heartbeat_at"] = timestamp_utc
    session["status"] = status
    state["session"] = session
    state["updated_at"] = timestamp_utc
    state["mode"] = "single_session_5m"
    state["active_session_epoch"] = SESSION_EPOCH
    state["producer_limit"] = 1
    state["worker_effective_cadence_minutes"] = 5
    if register:
        state["note"] = (
            "CURSOR-V17-SINGLE producer registered; legacy A/B ledgers are historical only."
        )
    put_file(
        repo,
        HB_STATE_PATH,
        content=json.dumps(state, indent=2) + "\n",
        message=f"heartbeat-state(CURSOR-V17-SINGLE): {timestamp_utc}",
        blob_sha=blob_sha,
    )


def main() -> int:
    p = argparse.ArgumentParser(description="CURSOR-V17-SINGLE coordination heartbeat")
    p.add_argument("--repo-slug", default=DEFAULT_REPO)
    p.add_argument("--branch", default=DEFAULT_BRANCH)
    p.add_argument("--trigger", default="manual")
    p.add_argument("--packet")
    p.add_argument("--artifact")
    p.add_argument("--status")
    p.add_argument("--note")
    p.add_argument("--blocker")
    p.add_argument("--spend-usd", type=float)
    p.add_argument("--force", action="store_true")
    p.add_argument("--skip-state-update", action="store_true")
    args = p.parse_args()

    root = state_root()
    lock_handle = acquire_lock(root)
    try:
        local_state_path = root / "state.json"
        context_path = root / "session-context.json"

        context = load_json(
            context_path,
            {
                "current_packet": "BOOTSTRAP",
                "current_artifact": "cross-version",
                "status": "working",
                "short_note": None,
                "blocker": None,
                "spend_usd": 0,
                "last_meaningful_activity_at": None,
            },
        )
        if args.packet is not None:
            context["current_packet"] = args.packet
        if args.artifact is not None:
            context["current_artifact"] = args.artifact
        if args.status is not None:
            context["status"] = args.status
        if args.note is not None:
            context["short_note"] = args.note[:400]
        if args.blocker is not None:
            context["blocker"] = args.blocker[:400] if args.blocker else None
        if args.spend_usd is not None:
            context["spend_usd"] = float(args.spend_usd)
        if any(
            v is not None
            for v in (args.packet, args.artifact, args.status, args.note, args.blocker, args.spend_usd)
        ):
            context["last_meaningful_activity_at"] = utc_now()
            write_json_private(context_path, context)

        _, hb_state = read_json_file(args.repo_slug, HB_STATE_PATH)
        cadence = int(hb_state.get("worker_effective_cadence_minutes") or 5)

        local_state = load_json(
            local_state_path,
            {"last_sent_epoch": 0.0, "last_scheduler_sent_epoch": 0.0},
        )
        now_epoch = time.time()
        last_scheduler_sent = float(local_state.get("last_scheduler_sent_epoch") or 0.0)
        if (
            args.trigger == "scheduler"
            and not args.force
            and last_scheduler_sent
            and (now_epoch - last_scheduler_sent) < cadence * 60 * 0.8
        ):
            print(
                json.dumps(
                    {
                        "status": "skipped_scheduler_not_due",
                        "effective_cadence_minutes": cadence,
                        "last_scheduler_sent_epoch": last_scheduler_sent,
                    },
                    indent=2,
                )
            )
            return 0

        branch_sha = remote_sha(args.repo_slug, args.branch)
        coord_sha = remote_sha(args.repo_slug, COORD_BRANCH)
        timestamp_utc = utc_now()
        status = str(context.get("status") or "working")
        if args.trigger in {"install", "session_started"} and args.status is None:
            status = "session_started"
            context["status"] = status

        entry = {
            "schema_version": "1.0",
            "session_id": SESSION_ID,
            "session_epoch": SESSION_EPOCH,
            "branch": args.branch,
            "branch_sha": branch_sha,
            "coordination_sha": coord_sha,
            "timestamp_utc": timestamp_utc,
            "trigger": args.trigger,
            "status": status,
            "current_packet": context.get("current_packet"),
            "current_artifact": context.get("current_artifact"),
            "short_note": (
                str(context.get("short_note"))[:400] if context.get("short_note") else None
            ),
            "last_meaningful_activity_at": context.get("last_meaningful_activity_at"),
            "blocker": context.get("blocker"),
            "spend_usd": context.get("spend_usd", 0),
            "effective_cadence_minutes": cadence,
        }

        blob_sha, current = read_json_file(args.repo_slug, LEDGER_PATH)
        history = list(current.get("history") or [])[-19:]
        history.append(entry)
        document = {
            "schema_version": "1.0",
            "session_id": SESSION_ID,
            "session_epoch": SESSION_EPOCH,
            "branch": args.branch,
            "last_heartbeat": entry,
            "history": history,
            "status": entry["status"],
            "timestamp_utc": timestamp_utc,
            "branch_sha": branch_sha,
            "coordination_sha": coord_sha,
            "trigger": args.trigger,
            "current_packet": entry["current_packet"],
            "current_artifact": entry["current_artifact"],
            "short_note": entry["short_note"],
            "last_meaningful_activity_at": entry["last_meaningful_activity_at"],
            "blocker": entry["blocker"],
            "spend_usd": entry["spend_usd"],
        }
        put_file(
            args.repo_slug,
            LEDGER_PATH,
            content=json.dumps(document, indent=2) + "\n",
            message=f"heartbeat(CURSOR-V17-SINGLE): {timestamp_utc}",
            blob_sha=blob_sha,
        )

        status_sha, _ = read_file(args.repo_slug, STATUS_PATH)
        put_file(
            args.repo_slug,
            STATUS_PATH,
            content=render_status(entry),
            message=f"status(CURSOR-V17-SINGLE): {timestamp_utc}",
            blob_sha=status_sha,
        )

        register = status == "session_started" or args.trigger in {"install", "session_started"}
        if not args.skip_state_update:
            update_heartbeat_state(
                args.repo_slug,
                status=status,
                timestamp_utc=timestamp_utc,
                register=register,
            )

        local_state.update(
            {
                "last_sent_epoch": now_epoch,
                "last_sent_at": timestamp_utc,
                "last_branch_sha": branch_sha,
                "last_coord_sha": coord_sha,
                "effective_cadence_minutes": cadence,
            }
        )
        if args.trigger == "scheduler":
            local_state["last_scheduler_sent_epoch"] = now_epoch
            local_state["last_scheduler_sent_at"] = timestamp_utc
        write_json_private(local_state_path, local_state)
        write_json_private(context_path, context)
        print(json.dumps(entry, indent=2))
        return 0
    finally:
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        lock_handle.close()


if __name__ == "__main__":
    raise SystemExit(main())
