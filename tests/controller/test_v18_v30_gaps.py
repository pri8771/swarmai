"""Additional V1.8–V3.0 gap-close tests (epoch fence, fleet, objectives, selfdev)."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from swarm.capabilities import CapabilityPackManifest, CapabilityPackRegistry, ProjectPackGrant
from swarm.contracts.common import utc_now
from swarm.contracts.workspace import WorkerLease
from swarm.controller.reservations import ReservationComponent, ReservationError, ReservationService
from swarm.controller.scheduler import AdaptiveScheduler
from swarm.extensions.registry import ExtensionAuthzError
from swarm.learning import LearningProposal, LearningRepository
from swarm.objectives import ObjectiveContract, ObjectiveError, ObjectiveRepository
from swarm.observability import OpsEventLog, assert_dashboard_mutation_via_action
from swarm.recovery import SiteAuthorityService, StaleEpochError
from swarm.selfdev.policy import assert_learning_governance
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import InMemoryEffectStore
from swarm.tools.v17_gateway import ConsequentialToolGateway
from swarm.workers.fleet import FleetError, FleetPlacementService
from swarm.workers.registry import WorkerRegistryService


@pytest.mark.asyncio
async def test_v17_gateway_rejects_stale_site_epoch() -> None:
    auth = SiteAuthorityService()
    auth.bootstrap("site_a", epoch=3)
    adapter = ApiMcpAdapter()
    gw = ConsequentialToolGateway(
        adapter,
        project_id="proj_a",
        allowed_scopes={"network.https", "mcp.call"},
        current_lease_generation=1,
        store=InMemoryEffectStore(),
        site_authority=auth,
        site_id="site_a",
    )
    env = adapter.normalize(
        {
            "project_id": "proj_a",
            "destination": "mcp://echo/default",
            "body": "ping",
            "operation": "echo",
        }
    )
    env.site_epoch = 2
    approval = gw.make_approval(env)
    env.approval_id = approval.approval_id
    with pytest.raises(StaleEpochError, match="stale_epoch"):
        await gw.execute_envelope(env)
    env.site_epoch = 3
    receipt = await gw.execute_envelope(env)
    assert receipt.outcome == "succeeded"


def test_scheduler_epoch_and_drain() -> None:
    from swarm.contracts.enums import TaskStatus
    from swarm.contracts.fixtures import sample_mission, sample_task

    auth = SiteAuthorityService()
    auth.bootstrap("site_a", epoch=1)
    sched = AdaptiveScheduler(site_authority=auth, site_id="site_a", site_epoch=1)
    mission = sample_mission()
    tasks = [
        sample_task().model_copy(
            update={"mission_id": mission.id, "status": TaskStatus.READY, "task_family": "extraction"}
        )
    ]
    selected, expl = sched.choose_ready(
        mission, tasks, inference_slots=4, worker_slots=4, site_epoch=1
    )
    assert expl["site_epoch"] == 1
    assert isinstance(selected, list)
    with pytest.raises(StaleEpochError):
        sched.choose_ready(mission, tasks, inference_slots=4, worker_slots=4, site_epoch=0)
    sched.begin_drain()
    selected2, expl2 = sched.choose_ready(
        mission, tasks, inference_slots=4, worker_slots=4, site_epoch=1
    )
    assert selected2 == []
    assert expl2["reason"] == "draining"


def test_reservation_drain_cancel_backpressure() -> None:
    svc = ReservationService(current_epoch=1, backpressure_floor=1.0)
    svc.set_capacity("worker", "local", 2)
    with pytest.raises(ReservationError, match="backpressure"):
        svc.reserve(
            project_id="p",
            mission_id="m",
            attempt_id="a1",
            site_epoch=1,
            components=[ReservationComponent("worker", "local", units=2)],
        )
    intent = svc.reserve(
        project_id="p",
        mission_id="m",
        attempt_id="a2",
        site_epoch=1,
        components=[ReservationComponent("worker", "local", units=1)],
    )
    svc.cancel(intent.attempt_id, site_epoch=1)
    svc.begin_drain()
    with pytest.raises(ReservationError, match="drain_active"):
        svc.reserve(
            project_id="p",
            mission_id="m",
            attempt_id="a3",
            site_epoch=1,
            components=[ReservationComponent("worker", "local", units=1)],
        )


def test_objective_rate_expiry_stop_authority(tmp_path: Path) -> None:
    _ = tmp_path
    repo = ObjectiveRepository()
    obj = repo.create(
        ObjectiveContract(
            project_id="p",
            goal="g",
            rate_limit_per_hour=1,
            max_active_missions=2,
            tool_envelope=["sandbox.fs"],
            stop_conditions=["quota_exhausted"],
            expires_at=(utc_now() + timedelta(hours=1)).isoformat(),
            spend_usd_ceiling=0.0,
        )
    )
    scopes = repo.intersect_authority(obj.objective_id, tools={"sandbox.fs", "admin"})
    assert scopes["tools"] == {"sandbox.fs"}
    with pytest.raises(ObjectiveError, match="authority_intersection_empty"):
        repo.intersect_authority(obj.objective_id, tools={"admin"})
    repo.trigger(obj.objective_id, dedupe_key="k1", trigger_kind="manual")
    with pytest.raises(ObjectiveError, match="rate_limit"):
        repo.trigger(obj.objective_id, dedupe_key="k2", trigger_kind="manual")
    repo.mark_stop(obj.objective_id, "quota_exhausted")
    with pytest.raises(ObjectiveError, match="objective_not_active|stop_condition"):
        repo.trigger(obj.objective_id, dedupe_key="k3", trigger_kind="manual")


def test_fleet_cross_tenant_negative() -> None:
    import asyncio

    reg = WorkerRegistryService()
    lease_a = WorkerLease(
        worker_id="wrk_a",
        node_identity="n1",
        architecture="x86_64",
        runtime_version="1",
        capacity_units=1.0,
    )
    lease_b = WorkerLease(
        worker_id="wrk_b",
        node_identity="n2",
        architecture="x86_64",
        runtime_version="1",
        capacity_units=1.0,
    )
    asyncio.run(reg.register(lease_a, token="tok_a", project_id="proj_a"))
    asyncio.run(reg.register(lease_b, token="tok_b", project_id="proj_b"))
    fleet = FleetPlacementService(reg)
    fleet.bind_project_tenant("proj_a", "ten_a")
    fleet.bind_project_tenant("proj_b", "ten_b")
    fleet.annotate_worker("wrk_a", tenant_id="ten_a")
    fleet.annotate_worker("wrk_b", tenant_id="ten_b")
    decision = fleet.place(project_id="proj_a")
    assert decision.worker_id == "wrk_a"
    with pytest.raises(FleetError, match="cross_tenant"):
        fleet.assert_same_tenant(actor_tenant="ten_a", resource_tenant="ten_b", action="effect")
    audit = fleet.audit_log()
    assert any(e["action"] == "cross_tenant_denied" for e in audit)


def test_pack_signature_and_revoke() -> None:
    reg = CapabilityPackRegistry(require_signature=True)
    base = CapabilityPackManifest(
        pack_id="pack.demo",
        version="1",
        content_digest="abc",
        capability_declarations=["read_logs"],
    )
    with pytest.raises(ExtensionAuthzError, match="signature_required"):
        reg.register(base)
    signed = CapabilityPackRegistry.sign(base)
    reg.register(signed)
    reg.revoke("pack.demo", "1")
    with pytest.raises(ExtensionAuthzError, match="pack_revoked"):
        reg.grant(
            ProjectPackGrant(
                project_id="p",
                pack_id="pack.demo",
                version="1",
                granted_capabilities=["read_logs"],
            )
        )


def test_selfdev_requires_learning_governance() -> None:
    bad = assert_learning_governance(
        learning_proposal_id=None, learning_state=None, expands_spend=True
    )
    assert bad.allowed is False
    ok = assert_learning_governance(
        learning_proposal_id="lrn_1", learning_state="canary", expands_spend=False
    )
    assert ok.allowed is True


def test_ops_events_and_dashboard_boundary() -> None:
    log = OpsEventLog()
    log.emit("dispatch", "scheduler", project_id="p", site_epoch=1, detail={"api_key": "sk"})
    events = log.list_events(project_id="p")
    assert events[0]["detail"]["api_key"] == "[redacted]"
    with pytest.raises(PermissionError, match="action_boundary"):
        assert_dashboard_mutation_via_action(surface="dashboard", uses_action_boundary=False)
    assert_dashboard_mutation_via_action(surface="dashboard", uses_action_boundary=True)


def test_learning_contamination_terminal() -> None:
    repo = LearningRepository()
    prop = repo.create(
        LearningProposal(
            project_id="p",
            change_summary="x",
            sealed_holdout_ref="seal:h#1",
        )
    )
    repo.transition(prop.proposal_id, "validated")
    repo.transition(prop.proposal_id, "calibrating")
    repo.transition(prop.proposal_id, "frozen")
    repo.transition(prop.proposal_id, "held_out_eval")
    repo.transition(prop.proposal_id, "contaminated")
    from swarm.learning import LearningError

    with pytest.raises(LearningError, match="illegal_transition"):
        repo.transition(prop.proposal_id, "accepted")
