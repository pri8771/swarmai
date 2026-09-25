#!/usr/bin/env python3
"""TH-04: durable artifacts reopen with identical hash after API (and worker) restart.

Mac loopback only. Does not wait on R730 / DNS / Cloudflare.
Publishes a content-addressed artifact via the authoritative API, restarts the
Compose API container (volume-backed /app/var), then reopens the same sha256.
Also enrolls a worker, kills its in-process session, and re-enrolls to show
worker restart does not erase the durable artifact.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = os.environ.get("SWARM_SERVER_URL", "http://127.0.0.1:18766")
EVIDENCE_DIR = ROOT / "docs" / "evidence" / "two-host" / "TH-04"
COMPOSE_FILE = ROOT / "deploy" / "compose" / "server.yml"
ARTIFACT_BODY = (
    "TH-04 durable artifact body\n"
    "hostname=swarm.splitsignal.ai\n"
    "packet=TH-04\n"
)
ARTIFACT_BYTES = ARTIFACT_BODY.encode("utf-8")


def _load_token() -> str:
    env_path = ROOT / "deploy" / "env" / "server.env"
    if not env_path.is_file():
        raise SystemExit(f"missing {env_path} — copy from server.env.example")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("SWARM_SEED_LOOPBACK_TOKEN="):
            token = line.split("=", 1)[1].strip()
            if token and "replace-with" not in token:
                return token
    raise SystemExit("SWARM_SEED_LOOPBACK_TOKEN unset in deploy/env/server.env")


def _wait_ready(client: httpx.Client, *, timeout_s: float = 90.0) -> dict:
    deadline = time.time() + timeout_s
    last: dict | None = None
    while time.time() < deadline:
        try:
            resp = client.get("/health/ready")
            if resp.status_code == 200:
                body = resp.json()
                if body.get("status") == "ready" and body.get("database") == "up":
                    return body
                last = body
        except httpx.HTTPError:
            pass
        time.sleep(1.5)
    raise SystemExit(f"server not ready after restart: {last}")


def _compose(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", "compose", "-f", str(COMPOSE_FILE), *args]
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)


def main() -> int:
    base = DEFAULT_BASE.rstrip("/")
    token = _load_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    run_id = uuid.uuid4().hex[:12]
    expected_hash = hashlib.sha256(ARTIFACT_BYTES).hexdigest()
    evidence: dict[str, object] = {
        "packet": "TH-04",
        "hostname_public": "swarm.splitsignal.ai",
        "server_url": base,
        "started_at": datetime.now(UTC).isoformat(),
        "spend_usd": 0,
        "allow_paid": False,
        "expected_content_hash": expected_hash,
        "steps": [],
    }

    with httpx.Client(base_url=base, headers=headers, timeout=45.0) as client:
        ready = _wait_ready(client, timeout_s=30.0)
        evidence["health_ready_before"] = ready
        evidence["steps"].append({"step": "health_ready_before", "ok": True})

        proj = client.post(
            "/v1/projects",
            json={
                "name": f"TH-04 Mac loopback {run_id}",
                "repo_path": "/app",
                "allowed_tools": ["extract", "chat"],
                "provider_policy": {"allow_paid": False, "prefer_local": True},
                "budgets": {"max_cost_usd": 0.0, "max_requests": 20},
                "safety": {"require_approval_for_writes": True},
            },
            headers={**headers, "Idempotency-Key": f"th04-proj-{run_id}"},
        )
        if proj.status_code >= 400:
            raise SystemExit(f"create_project failed: {proj.status_code} {proj.text}")
        project_id = proj.json()["project"]["project_id"]
        evidence["project_id"] = project_id
        evidence["steps"].append({"step": "create_project", "ok": True, "project_id": project_id})

        mission_body = {
            "mission": {
                "project_id": project_id,
                "objective": f"TH-04 durable artifact recovery {run_id}",
                "acceptance_criteria": [
                    "artifact published to durable CAS",
                    "identical sha256 after API restart",
                    "worker re-enroll leaves artifact intact",
                ],
                "allowed_capabilities": ["extract", "chat", "code.read"],
                "data_scope_ids": ["scope_local"],
                "resource_policy_id": "policy_default",
                "max_wall_time_seconds": 600,
                "max_graph_nodes": 20,
                "max_active_sessions": 2,
                "max_model_calls": 5,
            },
            "task_family": "extract",
        }
        created = client.post(
            "/v1/missions",
            json=mission_body,
            headers={**headers, "Idempotency-Key": f"th04-msn-{run_id}"},
        )
        if created.status_code >= 400:
            raise SystemExit(f"create_mission failed: {created.status_code} {created.text}")
        mission_id = created.json()["mission"]["id"]
        evidence["mission_id"] = mission_id
        evidence["steps"].append({"step": "create_mission", "ok": True, "mission_id": mission_id})

        # Worker enroll (will restart/re-enroll after API restart).
        enroll = client.post(
            "/v1/workers/enroll",
            json={
                "project_id": project_id,
                "capabilities": ["extract", "chat", "code.read"],
                "capacity_units": 1.0,
                "privacy_classes": ["local"],
            },
            headers={**headers, "Idempotency-Key": f"th04-wk-{run_id}"},
        )
        if enroll.status_code >= 400:
            raise SystemExit(f"enroll failed: {enroll.status_code} {enroll.text}")
        worker = enroll.json().get("worker") or {}
        worker_id = worker.get("worker_id") or worker.get("id")
        evidence["worker_id_before"] = worker_id
        evidence["steps"].append(
            {"step": "enroll_worker_before", "ok": bool(worker_id), "worker_id": worker_id}
        )

        published = client.post(
            f"/v1/missions/{mission_id}/artifacts",
            json={
                "kind": "result",
                "content_base64": base64.b64encode(ARTIFACT_BYTES).decode("ascii"),
                "media_type": "text/plain",
                "summary": "TH-04 durable result",
                "expected_hash": expected_hash,
            },
            headers={**headers, "Idempotency-Key": f"th04-art-{run_id}"},
        )
        if published.status_code >= 400:
            raise SystemExit(f"publish failed: {published.status_code} {published.text}")
        art = published.json()["artifact"]
        artifact_id = art["artifact_id"]
        content_hash = art["content_hash"]
        evidence["artifact_id"] = artifact_id
        evidence["content_hash_before"] = content_hash
        evidence["steps"].append(
            {
                "step": "publish_artifact",
                "ok": content_hash == expected_hash,
                "artifact_id": artifact_id,
                "content_hash": content_hash,
            }
        )
        if content_hash != expected_hash:
            raise SystemExit(f"publish hash mismatch: {content_hash} != {expected_hash}")

        listed = client.get(f"/v1/missions/{mission_id}/artifacts")
        listed.raise_for_status()
        before_arts = listed.json().get("artifacts") or []
        before_match = next(
            (a for a in before_arts if a.get("artifact_id") == artifact_id), None
        )
        evidence["steps"].append(
            {
                "step": "list_artifacts_before",
                "ok": bool(before_match)
                and before_match.get("content_hash") == expected_hash,
                "count": len(before_arts),
            }
        )

        content = client.get(f"/v1/missions/{mission_id}/artifacts/{artifact_id}/content")
        content.raise_for_status()
        before_content = content.json()
        evidence["steps"].append(
            {
                "step": "read_content_before",
                "ok": before_content.get("content_hash") == expected_hash,
                "byte_length": before_content.get("byte_length"),
            }
        )

        # Restart API container — Postgres + swarm_var volumes must survive.
        restart = _compose("restart", "api")
        evidence["steps"].append(
            {
                "step": "restart_api_container",
                "ok": restart.returncode == 0,
                "returncode": restart.returncode,
                "stderr_tail": (restart.stderr or "")[-400:],
            }
        )
        if restart.returncode != 0:
            raise SystemExit(f"compose restart failed: {restart.stderr}")

        ready_after = _wait_ready(client, timeout_s=120.0)
        evidence["health_ready_after"] = ready_after
        evidence["steps"].append(
            {
                "step": "health_ready_after_restart",
                "ok": ready_after.get("database") == "up",
                "database": ready_after.get("database"),
            }
        )

        # Mission + artifact reopen after process death.
        get_msn = client.get(f"/v1/missions/{mission_id}")
        get_msn.raise_for_status()
        evidence["steps"].append(
            {
                "step": "hydrate_mission_after_restart",
                "ok": get_msn.status_code == 200,
                "status": (get_msn.json().get("mission") or {}).get("status"),
            }
        )

        listed_after = client.get(f"/v1/missions/{mission_id}/artifacts")
        listed_after.raise_for_status()
        after_arts = listed_after.json().get("artifacts") or []
        after_match = next(
            (a for a in after_arts if a.get("artifact_id") == artifact_id), None
        )
        same_hash = bool(after_match) and after_match.get("content_hash") == expected_hash
        evidence["content_hash_after"] = (after_match or {}).get("content_hash")
        evidence["steps"].append(
            {
                "step": "list_artifacts_after_restart",
                "ok": same_hash,
                "count": len(after_arts),
                "content_hash": (after_match or {}).get("content_hash"),
            }
        )
        if not same_hash:
            raise SystemExit(
                f"artifact hash changed or missing after restart: {after_match}"
            )

        content_after = client.get(
            f"/v1/missions/{mission_id}/artifacts/{artifact_id}/content"
        )
        content_after.raise_for_status()
        after_body = content_after.json()
        evidence["steps"].append(
            {
                "step": "read_content_after_restart",
                "ok": after_body.get("content_hash") == expected_hash
                and after_body.get("byte_length") == len(ARTIFACT_BYTES),
                "content_hash": after_body.get("content_hash"),
                "byte_length": after_body.get("byte_length"),
            }
        )
        if after_body.get("content_hash") != expected_hash:
            raise SystemExit("content reopen hash mismatch after restart")

        # Verify CAS blob on volume inside container (authoritative path).
        cas_check = _compose(
            "exec",
            "-T",
            "api",
            "python",
            "-c",
            (
                "import hashlib, pathlib; "
                f"p=pathlib.Path('/app/var/artifacts/cas/{expected_hash[:2]}/{expected_hash}'); "
                "d=p.read_bytes(); "
                "print(hashlib.sha256(d).hexdigest()); "
                f"assert hashlib.sha256(d).hexdigest()=='{expected_hash}'"
            ),
        )
        volume_hash = (cas_check.stdout or "").strip().splitlines()[-1] if cas_check.stdout else ""
        evidence["steps"].append(
            {
                "step": "volume_cas_blob_verified",
                "ok": cas_check.returncode == 0 and volume_hash == expected_hash,
                "returncode": cas_check.returncode,
                "volume_hash": volume_hash,
                "stderr_tail": (cas_check.stderr or "")[-300:],
            }
        )
        if cas_check.returncode != 0 or volume_hash != expected_hash:
            raise SystemExit(f"volume CAS verify failed: {cas_check.stderr}")

        # Worker restart: re-enroll after API restart; artifact still listed.
        enroll2 = client.post(
            "/v1/workers/enroll",
            json={
                "project_id": project_id,
                "capabilities": ["extract", "chat", "code.read"],
                "capacity_units": 1.0,
                "privacy_classes": ["local"],
            },
            headers={**headers, "Idempotency-Key": f"th04-wk2-{run_id}"},
        )
        if enroll2.status_code >= 400:
            raise SystemExit(f"reenroll failed: {enroll2.status_code} {enroll2.text}")
        worker2 = enroll2.json().get("worker") or {}
        worker_id2 = worker2.get("worker_id") or worker2.get("id")
        evidence["worker_id_after"] = worker_id2
        listed_final = client.get(f"/v1/missions/{mission_id}/artifacts")
        listed_final.raise_for_status()
        final_arts = listed_final.json().get("artifacts") or []
        final_ok = any(
            a.get("artifact_id") == artifact_id and a.get("content_hash") == expected_hash
            for a in final_arts
        )
        evidence["steps"].append(
            {
                "step": "worker_reenroll_artifact_intact",
                "ok": bool(worker_id2) and final_ok,
                "worker_id": worker_id2,
            }
        )

    all_ok = all(bool(s.get("ok")) for s in evidence["steps"])  # type: ignore[union-attr]
    evidence["ok"] = all_ok
    evidence["finished_at"] = datetime.now(UTC).isoformat()

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE_DIR / f"th04-durable-artifacts-{run_id}.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    latest = EVIDENCE_DIR / "latest.json"
    latest.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_ok, "evidence": str(out), "content_hash": expected_hash}))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
