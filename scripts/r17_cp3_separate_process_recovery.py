#!/usr/bin/env python3
"""R17 / CP3 — separate-process durable worker recovery proof.

Real OS processes share one Postgres DSN. Sequence:
  register -> claim -> kill -> expire/reassign -> stale reject -> valid accept
  -> duplicate accept race fails -> exactly one accepted result.

Does not invent multi-host proof. No spend.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import signal
import sys
import time
import traceback
from datetime import timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from swarm.contracts.common import new_id, utc_now  # noqa: E402
from swarm.contracts.enums import MissionStatus, TaskStatus  # noqa: E402
from swarm.contracts.fixtures import sample_mission, sample_task  # noqa: E402
from swarm.db.engine import create_db_engine, make_session_factory, ping  # noqa: E402
from swarm.db.lease_fencing import ResultAcceptanceError  # noqa: E402
from swarm.db.models import Base, TaskRow  # noqa: E402
from swarm.db.repositories import MissionRepository  # noqa: E402
from swarm.workers.client import WorkerClient  # noqa: E402
from swarm.workers.envelopes import EnrollmentRequest  # noqa: E402
from swarm.workers.service import DurableWorkerService  # noqa: E402
from swarm.workers.transport import InProcessWorkerTransport  # noqa: E402

CAPS = ["code.read", "chat"]


def _dsn() -> str:
    url = (os.environ.get("SWARM_DATABASE_URL") or "").strip()
    if not url:
        raise SystemExit("SWARM_DATABASE_URL required")
    if "swarm:swarm@" in url:
        raise SystemExit("forbidden demo DSN swarm:swarm")
    return url


def _open_session(url: str):
    engine = create_db_engine(url)
    ping(engine)
    factory = make_session_factory(engine)
    return engine, factory()


def _enroll_client(session, *, project_id: str, host_alias: str) -> WorkerClient:
    service = DurableWorkerService(session)
    client = WorkerClient(InProcessWorkerTransport(service))
    client.enroll(
        EnrollmentRequest(
            host_alias=host_alias,
            project_id=project_id,
            capabilities=list(CAPS),
            trust_class="compute_only",
        )
    )
    return client


def _worker_claim(queue: mp.Queue, dsn: str, project_id: str, host: str) -> None:
    try:
        _engine, session = _open_session(dsn)
        client = _enroll_client(session, project_id=project_id, host_alias=host)
        claimed = client.claim()
        session.commit()
        if not claimed.claimed or not claimed.lease_id:
            queue.put({"ok": False, "error": "claim_failed", "host": host})
            return
        queue.put(
            {
                "ok": True,
                "host": host,
                "pid": os.getpid(),
                "worker_id": client.worker_id,
                "generation": client.generation,
                "membership_token": client.membership_token,
                "lease_id": claimed.lease_id,
                "attempt_id": claimed.attempt_id,
                "task_id": claimed.task_id,
            }
        )
        while True:
            time.sleep(1.0)
    except Exception as exc:  # noqa: BLE001
        queue.put({"ok": False, "error": str(exc), "trace": traceback.format_exc()})


def _worker_reclaim_and_submit(
    queue: mp.Queue, dsn: str, project_id: str, host: str
) -> None:
    try:
        _engine, session = _open_session(dsn)
        client = _enroll_client(session, project_id=project_id, host_alias=host)
        claimed = client.claim()
        if not claimed.claimed or not claimed.lease_id:
            session.commit()
            queue.put({"ok": False, "error": "reclaim_failed"})
            return
        submitted = client.submit_result(
            lease_id=claimed.lease_id,
            status="succeeded",
            checks={"review_passed": True},
            summary="cp3_valid",
        )
        session.commit()
        queue.put(
            {
                "ok": True,
                "pid": os.getpid(),
                "worker_id": client.worker_id,
                "lease_id": claimed.lease_id,
                "attempt_id": claimed.attempt_id,
                "result_id": submitted.result_id,
            }
        )
    except Exception as exc:  # noqa: BLE001
        queue.put({"ok": False, "error": str(exc), "trace": traceback.format_exc()})


def _stale_submit(queue: mp.Queue, dsn: str, creds: dict) -> None:
    try:
        _engine, session = _open_session(dsn)
        service = DurableWorkerService(session)
        client = WorkerClient(InProcessWorkerTransport(service))
        client.worker_id = creds["worker_id"]
        client.generation = int(creds["generation"])
        client.membership_token = creds["membership_token"]
        client.project_id = creds.get("project_id")
        submitted = client.submit_result(
            lease_id=creds["lease_id"],
            status="succeeded",
            checks={"review_passed": True},
            summary="cp3_stale",
        )
        # Persist the durable submission before the accept attempt so a rejected
        # accept cannot roll back the evidence row.
        session.commit()
        rejected = False
        reason = None
        try:
            service.accept_result(result_id=submitted.result_id)
            session.commit()
        except ResultAcceptanceError as exc:
            rejected = True
            reason = str(exc)
            session.commit()  # keep rejection marking if any
        queue.put(
            {
                "ok": True,
                "pid": os.getpid(),
                "result_id": submitted.result_id,
                "accept_rejected": rejected,
                "reason": reason,
            }
        )
    except Exception as exc:  # noqa: BLE001
        queue.put({"ok": False, "error": str(exc), "trace": traceback.format_exc()})


def main() -> int:
    dsn = _dsn()
    out_dir = REPO / "docs/evidence/v17-recovery/R17"
    out_dir.mkdir(parents=True, exist_ok=True)

    engine, session = _open_session(dsn)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    mission = sample_mission().model_copy(
        update={"id": new_id("msn_"), "status": MissionStatus.RUNNING}
    )
    MissionRepository(session).insert(mission)
    session.flush()
    tid = new_id("tsk_")
    task = sample_task(mission_id=mission.id).model_copy(
        update={
            "id": tid,
            "project_id": mission.project_id,
            "required_capabilities": list(CAPS),
            "scopes": ["scope_repo_demo"],
            "status": TaskStatus.READY,
            "priority": 10,
            "graph_revision": mission.revision,
        }
    )
    session.add(
        TaskRow(
            id=tid,
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
    session.commit()
    project_id = mission.project_id

    ctx = mp.get_context("spawn")
    q: mp.Queue = ctx.Queue()

    victim = ctx.Process(
        target=_worker_claim, args=(q, dsn, project_id, "cp3-victim"), name="cp3-victim"
    )
    victim.start()
    claim_a = q.get(timeout=45)
    if not claim_a.get("ok"):
        print(json.dumps(claim_a, indent=2))
        victim.terminate()
        return 1
    victim_pid = int(claim_a["pid"])
    os.kill(victim_pid, signal.SIGKILL)
    victim.join(timeout=10)

    clock = utc_now()
    service = DurableWorkerService(session)
    expired = service.lifecycle.expire_leases(now=clock + timedelta(seconds=120))
    session.commit()

    survivor = ctx.Process(
        target=_worker_reclaim_and_submit,
        args=(q, dsn, project_id, "cp3-survivor"),
        name="cp3-survivor",
    )
    survivor.start()
    claim_b = q.get(timeout=45)
    survivor.join(timeout=30)
    if not claim_b.get("ok"):
        print(json.dumps(claim_b, indent=2))
        return 1

    stale_creds = {**claim_a, "project_id": project_id}
    zombie = ctx.Process(
        target=_stale_submit, args=(q, dsn, stale_creds), name="cp3-zombie"
    )
    zombie.start()
    stale = q.get(timeout=45)
    zombie.join(timeout=30)
    if not stale.get("ok") or not stale.get("accept_rejected"):
        print(json.dumps({"stale": stale}, indent=2))
        return 1

    accept_now = utc_now()
    accepted = service.accept_result(result_id=claim_b["result_id"], now=accept_now)
    session.commit()
    # Duplicate / competing result race: accept of the stale result must fail
    # once a result for the task is already accepted (idempotent re-accept of
    # the same result_id is allowed by design and is not a second acceptance).
    dup_rejected = False
    dup_reason = None
    try:
        service.accept_result(
            result_id=stale["result_id"], now=accept_now + timedelta(seconds=1)
        )
        session.commit()
    except ResultAcceptanceError as exc:
        dup_rejected = True
        dup_reason = str(exc)
        session.rollback()

    # Confirm exactly one accepted row for this task.
    from sqlalchemy import select

    from swarm.db.models import WorkerResultRow

    accepted_rows = (
        session.execute(
            select(WorkerResultRow).where(
                WorkerResultRow.task_id == tid,
                WorkerResultRow.acceptance_state == "accepted",
            )
        )
        .scalars()
        .all()
    )
    exactly_one = len(accepted_rows) == 1 and accepted_rows[0].result_id == claim_b["result_id"]

    report = {
        "packet_id": "R17",
        "artifact_id": "ART-V15-RECOVERY-EVIDENCE",
        "checkpoint": "CP3",
        "mode": "separate_os_processes_shared_postgres",
        "live_multi_host_evidence": "UNKNOWN_pending_second_physical_host",
        "self_accept": False,
        "spend_usd": 0.0,
        "dsn_note": "operator DB via SWARM_DATABASE_URL (not swarm:swarm)",
        "project_id": project_id,
        "mission_id": mission.id,
        "task_id": tid,
        "steps": {
            "victim_claim": {
                "pid": victim_pid,
                "lease_id": claim_a["lease_id"],
                "attempt_id": claim_a["attempt_id"],
                "killed": True,
            },
            "expire_reassign": {"expired_leases": list(expired)},
            "survivor_submit": {
                "pid": claim_b["pid"],
                "lease_id": claim_b["lease_id"],
                "result_id": claim_b["result_id"],
            },
            "stale_reject": {
                "pid": stale["pid"],
                "result_id": stale["result_id"],
                "accept_rejected": stale["accept_rejected"],
                "reason": stale.get("reason"),
            },
            "exactly_one_accept": {
                "accepted_result_id": claim_b["result_id"],
                "accepted_attempt_id": getattr(accepted, "attempt_id", None),
                "competing_stale_accept_rejected": dup_rejected,
                "competing_reason": dup_reason,
                "accepted_count_for_task": len(accepted_rows),
                "exactly_one_accepted": exactly_one,
            },
        },
        "ok": bool(
            claim_a["lease_id"] in expired
            and claim_b["lease_id"] != claim_a["lease_id"]
            and stale["accept_rejected"]
            and dup_rejected
            and exactly_one
        ),
    }

    (out_dir / "cp3-separate-process-receipt.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
