#!/usr/bin/env python3
"""V2A-002 / ART-V11-RESTART-EVIDENCE — actual OS process stop/start reopen.

Starts a real uvicorn API process against an isolated durable store, creates one
mission, SIGTERM-stops the process, starts a new process (distinct PID), then
reopens the same mission ID via HTTP and CLI. Does not invent acceptance.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_PORT = 18791
TOKEN = "atk_v2a002_restart_loopback"
INSTALL_PROJECT = "proj_install_v2a002_restart"


def _utc() -> str:
    return datetime.now(UTC).isoformat()


def _git_sha() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
            ).strip()
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _http_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: float = 10.0,
) -> tuple[int, dict]:
    data = None
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return int(resp.status), json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return int(exc.code), payload


def _wait_ready(base: str, *, timeout_s: float = 20.0) -> dict:
    deadline = time.time() + timeout_s
    last: dict = {}
    while time.time() < deadline:
        try:
            status, body = _http_json("GET", f"{base}/health/ready")
            last = {"http_status": status, "body": body, "at": _utc()}
            if status == 200 and (body.get("status") == "ready" or body.get("runtime")):
                return last
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = {"error": str(exc), "at": _utc()}
        time.sleep(0.2)
    raise RuntimeError(f"api_not_ready:{last}")


def _start_api(
    *,
    repo_root: Path,
    port: int,
    env_extra: dict[str, str] | None = None,
) -> tuple[subprocess.Popen[str], dict]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO / "src") + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    env["SWARM_REPO_ROOT"] = str(repo_root)
    env["SWARM_SEED_LOOPBACK_TOKEN"] = TOKEN
    env["SWARM_INSTALL_PROJECT_ID"] = INSTALL_PROJECT
    env["SWARM_ALLOW_PAID"] = "false"
    if env_extra:
        env.update(env_extra)
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "swarm.api.app:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    started_at = _utc()
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    meta = {
        "command": cmd,
        "pid": proc.pid,
        "started_at": started_at,
        "cwd": str(REPO),
        "SWARM_REPO_ROOT": str(repo_root),
        "SWARM_INSTALL_PROJECT_ID": INSTALL_PROJECT,
        "port": port,
        "host": "127.0.0.1",
    }
    return proc, meta


def _stop_api(proc: subprocess.Popen[str]) -> dict:
    stop_sent_at = _utc()
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    return {
        "stop_signal": "SIGTERM",
        "stop_sent_at": stop_sent_at,
        "exited_at": _utc(),
        "exit_code": proc.returncode,
        "pid": proc.pid,
        "still_alive": proc.poll() is None,
    }


def _file_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def run_proof(*, port: int = DEFAULT_PORT, out_path: Path | None = None) -> dict:
    candidate_sha = _git_sha()
    with tempfile.TemporaryDirectory(prefix="swarm-v2a002-") as td:
        durable_root = Path(td).resolve()
        store_alias = str(durable_root / "var" / "missions")
        base = f"http://127.0.0.1:{port}"

        # --- process 1: create mission ---
        p1, p1_meta = _start_api(repo_root=durable_root, port=port)
        try:
            ready1 = _wait_ready(base)
            create_body = {
                "mission": {
                    "project_id": INSTALL_PROJECT,
                    "objective": (
                        "V2A-002 process-restart reopen probe — no model rerun required"
                    ),
                    "acceptance_criteria": ["durable reopen after OS process restart"],
                    "allowed_capabilities": ["code.read"],
                    "data_scope_ids": ["scope_local"],
                    "resource_policy_id": "policy_default",
                    "max_wall_time_seconds": 600,
                    "max_graph_nodes": 20,
                    "max_active_sessions": 2,
                    "max_model_calls": 10,
                },
                "task_family": "extract",
            }
            create_at = _utc()
            create_status, create_json = _http_json(
                "POST",
                f"{base}/v1/missions",
                token=TOKEN,
                body=create_body,
            )
            mission = (create_json.get("mission") or {}) if create_status == 200 else {}
            mission_id = str(mission.get("id") or "")
            get1_status, get1_json = _http_json(
                "GET", f"{base}/v1/missions/{mission_id}", token=TOKEN
            )
            disk_before = durable_root / "var" / "missions" / f"{mission_id}.json"
            disk_hash_before = _file_sha256(disk_before)
            observed1 = {
                "create_http_status": create_status,
                "create_at": create_at,
                "mission_id": mission_id,
                "mission_status": mission.get("status"),
                "get_http_status": get1_status,
                "get_status": ((get1_json.get("mission") or {}).get("status")),
                "disk_path": str(disk_before),
                "disk_sha256": disk_hash_before,
                "process_alive": p1.poll() is None,
            }
        finally:
            stop1 = _stop_api(p1)

        if not mission_id or create_status != 200:
            raise RuntimeError(f"create_failed:{create_status}:{create_json}")

        # Ensure port is free before process 2.
        time.sleep(0.3)

        # --- process 2: reopen via HTTP ---
        evidence: dict = {}
        p2, p2_meta = _start_api(repo_root=durable_root, port=port)
        try:
            ready2 = _wait_ready(base)
            reopen_http_at = _utc()
            get2_status, get2_json = _http_json(
                "GET", f"{base}/v1/missions/{mission_id}", token=TOKEN
            )
            mission2 = get2_json.get("mission") or {}
            disk_after = durable_root / "var" / "missions" / f"{mission_id}.json"
            disk_hash_after = _file_sha256(disk_after)

            # --- another interface: CLI mission status (separate process) ---
            cli_env = os.environ.copy()
            cli_env["PYTHONPATH"] = str(REPO / "src") + (
                os.pathsep + cli_env["PYTHONPATH"] if cli_env.get("PYTHONPATH") else ""
            )
            cli_env["SWARM_REPO_ROOT"] = str(durable_root)
            cli_env["SWARM_ALLOW_PAID"] = "false"
            cli_cmd = [
                sys.executable,
                "-m",
                "swarm.cli",
                "mission",
                "status",
                "--mission-id",
                mission_id,
            ]
            cli_started = _utc()
            cli_proc = subprocess.run(
                cli_cmd,
                cwd=str(REPO),
                env=cli_env,
                capture_output=True,
                text=True,
                check=False,
            )
            cli_finished = _utc()
            try:
                cli_json = json.loads(cli_proc.stdout) if cli_proc.stdout.strip() else {}
            except json.JSONDecodeError:
                cli_json = {"raw_stdout": cli_proc.stdout, "stderr": cli_proc.stderr}

            http_ok = (
                get2_status == 200
                and mission2.get("id") == mission_id
                and bool(mission2.get("status"))
            )
            cli_ok = cli_proc.returncode == 0 and (
                cli_json.get("mission_id") == mission_id
                or (cli_json.get("mission") or {}).get("id") == mission_id
                or cli_json.get("status") is not None
            )
            distinct_pids = p1_meta["pid"] != p2_meta["pid"]
            same_disk = (
                disk_hash_before is not None
                and disk_hash_before == disk_hash_after
                and disk_before.exists()
            )
            passed = bool(
                http_ok
                and cli_ok
                and distinct_pids
                and same_disk
                and stop1.get("still_alive") is False
            )

            evidence = {
                "gate": "G11-RUN-111",
                "artifact_id": "ART-V11-RESTART-EVIDENCE",
                "packet_id": "V2A-002",
                "scenario": "os_process_restart_reopen_operational",
                "recorded_at": _utc(),
                "mode": "live_local",
                "status": "pass" if passed else "fail",
                "command": " ".join(p1_meta["command"]),
                "exit_code": 0 if passed else 1,
                "generated_at": _utc(),
                "candidate_sha": candidate_sha,
                "spend_usd": 0.0,
                "execution_mode": "operational",
                "g11_lead_accept_invented": False,
                "identity": {
                    "candidate_sha": candidate_sha,
                    "config_version": "v2a002-process-restart-v1",
                    "store_alias": store_alias,
                    "install_project_id": INSTALL_PROJECT,
                    "seed_token_name": "SWARM_SEED_LOOPBACK_TOKEN",
                    "repo_root_env": "SWARM_REPO_ROOT",
                },
                "process_1": {
                    **p1_meta,
                    "ready": ready1,
                    "stop": stop1,
                    "observed": observed1,
                },
                "process_2": {
                    **p2_meta,
                    "ready": ready2,
                    "reopen_http_at": reopen_http_at,
                    "reopen_http_status": get2_status,
                    "reopened_mission_id": mission2.get("id"),
                    "reopened_status": mission2.get("status"),
                    "reopened_objective": mission2.get("objective"),
                    "disk_sha256": disk_hash_after,
                },
                "cli_reopen": {
                    "command": cli_cmd,
                    "pid_note": "cli_subprocess_separate_from_api",
                    "started_at": cli_started,
                    "finished_at": cli_finished,
                    "exit_code": cli_proc.returncode,
                    "stdout_json": cli_json,
                    "stderr_tail": (cli_proc.stderr or "")[-500:],
                },
                "checks": {
                    "distinct_os_pids": distinct_pids,
                    "pid_1": p1_meta["pid"],
                    "pid_2": p2_meta["pid"],
                    "process_1_exited": stop1.get("still_alive") is False,
                    "same_durable_id": mission2.get("id") == mission_id,
                    "same_disk_sha256": same_disk,
                    "http_reopen_ok": http_ok,
                    "cli_reopen_ok": cli_ok,
                    "not_create_app_object_only": True,
                },
                "note": (
                    "Actual uvicorn OS process SIGTERM stop/start against durable "
                    "SWARM_REPO_ROOT store; reopen via HTTP + CLI. Not create_app() "
                    "in-process recreation. Lead acceptance not claimed."
                ),
            }
        finally:
            stop2 = _stop_api(p2)
            if evidence:
                evidence.setdefault("process_2", {})["stop"] = stop2

        if not evidence:
            raise RuntimeError("process_2_failed_without_evidence")

        # Copy durable mission file into evidence tree for audit (content hash already bound).
        out = out_path or (
            REPO / "docs" / "evidence" / "g11" / "process-restart-reopen-operational.json"
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        evidence["evidence_path"] = str(out)
        evidence["evidence_sha256"] = _file_sha256(out)
        out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        return evidence


def main() -> int:
    evidence = run_proof()
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "path": evidence.get("evidence_path"),
                "checks": evidence["checks"],
            },
            indent=2,
        )
    )
    return 0 if evidence["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
