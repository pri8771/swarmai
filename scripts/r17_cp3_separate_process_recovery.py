#!/usr/bin/env python3
"""R17 / R17a — CP3 separate-process durable worker recovery proof.

Real OS processes share one Postgres DSN. Sequence:
  register -> claim -> kill -> expire/reassign -> stale reject -> valid accept
  -> duplicate accept race fails -> exactly one accepted result
  -> (R17a) cancellation-generation rejection
  -> (R17a) genuinely concurrent duplicate accept, 20 iterations, one winner each.

Does not invent multi-host proof. No spend. Writes a write-once run directory
under docs/evidence/v17-checkpoints/CP3/<run-id>/ with a machine-readable
`requirements` map covering all nine CP3 requirements.
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
from swarm.db.lease_fencing import LeaseRenewError, ResultAcceptanceError  # noqa: E402
from swarm.db.models import Base, MissionRow, TaskRow, WorkerResultRow  # noqa: E402
from swarm.db.repositories import MissionRepository  # noqa: E402
from swarm.workers.client import WorkerClient  # noqa: E402
from swarm.workers.envelopes import EnrollmentRequest  # noqa: E402
from swarm.workers.service import DurableWorkerService  # noqa: E402
from swarm.workers.transport import InProcessWorkerTransport  # noqa: E402

CAPS = ["code.read", "chat"]
CONCURRENT_ITERATIONS = 20

# The nine CP3 requirements (V17_LIVE_CHECKPOINT_PROTOCOL.md), by name.
REQUIREMENTS = (
    "durable_worker_registration",
    "claim",
    "renew",
    "process_restart_real_kill",
    "expiry_reassignment",
    "stale_result_rejection",
    "duplicate_result_race_concurrent",
    "cancellation_generation_rejection",
    "exactly_one_accepted_result",
)


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


def _worker_reclaim_and_submit(queue: mp.Queue, dsn: str, project_id: str, host: str) -> None:
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


def _seed_task(session, *, mission_id: str, project_id: str, revision: int) -> str:
    tid = new_id("tsk_")
    task = sample_task(mission_id=mission_id).model_copy(
        update={
            "id": tid,
            "project_id": project_id,
            "required_capabilities": list(CAPS),
            "scopes": ["scope_repo_demo"],
            "status": TaskStatus.READY,
            "priority": 10,
            "graph_revision": revision,
        }
    )
    session.add(
        TaskRow(
            id=tid,
            project_id=project_id,
            mission_id=mission_id,
            objective=task.objective,
            task_family=task.task_family,
            status="ready",
            graph_revision=revision,
            priority=10,
            scopes=list(task.scopes),
            dependency_ids=[],
            payload=task.model_dump(mode="json"),
        )
    )
    session.commit()
    return tid


def _seed_mission(session) -> MissionRow:
    mission = sample_mission().model_copy(
        update={"id": new_id("msn_"), "status": MissionStatus.RUNNING}
    )
    MissionRepository(session).insert(mission)
    session.commit()
    row = session.get(MissionRow, mission.id)
    assert row is not None
    return row


def _worker_claim_then_commands(
    queue: mp.Queue, commands: mp.Queue, dsn: str, project_id: str, host: str
) -> None:
    """R17a cancellation step: claim, then obey submit/renew commands from the control plane."""
    try:
        _engine, session = _open_session(dsn)
        client = _enroll_client(session, project_id=project_id, host_alias=host)
        claimed = client.claim()
        session.commit()
        if not claimed.claimed or not claimed.lease_id:
            queue.put({"ok": False, "error": "claim_failed"})
            return
        queue.put(
            {"ok": True, "phase": "claimed", "pid": os.getpid(), "lease_id": claimed.lease_id}
        )
        while True:
            command = commands.get(timeout=60)
            if command == "submit":
                submitted = client.submit_result(
                    lease_id=claimed.lease_id,
                    status="succeeded",
                    checks={"review_passed": True},
                    summary="cp3_after_cancel",
                )
                session.commit()
                queue.put({"ok": True, "phase": "submitted", "result_id": submitted.result_id})
            elif command == "renew":
                try:
                    client.renew(lease_id=claimed.lease_id)
                    session.commit()
                    queue.put({"ok": True, "phase": "renewed", "rejected": False})
                except LeaseRenewError as exc:
                    session.rollback()
                    queue.put(
                        {"ok": True, "phase": "renewed", "rejected": True, "reason": str(exc)}
                    )
            elif command == "exit":
                return
    except Exception as exc:  # noqa: BLE001
        queue.put({"ok": False, "error": str(exc), "trace": traceback.format_exc()})


def _worker_claim_submit_twice(queue: mp.Queue, dsn: str, project_id: str, host: str) -> None:
    """R17a concurrent step: one lease, two durable result submissions (duplicate delivery)."""
    try:
        _engine, session = _open_session(dsn)
        client = _enroll_client(session, project_id=project_id, host_alias=host)
        claimed = client.claim()
        if not claimed.claimed or not claimed.lease_id:
            session.commit()
            queue.put({"ok": False, "error": "claim_failed"})
            return
        ids = []
        for n in (1, 2):
            submitted = client.submit_result(
                lease_id=claimed.lease_id,
                status="succeeded",
                checks={"review_passed": True},
                summary=f"cp3_dup_{n}",
            )
            ids.append(submitted.result_id)
        session.commit()
        queue.put(
            {
                "ok": True,
                "pid": os.getpid(),
                "task_id": claimed.task_id,
                "attempt_id": claimed.attempt_id,
                "result_ids": ids,
            }
        )
    except Exception as exc:  # noqa: BLE001
        queue.put({"ok": False, "error": str(exc), "trace": traceback.format_exc()})


def _concurrent_accept(barrier, queue: mp.Queue, dsn: str, result_id: str) -> None:
    """R17a: control-plane acceptor; waits on a shared barrier before accept_result."""
    try:
        _engine, session = _open_session(dsn)
        service = DurableWorkerService(session)
        barrier.wait(timeout=60)
        try:
            accepted = service.accept_result(result_id=result_id)
            session.commit()
            queue.put(
                {
                    "ok": True,
                    "pid": os.getpid(),
                    "result_id": result_id,
                    "accepted": True,
                    "attempt_id": getattr(accepted, "attempt_id", None),
                }
            )
        except ResultAcceptanceError as exc:
            session.rollback()
            queue.put(
                {
                    "ok": True,
                    "pid": os.getpid(),
                    "result_id": result_id,
                    "accepted": False,
                    "reason": str(exc),
                }
            )
    except Exception as exc:  # noqa: BLE001
        queue.put({"ok": False, "error": str(exc), "trace": traceback.format_exc()})


def evaluate_cancellation_step(observed: dict) -> dict:
    """Pure evaluation: the step is demonstrated only with the exact fence reasons."""
    demonstrated = bool(
        observed.get("generation_bumped")
        and observed.get("accept_rejected") is True
        and observed.get("accept_reason") == "cancellation_generation_stale"
        and observed.get("renew_rejected") is True
        and observed.get("renew_reason") == "cancellation_generation_stale"
        and observed.get("accepted_count_for_task") == 0
    )
    return {"demonstrated": demonstrated, "detail": observed}


def evaluate_concurrent_step(iterations: list[dict]) -> dict:
    """Pure evaluation: every iteration has exactly one accepted result across two processes."""
    ok_iterations = 0
    for it in iterations:
        outcomes = it.get("outcomes") or []
        accepted = [o for o in outcomes if o.get("accepted") is True]
        rejected = [o for o in outcomes if o.get("accepted") is False]
        if (
            len(outcomes) == 2
            and len(accepted) == 1
            and len(rejected) == 1
            and it.get("accepted_count_for_task") == 1
        ):
            ok_iterations += 1
    demonstrated = bool(iterations) and ok_iterations == len(iterations)
    return {
        "demonstrated": demonstrated,
        "detail": {
            "iterations": len(iterations),
            "iterations_with_exactly_one_accept": ok_iterations,
            "winner_pids": [it.get("winner_pid") for it in iterations],
        },
    }


def run_cancellation_step(session, dsn: str, ctx, *, bump_generation: bool = True) -> dict:
    """R17a step: durable cancellation generation bump fences a live worker's result/renew.

    Finding recorded honestly: `LeaseLifecycleService.cancel_active_lease` cancels one
    lease but does not bump the mission's durable `cancellation_generation`, and no
    mission-cancel service method exists. The control plane (this harness) performs
    the durable bump directly; the advisory per-lease cancel is applied afterwards.
    `bump_generation=False` exists only so a test can prove this step is able to fail.
    """
    mission = _seed_mission(session)
    tid = _seed_task(
        session, mission_id=mission.id, project_id=mission.project_id, revision=mission.revision
    )
    q: mp.Queue = ctx.Queue()
    commands: mp.Queue = ctx.Queue()
    worker = ctx.Process(
        target=_worker_claim_then_commands,
        args=(q, commands, dsn, mission.project_id, "cp3-cancel-worker"),
        name="cp3-cancel-worker",
    )
    worker.start()
    observed: dict = {"task_id": tid, "mission_id": mission.id}
    try:
        claimed = q.get(timeout=60)
        if not claimed.get("ok"):
            observed["error"] = claimed
            return evaluate_cancellation_step(observed)
        observed["worker_pid"] = claimed["pid"]
        observed["lease_id"] = claimed["lease_id"]
        # Control plane: durable cancellation authority.
        if bump_generation:
            row = session.get(MissionRow, mission.id, with_for_update=True)
            assert row is not None
            row.cancellation_generation = int(row.cancellation_generation) + 1
            session.commit()
            observed["generation_bumped"] = True
            observed["mission_cancellation_generation"] = int(row.cancellation_generation)
        else:
            observed["generation_bumped"] = False
        # Worker (separate process) submits after the durable cancellation.
        commands.put("submit")
        submitted = q.get(timeout=60)
        observed["result_id"] = submitted.get("result_id")
        service = DurableWorkerService(session)
        try:
            service.accept_result(result_id=submitted["result_id"])
            session.commit()
            observed["accept_rejected"] = False
        except ResultAcceptanceError as exc:
            session.rollback()
            observed["accept_rejected"] = True
            observed["accept_reason"] = str(exc)
        # Worker renewal is fenced by the same durable generation.
        commands.put("renew")
        renewed = q.get(timeout=60)
        observed["renew_rejected"] = renewed.get("rejected")
        observed["renew_reason"] = renewed.get("reason")
        # Advisory per-lease cancellation (worker notification path) afterwards.
        try:
            service.lifecycle.cancel_active_lease(lease_id=claimed["lease_id"], reason="cancelled")
            session.commit()
            observed["advisory_cancel_applied"] = True
        except ResultAcceptanceError as exc:
            session.rollback()
            observed["advisory_cancel_applied"] = False
            observed["advisory_cancel_error"] = str(exc)
        try:
            service.accept_result(result_id=submitted["result_id"])
            session.commit()
            observed["accept_after_advisory_cancel_rejected"] = False
        except ResultAcceptanceError as exc:
            session.rollback()
            observed["accept_after_advisory_cancel_rejected"] = True
            observed["accept_after_advisory_cancel_reason"] = str(exc)
        observed["accepted_count_for_task"] = _accepted_count(session, tid)
    finally:
        commands.put("exit")
        worker.join(timeout=15)
        if worker.is_alive():
            worker.kill()
    return evaluate_cancellation_step(observed)


def run_concurrent_duplicate_accept(session, dsn: str, ctx, *, iterations: int) -> dict:
    """R17a step: two real processes race accept_result on two results of one attempt."""
    mission = _seed_mission(session)
    results: list[dict] = []
    for index in range(iterations):
        tid = _seed_task(
            session,
            mission_id=mission.id,
            project_id=mission.project_id,
            revision=mission.revision,
        )
        q: mp.Queue = ctx.Queue()
        worker = ctx.Process(
            target=_worker_claim_submit_twice,
            args=(q, dsn, mission.project_id, f"cp3-dup-worker-{index}"),
        )
        worker.start()
        submitted = q.get(timeout=60)
        worker.join(timeout=30)
        iteration: dict = {"index": index, "task_id": tid}
        if not submitted.get("ok"):
            iteration["error"] = submitted
            results.append(iteration)
            continue
        barrier = ctx.Barrier(2)
        rq: mp.Queue = ctx.Queue()
        acceptors = [
            ctx.Process(target=_concurrent_accept, args=(barrier, rq, dsn, rid))
            for rid in submitted["result_ids"]
        ]
        for proc in acceptors:
            proc.start()
        outcomes = [rq.get(timeout=90) for _ in acceptors]
        for proc in acceptors:
            proc.join(timeout=30)
        iteration["attempt_id"] = submitted["attempt_id"]
        iteration["outcomes"] = outcomes
        winners = [o for o in outcomes if o.get("accepted") is True]
        iteration["winner_pid"] = winners[0]["pid"] if len(winners) == 1 else None
        iteration["accepted_count_for_task"] = _accepted_count(session, tid)
        results.append(iteration)
    return evaluate_concurrent_step(results)


def _accepted_count(session, task_id: str) -> int:
    from sqlalchemy import select

    session.expire_all()
    rows = (
        session.execute(
            select(WorkerResultRow).where(
                WorkerResultRow.task_id == task_id,
                WorkerResultRow.acceptance_state == "accepted",
            )
        )
        .scalars()
        .all()
    )
    return len(rows)


def build_requirements(report: dict) -> dict:
    """Map the run's observations onto the nine CP3 requirements."""
    steps = report["steps"]
    exactly_one = steps["exactly_one_accept"]
    concurrent = report["r17a"]["concurrent_duplicate_accept"]
    cancel = report["r17a"]["cancellation_fence"]
    return {
        "durable_worker_registration": {
            "demonstrated": True,
            "detail": "victim/survivor/zombie/cancel/dup workers enrolled via DurableWorkerService",
        },
        "claim": {"demonstrated": True, "detail": steps["victim_claim"]},
        "renew": {
            "demonstrated": cancel["detail"].get("renew_rejected") is True,
            "detail": "renew exercised by the cancellation step (rejected by fence)",
        },
        "process_restart_real_kill": {
            "demonstrated": steps["victim_claim"]["killed"] is True,
            "detail": {"pid": steps["victim_claim"]["pid"], "signal": "SIGKILL"},
        },
        "expiry_reassignment": {
            "demonstrated": bool(steps["expire_reassign"]["expired_leases"])
            and steps["survivor_submit"]["lease_id"] != steps["victim_claim"]["lease_id"],
            "detail": steps["expire_reassign"],
        },
        "stale_result_rejection": {
            "demonstrated": steps["stale_reject"]["accept_rejected"] is True,
            "detail": steps["stale_reject"],
        },
        "duplicate_result_race_concurrent": concurrent,
        "cancellation_generation_rejection": cancel,
        "exactly_one_accepted_result": {
            "demonstrated": exactly_one["exactly_one_accepted"] is True,
            "detail": exactly_one,
        },
    }


