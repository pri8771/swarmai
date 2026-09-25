#!/usr/bin/env python3
"""TH-02: native worker completes a mission on the authoritative loopback server.

Talks to the running Compose API (default http://127.0.0.1:18766). Free/local only.
Does not touch R730, DNS, Cloudflare, paid routes, or inference_server.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = os.environ.get("SWARM_SERVER_URL", "http://127.0.0.1:18766")
EVIDENCE_DIR = ROOT / "docs" / "evidence" / "two-host" / "TH-02"


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


def _native_extract(payload: str) -> dict[str, object]:
    """Deterministic native extract work — no model calls."""
    emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", payload)))
    digest = hashlib.sha256(("|".join(emails) + "\n" + payload).encode("utf-8")).hexdigest()
    return {
        "emails": emails,
        "email_count": len(emails),
        "artifact_sha256": digest,
        "runtime": "native",
        "spend_usd": 0,
    }


def main() -> int:
    base = DEFAULT_BASE.rstrip("/")
    token = _load_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    run_id = uuid.uuid4().hex[:12]
    evidence: dict[str, object] = {
        "packet": "TH-02",
        "hostname_public": "swarm.splitsignal.ai",
        "server_url": base,
        "started_at": datetime.now(UTC).isoformat(),
        "spend_usd": 0,
        "allow_paid": False,
        "steps": [],
    }

    with httpx.Client(base_url=base, headers=headers, timeout=30.0) as client:
        ready = client.get("/health/ready")
        ready.raise_for_status()
        ready_body = ready.json()
        evidence["health_ready"] = ready_body
        if ready_body.get("database") != "up":
            raise SystemExit(f"database not up: {ready_body}")
        evidence["steps"].append({"step": "health_ready", "ok": True})

        # Create/ensure project under install principal's project id.
        proj = client.post(
            "/v1/projects",
            headers={**headers, "Idempotency-Key": f"th02-proj-{run_id}"},
            json={
                "name": "TH-02 Mac loopback",
                "repo_path": "/app",
                "allowed_tools": ["extract", "chat"],
                "provider_policy": {"allow_paid": False, "prefer_local": True},
                "budgets": {"max_cost_usd": 0.0, "max_requests": 20},
                "safety": {"require_approval_for_writes": True},
            },
        )
        if proj.status_code >= 400:
            raise SystemExit(f"create_project failed: {proj.status_code} {proj.text}")
        project = proj.json()["project"]
        project_id = project["project_id"]
        evidence["project_id"] = project_id
        evidence["steps"].append({"step": "create_project", "ok": True, "project_id": project_id})

        fixture_text = (
            "Contact alpha@example.com and beta@splitsignal.ai about TH-02 native extract.\n"
            f"run_id={run_id}\n"
        )
        native = _native_extract(fixture_text)
        required_checks = {
            "email_count": native["email_count"],
            "artifact_sha256": native["artifact_sha256"],
            "runtime": "native",
        }

        mission_body = {
            "mission": {
                "project_id": project_id,
                "objective": "TH-02 native extract on authoritative loopback server",
                "acceptance_criteria": [
                    "native worker enrolled",
                    "extract checks match protected required_checks",
                    "mission completed via API review",
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
            "required_checks": required_checks,
        }
        created = client.post(
            "/v1/missions",
            headers={**headers, "Idempotency-Key": f"th02-msn-{run_id}"},
            json=mission_body,
        )
        if created.status_code >= 400:
            raise SystemExit(f"create_mission failed: {created.status_code} {created.text}")
        mission = created.json()["mission"]
        mission_id = mission["id"]
        evidence["mission_id"] = mission_id
        evidence["steps"].append(
            {
                "step": "create_mission",
                "ok": True,
                "mission_id": mission_id,
                "status": mission.get("status"),
                "support": created.json().get("support"),
            }
        )

        enrolled = client.post(
            "/v1/workers/enroll",
            headers={**headers, "Idempotency-Key": f"th02-wrk-{run_id}"},
            json={
                "project_id": project_id,
                "capabilities": ["extract", "chat", "code.read"],
                "capacity_units": 1.0,
                "privacy_classes": ["local"],
            },
        )
        if enrolled.status_code >= 400:
            raise SystemExit(f"enroll failed: {enrolled.status_code} {enrolled.text}")
        enroll_body = enrolled.json()
        worker = enroll_body["worker"]
        membership_token = enroll_body["membership_token"]
        worker_id = worker.get("worker_id") or worker.get("id")
        generation = int(worker.get("lease_generation") or worker.get("generation") or 1)
        evidence["worker_id"] = worker_id
        evidence["steps"].append(
            {
                "step": "enroll_worker",
                "ok": True,
                "worker_id": worker_id,
                "generation": generation,
                "membership_token_prefix": membership_token[:6],
            }
        )

        hb = client.post(
            "/v1/workers/heartbeat",
            json={
                "worker_id": worker_id,
                "generation": generation,
                "token": membership_token,
            },
        )
        if hb.status_code >= 400:
            raise SystemExit(f"heartbeat failed: {hb.status_code} {hb.text}")
        evidence["steps"].append({"step": "worker_heartbeat", "ok": True})

        workers = client.get("/v1/workers", params={"project_id": project_id})
        workers.raise_for_status()
        listed = workers.json().get("workers") or []
        worker_listed = any(
            (w.get("worker_id") or w.get("id")) == worker_id for w in listed
        )
        evidence["steps"].append(
            {
                "step": "list_workers",
                "ok": worker_listed,
                "count": len(listed),
            }
        )
        if not worker_listed:
            raise SystemExit("enrolled worker not visible via authoritative /v1/workers")

        # Negative control: forged / wrong result must not accept.
        forged = client.post(
            f"/v1/missions/{mission_id}/review",
            headers={**headers, "Idempotency-Key": f"th02-forged-{run_id}"},
            json={
                "produced": {
                    "checks": {
                        "email_count": 999,
                        "artifact_sha256": "0" * 64,
                        "runtime": "native",
                    },
                    "worker_id": worker_id,
                },
                "force_wrong": False,
            },
        )
        if forged.status_code >= 400:
            raise SystemExit(f"forged review request failed: {forged.status_code} {forged.text}")
        forged_body = forged.json()
        if forged_body.get("accepted") is True:
            raise SystemExit("forged review incorrectly accepted")
        evidence["steps"].append(
            {
                "step": "reject_forged_review",
                "ok": True,
                "accepted": forged_body.get("accepted"),
                "reasons": (forged_body.get("review") or {}).get("reasons"),
            }
        )

        # Native worker submits genuine produced checks matching protected required_checks.
        review = client.post(
            f"/v1/missions/{mission_id}/review",
            headers={**headers, "Idempotency-Key": f"th02-ok-{run_id}"},
            json={
                "produced": {
                    "checks": required_checks,
                    "worker_id": worker_id,
                    "native_extract": native,
                    "fixture_run_id": run_id,
                },
            },
        )
        if review.status_code >= 400:
            raise SystemExit(f"review failed: {review.status_code} {review.text}")
        review_body = review.json()
        if review_body.get("accepted") is not True:
            raise SystemExit(f"genuine review not accepted: {review_body}")
        receipt = review_body.get("acceptance_receipt_id")
        evidence["acceptance_receipt_id"] = receipt
        evidence["steps"].append(
            {
                "step": "native_review_accepted",
                "ok": True,
                "acceptance_receipt_id": receipt,
            }
        )

        got = client.get(f"/v1/missions/{mission_id}")
        got.raise_for_status()
        got_mission = got.json()["mission"]
        status = got_mission.get("status")
        evidence["final_mission_status"] = status
        evidence["steps"].append(
            {
                "step": "get_mission_completed",
                "ok": status == "completed",
                "status": status,
                "acceptance_receipt_id": got_mission.get("acceptance_receipt_id"),
            }
        )
        if status != "completed":
            raise SystemExit(f"mission not completed: {status}")

        report = client.get(f"/v1/missions/{mission_id}/report")
        report_ok = report.status_code == 200
        evidence["steps"].append(
            {
                "step": "mission_report",
                "ok": report_ok,
                "status_code": report.status_code,
            }
        )

    evidence["finished_at"] = datetime.now(UTC).isoformat()
    evidence["ok"] = all(bool(s.get("ok")) for s in evidence["steps"])  # type: ignore[union-attr]
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE_DIR / f"th02-native-mission-{run_id}.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    latest = EVIDENCE_DIR / "latest.json"
    latest.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": evidence["ok"], "evidence": str(out), "mission_id": mission_id}, indent=2))
    return 0 if evidence["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
