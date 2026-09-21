#!/usr/bin/env python3
"""SwarmAI durable coordination heartbeat.

Publishes a sanitized host/session heartbeat to coordination/swarm-control
through the authenticated GitHub CLI. The OS scheduler may wake every 15
minutes; HEARTBEAT_STATE.json controls the effective publication cadence.
"""

from __future__ import annotations

import argparse
import base64
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


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def run(argv: list[str], *, stdin: str | None = None, timeout: int = 45) -> str:
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


def read_json_file(repo: str, path: str) -> tuple[str, dict]:
    data = gh_api(contents_endpoint(repo, path, ref=COORD_BRANCH))
    raw = base64.b64decode(str(data["content"]).encode()).decode()
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"coord_json_not_object:{path}")
    return str(data["sha"]), parsed


def remote_sha(repo: str, ref: str) -> str:
    data = gh_api(f"repos/{repo}/commits/{quote(ref, safe='')}")
    return str(data["sha"])


def state_root(host: str) -> Path:
    override = os.environ.get("SWARM_COORD_HEARTBEAT_STATE_DIR")
    if override:
        return Path(override).expanduser()
    home = Path.home()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or (home / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = home / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_STATE_HOME") or (home / ".local" / "state"))
    return base / "SwarmAI" / f"coord-heartbeat-{host}"


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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-slug", default=DEFAULT_REPO)
    p.add_argument("--host", required=True)
    p.add_argument("--session", required=True)
    p.add_argument("--branch", required=True)
    p.add_argument("--trigger", default="manual")
    p.add_argument("--packet")
    p.add_argument("--artifact")
    p.add_argument("--status")
    p.add_argument("--note")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    root = state_root(args.host)
    root.mkdir(parents=True, exist_ok=True)
    local_state_path = root / "state.json"
    context_path = root / "session-context.json"

    context = load_json(
        context_path,
        {
            "packet_id": None,
            "artifact_id": None,
            "status": "bootstrap",
            "note": None,
            "last_agent_activity_at": None,
        },
    )
    if args.packet is not None:
        context["packet_id"] = args.packet
    if args.artifact is not None:
        context["artifact_id"] = args.artifact
    if args.status is not None:
        context["status"] = args.status
    if args.note is not None:
        context["note"] = args.note[:300]
    if any(v is not None for v in (args.packet, args.artifact, args.status, args.note)):
        context["last_agent_activity_at"] = utc_now()
        write_json_private(context_path, context)

    _, hb_state = read_json_file(
        args.repo_slug, "docs/coordination/HEARTBEAT_STATE.json"
    )
    cadence = int(hb_state.get("worker_effective_cadence_minutes") or 15)

    # Scheduler cadence is tracked independently from manual/work heartbeats.
    # A forced packet-status update must never reset/suppress the 15-minute
    # scheduler proof clock.
    local_state = load_json(
        local_state_path,
        {"last_sent_epoch": 0.0, "last_scheduler_sent_epoch": 0.0},
    )
    now_epoch = time.time()
    last_sent = float(local_state.get("last_sent_epoch") or 0.0)
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
    path = f"docs/coordination/heartbeats/{args.host}.json"
    blob_sha, current = read_json_file(args.repo_slug, path)

    observed_at = utc_now()
    entry = {
        "observed_at": observed_at,
        "trigger": args.trigger,
        "host_alias": args.host,
        "session_id": args.session,
        "branch": args.branch,
        "branch_sha": branch_sha,
        "coordination_sha": coord_sha,
        "effective_cadence_minutes": cadence,
        "packet_id": context.get("packet_id"),
        "artifact_id": context.get("artifact_id"),
        "status": context.get("status") or "unknown",
        "last_agent_activity_at": context.get("last_agent_activity_at"),
        "note": (str(context.get("note"))[:300] if context.get("note") else None),
    }
    history = list(current.get("history") or [])[-11:]
    history.append(entry)
    document = {
        "schema_version": "1.0",
        "host_alias": args.host,
        "session_id": args.session,
        "branch": args.branch,
        "last_heartbeat": entry,
        "history": history,
        "status": entry["status"],
    }
    encoded = base64.b64encode(
        (json.dumps(document, indent=2) + "\n").encode()
    ).decode()
    body = {
        "message": f"heartbeat({args.host}): {observed_at}",
        "content": encoded,
        "branch": COORD_BRANCH,
        "sha": blob_sha,
    }
    gh_api(contents_endpoint(args.repo_slug, path), method="PUT", payload=body)

    local_state.update(
        {
            "last_sent_epoch": now_epoch,
            "last_sent_at": observed_at,
            "last_branch_sha": branch_sha,
            "last_coord_sha": coord_sha,
            "effective_cadence_minutes": cadence,
        }
    )
    if args.trigger == "scheduler":
        local_state["last_scheduler_sent_epoch"] = now_epoch
        local_state["last_scheduler_sent_at"] = observed_at
    write_json_private(local_state_path, local_state)
    print(json.dumps(entry, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
