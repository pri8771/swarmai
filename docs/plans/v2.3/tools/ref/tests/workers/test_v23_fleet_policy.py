"""SW-W1-S7: ART fleet trust classes, drain states and deterministic placement."""

from __future__ import annotations

import asyncio

import pytest

from swarm.contracts.v23 import TrustClass, WorkerDrainState
from swarm.contracts.workspace import WorkerLease
from swarm.workers.fleet import FleetError, FleetPlacementService, normalize_trust
from swarm.workers.registry import WorkerRegistryService


def _fleet(*workers: tuple[str, str, str]) -> FleetPlacementService:
    """workers: (worker_id, trust_class, locality) — all in tenant ten_a, unbound project."""
    reg = WorkerRegistryService()
    for worker_id, _trust, _loc in workers:
        lease = WorkerLease(
            worker_id=worker_id,
            node_identity=f"n_{worker_id}",
            architecture="x86_64",
            runtime_version="1",
            capacity_units=1.0,
        )
        asyncio.run(reg.register(lease, token=f"tok_{worker_id}"))
    fleet = FleetPlacementService(reg)
    fleet.bind_project_tenant("proj_a", "ten_a")
    for worker_id, trust, loc in workers:
        fleet.annotate_worker(worker_id, tenant_id="ten_a", locality=loc, trust_class=trust)
    return fleet


def test_legacy_aliases_map_to_art_classes() -> None:
    assert normalize_trust("compute_only") == TrustClass.SANDBOX_COMPUTE
    assert normalize_trust("code_write") == TrustClass.TOOL_WORKER
    assert normalize_trust("model_worker") == TrustClass.MODEL_WORKER
    with pytest.raises(FleetError, match="unknown_trust_class"):
        normalize_trust("root")


def test_least_privilege_deterministic_choice() -> None:
    fleet = _fleet(
        ("wk_c", "integration_worker", "local"),
        ("wk_b", "tool_worker", "local"),
        ("wk_a", "tool_worker", "local"),
    )
    first = fleet.place(project_id="proj_a", min_trust="tool_worker")
    second = fleet.place(project_id="proj_a", min_trust="tool_worker")
    assert first.worker_id == second.worker_id == "wk_a"
    assert first.trust_class == "tool_worker"
    assert fleet.place(project_id="proj_a", min_trust="integration_worker").worker_id == "wk_c"


def test_draining_worker_gets_no_new_work() -> None:
    fleet = _fleet(("wk_a", "sandbox_compute", "local"), ("wk_b", "sandbox_compute", "local"))
    fleet.set_drain_state("wk_a", WorkerDrainState.DRAINING)
    assert fleet.place(project_id="proj_a").worker_id == "wk_b"
    fleet.set_drain_state("wk_b", WorkerDrainState.DRAINING)
    with pytest.raises(FleetError, match="no_eligible_worker"):
        fleet.place(project_id="proj_a")
    fleet.set_drain_state("wk_a", WorkerDrainState.DRAINED)
    fleet.set_drain_state("wk_a", WorkerDrainState.ACTIVE)
    assert fleet.place(project_id="proj_a").worker_id == "wk_a"


def test_revoked_is_terminal_and_registry_drain_respected() -> None:
    fleet = _fleet(("wk_a", "sandbox_compute", "local"), ("wk_b", "sandbox_compute", "local"))
    fleet.set_drain_state("wk_a", WorkerDrainState.REVOKED)
    with pytest.raises(FleetError, match="drain_transition_illegal"):
        fleet.set_drain_state("wk_a", WorkerDrainState.ACTIVE)
    fleet.registry.operator_drain("wk_b")
    with pytest.raises(FleetError, match="no_eligible_worker"):
        fleet.place(project_id="proj_a")


def test_project_trust_ceiling() -> None:
    fleet = _fleet(("wk_a", "sandbox_compute", "local"), ("wk_z", "integration_worker", "local"))
    fleet.set_project_trust_ceiling("proj_a", "model_worker")
    with pytest.raises(FleetError, match="trust_above_project_ceiling"):
        fleet.place(project_id="proj_a", min_trust="tool_worker")
    assert fleet.place(project_id="proj_a", min_trust="observe_only").worker_id == "wk_a"


def test_locality_is_strict() -> None:
    fleet = _fleet(("wk_a", "sandbox_compute", "local"), ("wk_e", "sandbox_compute", "edge"))
    assert fleet.place(project_id="proj_a", preferred_locality="edge").worker_id == "wk_e"
    with pytest.raises(FleetError, match="no_eligible_worker"):
        fleet.place(project_id="proj_a", preferred_locality="mars")
