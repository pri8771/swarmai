"""Collaborative mission + X→Y handoff through continuous connector leases.

Deterministic, zero-spend. Workers submit results; they never self-accept.
Predecessor cannot claim after adopted succession.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.fixtures import sample_task
from swarm.contracts.workspace import WorkerLease
from swarm.mission.collab import CollaborativeMissionBoard
from swarm.workers.continuous_connector import default_mac_executor
from swarm.workers.registry import WorkerRegistryService


@dataclass
class CollabConnectorCampaignReport:
    ok: bool
    mission_id: str
    collab: dict[str, Any]
    connector_steps: list[dict[str, Any]] = field(default_factory=list)
    predecessor_blocked_after_handoff: bool = False
    successor_submitted: bool = False
    self_accepted: bool = False
    spend_usd: float = 0.0
    one_shot: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet": "V1.7-collab-continuous-connector",
            "hostname_public": "swarm.splitsignal.ai",
            "ok": self.ok,
            "mission_id": self.mission_id,
            "collab": self.collab,
            "connector_steps": self.connector_steps,
            "predecessor_blocked_after_handoff": self.predecessor_blocked_after_handoff,
            "successor_submitted": self.successor_submitted,
            "self_accepted": self.self_accepted,
            "one_shot": self.one_shot,
            "continuous_lease_path": True,
            "spend_usd": self.spend_usd,
            "finished_at": utc_now().isoformat(),
        }


async def run_collab_connector_campaign(
    *,
    evidence_dir: Path | None = None,
    fixture_dir: Path | None = None,
) -> CollabConnectorCampaignReport:
    """Exercise collab + succession + continuous claim/renew/submit (no HTTP spend)."""
    mission_id = new_id("msn_collab_")
    board = CollaborativeMissionBoard(mission_id=mission_id)
    board.join("agent_x")
    board.join("agent_y")

    board.post(
        from_agent="agent_x",
        to_agent="agent_y",
        kind="request_help",
        body="Please continue mac_local extract; I will hand off context.",
        evidence_refs=["art_partial_1"],
    )
    board.post(
        from_agent="agent_y",
        to_agent="agent_x",
        kind="evidence",
        body="Ready to assume lease after KT handoff.",
        evidence_refs=[],
    )
    handoff = board.prepare_handoff(
        from_agent="agent_x",
        to_agent="agent_y",
        retained_facts=["placement=mac_local", "email_count_pending"],
        open_commitments=["claim_lease", "submit_result_pending_accept"],
        event_watermark=f"wm_{mission_id}",
    )
    board.adopt_handoff(handoff.handoff_id, by_agent="agent_y")

    reg = WorkerRegistryService(lease_ttl_seconds=60)
    steps: list[dict[str, Any]] = []

    async def _enroll(agent: str, node: str) -> tuple[str, str, int]:
        token = new_id("wt_")
        lease = await reg.register(
            WorkerLease(
                node_identity=node,
                architecture="arm64",
                runtime_version="0.1.0",
                capacity_units=1.0,
                capabilities=["mac.local.extract", "extract", "chat"],
                labels=["mac", agent],
            ),
            token=token,
            project_id="proj_collab",
        )
        reg._workers[lease.worker_id].privacy_classes = {"mac_local", "local"}
        await reg.heartbeat(lease.worker_id, lease.lease_generation, token=token)
        steps.append(
            {
                "step": "enroll",
                "agent": agent,
                "worker_id": lease.worker_id,
                "generation": lease.lease_generation,
            }
        )
        return lease.worker_id, token, lease.lease_generation

    x_id, x_tok, x_gen = await _enroll("agent_x", "mac-x")
    y_id, y_tok, y_gen = await _enroll("agent_y", "mac-y")

    task = sample_task(mission_id=mission_id).model_copy(
        update={
            "id": new_id("tsk_"),
            "project_id": "proj_collab",
            "required_capabilities": ["extract"],
            "scopes": ["mac_local"],
            "objective": "collaborative mac_local extract after X→Y succession",
            "role_hint": "agent_y",
        }
    )
    reg.enqueue(task)
    steps.append({"step": "enqueue", "task_id": task.id, "mission_id": mission_id})

    # Predecessor fenced by succession — must not claim.
    predecessor_blocked = not board.can_claim_work("agent_x")
    if predecessor_blocked:
        steps.append({"step": "predecessor_claim_blocked", "agent": "agent_x", "ok": True})
    else:
        steps.append({"step": "predecessor_claim_blocked", "agent": "agent_x", "ok": False})

    # Successor claims via continuous lease path.
    if not board.can_claim_work("agent_y"):
        report = CollabConnectorCampaignReport(
            ok=False,
            mission_id=mission_id,
            collab=board.evidence(),
            connector_steps=steps,
            predecessor_blocked_after_handoff=predecessor_blocked,
        )
        _dump(evidence_dir, report)
        return report

    claimed = await reg.claim_work(y_id, token=y_tok)
    steps.append(
        {
            "step": "claim",
            "agent": "agent_y",
            "claimed": claimed.claimed,
            "lease_id": claimed.lease.lease_id if claimed.lease else None,
        }
    )
    if not claimed.claimed or claimed.lease is None:
        report = CollabConnectorCampaignReport(
            ok=False,
            mission_id=mission_id,
            collab=board.evidence(),
            connector_steps=steps,
            predecessor_blocked_after_handoff=predecessor_blocked,
        )
        _dump(evidence_dir, report)
        return report

    renewed = reg.renew_lease(
        lease_id=claimed.lease.lease_id,
        worker_id=y_id,
        generation=y_gen,
        token=y_tok,
    )
    steps.append(
        {
            "step": "renew",
            "lease_id": renewed.lease_id,
            "state": renewed.state,
            "expires_at": renewed.expires_at.isoformat(),
        }
    )

    fx = fixture_dir or Path("var/mac-connector/fixtures")
    produced = default_mac_executor(
        {"task": claimed.lease.task.model_dump(mode="json")},
        fx,
    )
    submitted = reg.submit_result(
        lease_id=claimed.lease.lease_id,
        worker_id=y_id,
        generation=y_gen,
        token=y_tok,
        status=str(produced.get("status") or "completed"),
        checks=dict(produced.get("checks") or {}),
        artifact_manifest=dict(produced.get("artifact_manifest") or {}),
        usage=dict(produced.get("usage") or {}),
        summary=str(produced.get("summary") or "collab_successor_submit"),
    )
    self_accepted = submitted.get("acceptance_state") == "accepted"
    steps.append(
        {
            "step": "submit_result",
            "result_id": submitted.get("result_id"),
            "acceptance_state": submitted.get("acceptance_state"),
            "self_accepted": self_accepted,
        }
    )

    # Stale predecessor attempt after handoff must not get a second claim on empty queue.
    stale = await reg.claim_work(x_id, token=x_tok)
    steps.append(
        {
            "step": "predecessor_post_handoff_claim",
            "claimed": stale.claimed,
            "blocked_by_board": predecessor_blocked,
        }
    )

    ok = (
        predecessor_blocked
        and bool(submitted.get("result_id"))
        and not self_accepted
        and submitted.get("acceptance_state") == "pending"
        and stale.claimed is False
    )
    report = CollabConnectorCampaignReport(
        ok=ok,
        mission_id=mission_id,
        collab=board.evidence(),
        connector_steps=steps,
        predecessor_blocked_after_handoff=predecessor_blocked,
        successor_submitted=True,
        self_accepted=self_accepted,
    )
    _dump(evidence_dir, report)
    return report


def _dump(evidence_dir: Path | None, report: CollabConnectorCampaignReport) -> None:
    if evidence_dir is None:
        return
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / f"collab-connector-{report.mission_id}.json"
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    board_path = evidence_dir / f"collab-board-{report.mission_id}.json"
    board_path.write_text(json.dumps(report.collab, indent=2) + "\n", encoding="utf-8")
