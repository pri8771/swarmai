#!/usr/bin/env python3
"""TH-03: Mac connector completes a mac_local scoped task through the server.

Runs on the Mac host (or mac-connector container) against the authoritative
loopback server. Free/local only. Server must remain up after this process exits.
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from swarm.workers.mac_connector import (  # noqa: E402
    MacConnectorClient,
    dump_evidence,
    load_bearer_token,
    perform_mac_local_extract,
    write_mac_local_fixture,
)

EVIDENCE_DIR = ROOT / "docs" / "evidence" / "two-host" / "TH-03"
FIXTURE_DIR = ROOT / "var" / "mac-connector" / "fixtures"


def main() -> int:
    server_url = (os.environ.get("SWARM_SERVER_URL") or "http://127.0.0.1:18766").rstrip("/")
    token = load_bearer_token(root=ROOT)
    run_id = uuid.uuid4().hex[:12]
    evidence: dict[str, object] = {
        "packet": "TH-03",
        "hostname_public": "swarm.splitsignal.ai",
        "server_url": server_url,
        "connector_role": "mac_connector",
        "started_at": datetime.now(UTC).isoformat(),
        "spend_usd": 0,
        "allow_paid": False,
        "steps": [],
    }

    fixture_path = write_mac_local_fixture(FIXTURE_DIR, run_id=run_id)
    work = perform_mac_local_extract(fixture_path)
    evidence["mac_local_fixture"] = str(fixture_path)
    evidence["steps"].append(
        {
            "step": "mac_local_fixture",
            "ok": fixture_path.is_file(),
            "email_count": work.email_count,
        }
    )

    with MacConnectorClient(server_url=server_url, bearer_token=token) as connector:
        ready = connector.health_ready()
        evidence["health_ready"] = ready
        evidence["steps"].append({"step": "server_ready_before", "ok": True})

        project_id = connector.ensure_project(run_id=run_id)
        evidence["project_id"] = project_id
        evidence["steps"].append({"step": "ensure_project", "ok": True, "project_id": project_id})

        connector.enroll(project_id=project_id, run_id=run_id)
        worker_id = connector.worker_id
        evidence["worker_id"] = worker_id
        evidence["steps"].append(
            {
                "step": "enroll_mac_connector",
                "ok": bool(worker_id and connector.membership_token),
                "worker_id": worker_id,
                "privacy": ["mac_local", "local"],
                "membership_token_prefix": (connector.membership_token or "")[:6],
            }
        )

        connector.heartbeat()
        evidence["steps"].append({"step": "heartbeat", "ok": True})

        workers = connector.list_workers(project_id)
        listed = workers.get("workers") or []
        worker_listed = any((w.get("worker_id") or w.get("id")) == worker_id for w in listed)
        privacy_ok = False
        for row in listed:
            if (row.get("worker_id") or row.get("id")) == worker_id:
                privacy_ok = "mac_local" in (row.get("privacy") or [])
        evidence["steps"].append(
            {
                "step": "list_workers_mac_privacy",
                "ok": worker_listed and privacy_ok,
                "worker_listed": worker_listed,
                "privacy_ok": privacy_ok,
            }
        )
        if not (worker_listed and privacy_ok):
            raise SystemExit("mac connector not visible with mac_local privacy")

        created = connector.create_mac_scoped_mission(
            project_id=project_id,
            run_id=run_id,
            required_checks=work.required_checks(),
        )
        mission = created["mission"]
        mission_id = mission["id"]
        evidence["mission_id"] = mission_id
        evidence["steps"].append(
            {
                "step": "create_mac_scoped_mission",
                "ok": True,
                "mission_id": mission_id,
                "support": created.get("support"),
            }
        )

        # Wrong host claim must fail protected checks.
        forged = connector.review(
            mission_id=mission_id,
            run_id=run_id,
            idempotency_suffix="forged",
            produced={
                "checks": {
                    **work.required_checks(),
                    "artifact_sha256": "0" * 64,
                    "host_role": "server_worker",
                },
                "worker_id": worker_id,
            },
        )
        if forged.get("accepted") is True:
            raise SystemExit("forged_mac_review_accepted")
        evidence["steps"].append(
            {
                "step": "reject_non_mac_or_forged",
                "ok": forged.get("accepted") is False,
                "reasons": (forged.get("review") or {}).get("reasons"),
            }
        )

        accepted = connector.review(
            mission_id=mission_id,
            run_id=run_id,
            idempotency_suffix="ok",
            produced=work.produced(worker_id=worker_id or "", run_id=run_id),
        )
        if accepted.get("accepted") is not True:
            raise SystemExit(f"mac_review_not_accepted:{accepted}")
        evidence["acceptance_receipt_id"] = accepted.get("acceptance_receipt_id")
        evidence["steps"].append(
            {
                "step": "mac_local_review_accepted",
                "ok": True,
                "acceptance_receipt_id": accepted.get("acceptance_receipt_id"),
            }
        )

        got = connector.get_mission(mission_id)
        status = got["mission"].get("status")
        evidence["final_mission_status"] = status
        evidence["steps"].append(
            {"step": "get_mission_completed", "ok": status == "completed", "status": status}
        )
        if status != "completed":
            raise SystemExit(f"mission_not_completed:{status}")

        ready_after = connector.health_ready()
        evidence["health_ready_after_work"] = ready_after
        evidence["steps"].append(
            {
                "step": "server_ready_after_work",
                "ok": ready_after.get("database") == "up",
            }
        )

    # Connector process ends here — prove server still authoritative/alive.
    import httpx

    post = httpx.get(f"{server_url}/health/ready", timeout=10.0)
    post.raise_for_status()
    post_body = post.json()
    evidence["health_ready_after_connector_exit"] = post_body
    evidence["steps"].append(
        {
            "step": "server_survives_connector_exit",
            "ok": post_body.get("status") == "ready" and post_body.get("database") == "up",
        }
    )

    evidence["finished_at"] = datetime.now(UTC).isoformat()
    evidence["ok"] = all(bool(s.get("ok")) for s in evidence["steps"])  # type: ignore[arg-type]
    out = EVIDENCE_DIR / f"th03-mac-connector-{run_id}.json"
    dump_evidence(out, evidence)
    dump_evidence(EVIDENCE_DIR / "latest.json", evidence)
    print(
        __import__("json").dumps(
            {"ok": evidence["ok"], "evidence": str(out), "mission_id": mission_id},
            indent=2,
        )
    )
    return 0 if evidence["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
