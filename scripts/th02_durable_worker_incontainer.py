#!/usr/bin/env python3
"""TH-02 durable PG worker protocol proof — run INSIDE the API container.

Uses DurableWorkerService + WorkerClient against the authoritative Postgres.
No paid inference. Invoked via:
  docker compose -f deploy/compose/server.yml exec -T api \
    python /app/scripts/th02_durable_worker_incontainer.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from swarm.contracts.common import new_id
from swarm.contracts.enums import MissionStatus, TaskStatus
from swarm.contracts.fixtures import sample_mission, sample_task
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import TaskRow
from swarm.db.repositories import MissionRepository
from swarm.workers.client import WorkerClient
from swarm.workers.envelopes import EnrollmentRequest
from swarm.workers.service import DurableWorkerService
from swarm.workers.transport import InProcessWorkerTransport


def main() -> int:
    url = os.environ.get("SWARM_DATABASE_URL")
    if not url:
        print(json.dumps({"ok": False, "error": "SWARM_DATABASE_URL missing"}))
        return 2
    engine = create_db_engine(url)
    ping(engine)
    factory = make_session_factory(engine)
    session = factory()
    evidence: dict[str, object] = {
        "packet": "TH-02",
        "path": "durable_worker_postgres",
        "started_at": datetime.now(UTC).isoformat(),
        "spend_usd": 0,
        "steps": [],
    }
    try:
        mission = sample_mission().model_copy(
            update={
                "id": new_id("msn_"),
                "project_id": new_id("proj_th02_"),
                "status": MissionStatus.RUNNING,
                "objective": "TH-02 durable native worker claim/submit",
            }
        )
        MissionRepository(session).insert(mission)
        session.flush()
        evidence["mission_id"] = mission.id
        evidence["project_id"] = mission.project_id

        task = sample_task(mission_id=mission.id).model_copy(
            update={
                "id": new_id("tsk_"),
                "project_id": mission.project_id,
                "required_capabilities": ["code.read"],
                "scopes": ["scope_repo_demo"],
                "status": TaskStatus.READY,
                "priority": 10,
                "graph_revision": mission.revision,
            }
        )
        session.add(
            TaskRow(
                id=task.id,
                project_id=mission.project_id,
                mission_id=mission.id,
                objective=task.objective,
                task_family=task.task_family,
                status="ready",
                graph_revision=mission.revision,
                priority=10,
                scopes=list(task.scopes),
                dependency_ids=[],
                payload=task.model_dump(mode="json"),
            )
        )
        session.flush()
        evidence["task_id"] = task.id
        evidence["steps"].append({"step": "seed_mission_task", "ok": True})

        client = WorkerClient(
            transport=InProcessWorkerTransport(DurableWorkerService(session))
        )
        enrolled = client.enroll(
            EnrollmentRequest(
                host_alias="mac-loopback-th02",
                project_id=mission.project_id,
                capabilities=["code.read", "chat"],
                trust_class="compute_only",
            )
        )
        evidence["worker_id"] = enrolled.worker_id
        evidence["steps"].append(
            {
                "step": "enroll",
                "ok": enrolled.membership_token.startswith("wt_"),
                "generation": enrolled.generation,
            }
        )

        hb = client.heartbeat(health={"executor": "ready", "runtime": "native"})
        evidence["steps"].append({"step": "heartbeat", "ok": hb.status == "online"})

        claimed = client.claim()
        evidence["steps"].append(
            {
                "step": "claim",
                "ok": bool(claimed.claimed and claimed.lease_id),
                "lease_id": claimed.lease_id,
            }
        )
        if not claimed.claimed or not claimed.lease_id:
            raise RuntimeError("claim_failed")

        renewed = client.renew(lease_id=claimed.lease_id, progress_class="running")
        evidence["steps"].append({"step": "renew", "ok": renewed.state == "renewed"})

        submitted = client.submit_result(
            lease_id=claimed.lease_id,
            status="succeeded",
            checks={"review_passed": True, "runtime": "native"},
            artifact_manifest={"sha256": "th02" + "ab" * 30},
            summary="th02 native durable worker succeeded",
        )
        evidence["result_id"] = submitted.result_id
        evidence["steps"].append(
            {
                "step": "submit_result",
                "ok": bool(submitted.result_id),
                "result_id": submitted.result_id,
            }
        )

        accepted = client.control_plane_accept(result_id=submitted.result_id)
        evidence["steps"].append(
            {
                "step": "accept_result",
                "ok": getattr(accepted, "acceptance_state", None) == "accepted"
                or getattr(accepted, "accepted", False) is True,
                "acceptance_state": getattr(accepted, "acceptance_state", None),
                "accepted": getattr(accepted, "accepted", None),
            }
        )
        session.commit()
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        evidence["error"] = f"{type(exc).__name__}:{exc}"
        evidence["ok"] = False
        print(json.dumps(evidence, indent=2))
        return 1
    finally:
        session.close()

    evidence["finished_at"] = datetime.now(UTC).isoformat()
    evidence["ok"] = all(bool(s.get("ok")) for s in evidence["steps"])  # type: ignore[arg-type]
    out_dir = Path("/app/var/artifacts/th02")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "durable-worker-latest.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    evidence["evidence_path"] = str(out)
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