def main() -> int:
    dsn = _dsn()
    run_id = os.environ.get("CP3_RUN_ID") or f"cp3-{utc_now().strftime('%Y%m%dT%H%M%SZ')}"
    out_dir = REPO / "docs/evidence/v17-checkpoints/CP3" / run_id
    if out_dir.exists():
        raise SystemExit(f"refusing to overwrite existing run directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    started_at = utc_now().isoformat()

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
    zombie = ctx.Process(target=_stale_submit, args=(q, dsn, stale_creds), name="cp3-zombie")
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
        service.accept_result(result_id=stale["result_id"], now=accept_now + timedelta(seconds=1))
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

    # ---- R17a steps (each on its own mission so generations do not interfere)
    cancellation = run_cancellation_step(session, dsn, ctx)
    concurrent = run_concurrent_duplicate_accept(
        session, dsn, ctx, iterations=CONCURRENT_ITERATIONS
    )

    report = {
        "packet_id": "R17a",
        "run_id": run_id,
        "artifact_id": "ART-V15-RECOVERY-EVIDENCE",
        "checkpoint": "CP3",
        "started_at": started_at,
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
        "r17a": {
            "cancellation_fence": cancellation,
            "concurrent_duplicate_accept": concurrent,
        },
    }
    report["requirements"] = build_requirements(report)
    report["ok"] = bool(
        claim_a["lease_id"] in expired
        and claim_b["lease_id"] != claim_a["lease_id"]
        and stale["accept_rejected"]
        and dup_rejected
        and exactly_one
        and all(r["demonstrated"] for r in report["requirements"].values())
    )
    report["finished_at"] = utc_now().isoformat()
    report["finding"] = (
        "cancel_active_lease does not bump the durable mission cancellation_generation and no "
        "mission-cancel service method exists; the control plane (this harness) performed the "
        "durable bump directly. Follow-up: add a mission-cancel method that bumps the generation "
        "before advisory lease cancellation."
    )

    (out_dir / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "checkpoint": "CP3",
                "run_id": run_id,
                "packet": "R17a",
                "artifact": "ART-V15-RECOVERY-EVIDENCE",
                "source_sha": _git_sha(),
                "worktree_clean": _git_clean(),
                "started_at": started_at,
                "finished_at": report["finished_at"],
                "result": "pass" if report["ok"] else "fail",
                "spend_usd": 0.0,
                "self_accept": False,
                "live_multi_host_evidence": "UNKNOWN_pending_second_physical_host",
            },
            indent=2,
        )
        + "\n"
    )
    (out_dir / "commands.json").write_text(
        json.dumps(
            [
                {
                    "argv": ["uv", "run", "python", "scripts/r17_cp3_separate_process_recovery.py"],
                    "exit_code": 0 if report["ok"] else 2,
                }
            ],
            indent=2,
        )
        + "\n"
    )
    (out_dir / "environment.json").write_text(
        json.dumps(
            {
                "env_var_names_used": ["SWARM_DATABASE_URL", "CP3_RUN_ID"],
                "python": sys.version.split()[0],
                "platform": sys.platform,
                "database": "PostgreSQL via SWARM_DATABASE_URL (value not recorded)",
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 2


def _git_sha() -> str:
    import subprocess

    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _git_clean() -> bool:
    import subprocess

    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--", "src", "migrations", "tests", "scripts"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return out.strip() == ""
    except Exception:  # noqa: BLE001
        return False


if __name__ == "__main__":
    raise SystemExit(main())
