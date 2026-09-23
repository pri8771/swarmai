"""V2.0 candidate freeze + V2.3 scheduler/portability tests."""

from __future__ import annotations

import subprocess

import pytest

from swarm.capabilities import CapabilityPackManifest, CapabilityPackRegistry, ProjectPackGrant
from swarm.controller.fairness import DurableFairnessStore
from swarm.controller.reservations import ReservationComponent, ReservationError, ReservationService
from swarm.controller.resource_allocator import AllocationRequest, ResourceAllocator
from swarm.controller.scheduling_receipts import SchedulingReceiptLog
from swarm.extensions.registry import ExtensionAuthzError
from swarm.product.portability import PortabilityService
from swarm.release.candidate import CandidateFreezer


def test_candidate_freeze_binds_lock_digest(tmp_path) -> None:
    # Minimal repo shape for freezer.
    (tmp_path / "uv.lock").write_text("lock")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='swarm'\n")
    coord = tmp_path / "docs" / "coordination"
    coord.mkdir(parents=True)
    (coord / "ARTIFACT_REGISTRY.json").write_text("{}")
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    manifest = CandidateFreezer(tmp_path).freeze(source_sha=sha, schema_revision="a18tov30")
    assert manifest.source_sha == sha
    assert manifest.dependency_lock_digest != "missing"
    assert manifest.policy_versions["allow_paid"] == "false"


def test_fairness_and_reservation_epoch_fence() -> None:
    fair = DurableFairnessStore()
    fair.get("p1").weight = 2.0
    fair.note_dispatch("p2")
    assert fair.rank_projects(["p1", "p2"])[0] == "p1"
    svc = ReservationService(current_epoch=5)
    svc.set_capacity("worker", "local", 2)
    svc.set_capacity("provider", "rt_ollama_default", 2)
    with pytest.raises(ReservationError, match="stale_epoch"):
        svc.reserve(
            project_id="p1",
            mission_id="m1",
            attempt_id="a1",
            site_epoch=4,
            components=[ReservationComponent("worker", "local")],
        )
    intent = svc.reserve(
        project_id="p1",
        mission_id="m1",
        attempt_id="a1",
        site_epoch=5,
        components=[ReservationComponent("worker", "local")],
    )
    assert intent.state == "reserved"
    with pytest.raises(ReservationError, match="duplicate"):
        svc.reserve(
            project_id="p1",
            mission_id="m1",
            attempt_id="a1",
            site_epoch=5,
            components=[ReservationComponent("worker", "local")],
        )


def test_capability_pack_cannot_widen() -> None:
    reg = CapabilityPackRegistry()
    reg.register(
        CapabilityPackManifest(
            pack_id="pack.demo",
            version="1",
            content_digest="x",
            capability_declarations=["read_logs"],
        )
    )
    with pytest.raises(ExtensionAuthzError, match="capability_widen"):
        reg.grant(
            ProjectPackGrant(
                project_id="p",
                pack_id="pack.demo",
                version="1",
                granted_capabilities=["read_logs", "admin"],
            )
        )


def test_portability_rejects_secrets(tmp_path) -> None:
    svc = PortabilityService()
    with pytest.raises(ValueError, match="secret_in_bundle"):
        svc.export_project(
            project_id="p",
            project_config={"api_key": "sk-secret"},
            out_dir=tmp_path,
        )
    bundle = svc.export_project(
        project_id="p",
        project_config={"name": "demo", "db_url": "env:SWARM_DATABASE_URL"},
        knowledge_refs=["kn_1"],
        out_dir=tmp_path,
    )
    loaded = svc.import_bundle(tmp_path / f"{bundle.bundle_id}.json")
    assert loaded.integrity_digest == bundle.integrity_digest


def test_resource_allocator_emits_receipt() -> None:
    fair = DurableFairnessStore()
    reservations = ReservationService(current_epoch=1)
    reservations.set_capacity("worker", "local", 4)
    reservations.set_capacity("provider", "rt_ollama_default", 4)
    reservations.set_capacity("tool", "gateway", 10)
    receipts = SchedulingReceiptLog()
    alloc = ResourceAllocator(
        fairness=fair, reservations=reservations, receipts=receipts, site_epoch=1
    )
    result = alloc.allocate(
        AllocationRequest(project_id="p", mission_id="m", attempt_id="a", tool_units=1)
    )
    assert result["intent"]["state"] == "reserved"
    assert result["receipt"]["decision"] == "dispatch"
