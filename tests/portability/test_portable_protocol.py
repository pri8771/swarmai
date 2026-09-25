"""P4 portable protocol — execution, unsupported, recovery, revocation, isolation."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.capabilities import CapabilityPackManifest, CapabilityPackRegistry, ProjectPackGrant
from swarm.contracts.common import new_id
from swarm.extensions.registry import ExtensionAuthzError
from swarm.product.portability import PortabilityService
from swarm.product.portable_config import (
    PortableInstallPaths,
    PublicEndpointConfig,
    WorkerIdentitySpec,
    default_support_matrix,
)
from swarm.product.portable_protocol import PortableProtocolHarness


def _endpoint(hostname: str = "coordinator.example.test", port: int = 8765) -> PublicEndpointConfig:
    return PublicEndpointConfig(
        public_hostname=hostname,
        api_base_url=f"http://{hostname}:{port}",
        public_base_url=f"https://{hostname}",
    )


def _paths(tmp_path: Path, suffix: str = "a") -> PortableInstallPaths:
    root = tmp_path / f"install-{suffix}"
    ws = tmp_path / f"ws-{suffix}"
    data = tmp_path / f"data-{suffix}"
    root.mkdir(parents=True)
    ws.mkdir(parents=True)
    data.mkdir(parents=True)
    return PortableInstallPaths(
        install_root=str(root),
        workspace_root=str(ws),
        data_root=str(data),
    )


def _worker(
    *,
    platform: str = "linux",
    arch: str = "amd64",
    caps: list[str] | None = None,
    verified: list[str] | None = None,
    worker_id: str | None = None,
) -> WorkerIdentitySpec:
    caps = caps or ["chat", "tools.execute"]
    verified = verified if verified is not None else list(caps)
    return WorkerIdentitySpec(
        worker_id=worker_id or new_id("wk_"),
        node_identity=f"node-{platform}-{arch}",
        platform=platform,
        architecture=arch,
        capabilities=caps,
        verified_capabilities=verified,
        runtimes=["native"],
        resource_limits={"capacity_units": 1.0},
        workspace_grants=["bounded"],
        role="worker",
    )


@pytest.fixture
def harness(tmp_path: Path) -> PortableProtocolHarness:
    return PortableProtocolHarness(
        endpoint=_endpoint(),
        install_paths=_paths(tmp_path),
        support=default_support_matrix(),
        workspace=tmp_path / "ws-a",
    )


@pytest.mark.asyncio
async def test_fresh_startup_outside_original_checkout(tmp_path: Path) -> None:
    """Prove startup/config works from a fresh root — not the original Mac checkout."""
    fresh = tmp_path / "fresh-root"
    (fresh / "opt" / "swarm").mkdir(parents=True)
    (fresh / "var" / "workspace").mkdir(parents=True)
    h = PortableProtocolHarness(
        endpoint=_endpoint("api.fresh.test"),
        install_paths=PortableInstallPaths(
            install_root=str(fresh / "opt" / "swarm"),
            workspace_root=str(fresh / "var" / "workspace"),
            data_root=str(fresh / "var" / "data"),
        ),
        workspace=fresh / "var" / "workspace",
    )
    report = await h.run_happy_path(worker=_worker(), token=new_id("wt_"))
    assert report.ok
    assert report.endpoint["public_hostname"] == "api.fresh.test"
    assert "pchordia" not in report.endpoint["api_base_url"]
    art_steps = [s for s in report.steps if s.name == "claim_execute_accept"]
    assert art_steps and art_steps[0].ok
    outputs = list(fresh.joinpath("var", "workspace").glob("task_*.out"))
    assert len(outputs) == 1
    assert "portable_protocol_echo" in outputs[0].read_text(encoding="utf-8")
    assert "api.fresh.test" in outputs[0].read_text(encoding="utf-8")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "hostname",
    ["swarm.example.local", "coord-east.example.test", "127.0.0.1"],
)
async def test_correct_execution_across_hostnames(tmp_path: Path, hostname: str) -> None:
    h = PortableProtocolHarness(
        endpoint=_endpoint(hostname),
        install_paths=_paths(tmp_path, hostname.replace(".", "-")),
        workspace=tmp_path / f"ws-{hostname.replace('.', '-')}",
    )
    report = await h.run_happy_path(worker=_worker(), token=new_id("wt_"))
    assert report.ok
    assert report.endpoint["public_hostname"] == hostname.lower()


@pytest.mark.asyncio
async def test_reject_unsupported_platform(harness: PortableProtocolHarness) -> None:
    report = await harness.run_reject_unsupported(
        worker=_worker(platform="windows", arch="amd64", caps=["chat"], verified=["chat"]),
        token=new_id("wt_"),
    )
    assert report.ok
    assert report.scenario == "reject_unsupported_platform"


@pytest.mark.asyncio
async def test_self_reported_capabilities_cannot_grant_access(
    harness: PortableProtocolHarness,
) -> None:
    """Labels / declared-only caps do not enroll; verified intersection required."""
    with pytest.raises(Exception) as excinfo:
        await harness.enroll_worker_async(
            _worker(caps=["chat", "admin"], verified=[]),
            token=new_id("wt_"),
        )
    assert "no_verified_capabilities" in str(excinfo.value)


def test_capability_grant_cannot_widen() -> None:
    reg = CapabilityPackRegistry()
    reg.register(
        CapabilityPackManifest(
            pack_id="pack.portable",
            version="1",
            content_digest="abc",
            capability_declarations=["chat"],
        )
    )
    with pytest.raises(ExtensionAuthzError, match="capability_widen"):
        reg.grant(
            ProjectPackGrant(
                project_id="p",
                pack_id="pack.portable",
                version="1",
                granted_capabilities=["chat", "admin"],
            )
        )


@pytest.mark.asyncio
async def test_revocation_blocks_further_claims(harness: PortableProtocolHarness) -> None:
    report = await harness.run_revocation(worker=_worker(), token=new_id("wt_"))
    assert report.ok


@pytest.mark.asyncio
async def test_tenant_isolation(harness: PortableProtocolHarness) -> None:
    report = await harness.run_isolation(
        worker_a=_worker(worker_id="wk_iso_a"),
        token_a=new_id("wt_"),
        worker_b=_worker(worker_id="wk_iso_b"),
        token_b=new_id("wt_"),
    )
    assert report.ok


def test_persistent_recovery_export_import(harness: PortableProtocolHarness, tmp_path: Path) -> None:
    report = harness.run_recovery_persist(out_dir=tmp_path / "bundles")
    assert report.ok
    # Second install root can re-import.
    other = tmp_path / "other-install" / "bundles"
    other.mkdir(parents=True)
    src = next((tmp_path / "bundles").glob("port_*.json"))
    dest = other / src.name
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    loaded = PortabilityService().import_bundle(dest)
    assert loaded.project_config["public_hostname"] == "coordinator.example.test"


@pytest.mark.asyncio
async def test_placement_prefers_authorized_locality(tmp_path: Path) -> None:
    h = PortableProtocolHarness(
        endpoint=_endpoint(),
        install_paths=_paths(tmp_path),
        workspace=tmp_path / "ws-a",
    )
    token = new_id("wt_")
    worker = _worker()
    enrolled = await h.enroll_worker_async(worker, token=token, project_id="proj_portable")
    h.fleet.bind_project_tenant("proj_portable", "ten_portable")
    h.fleet.annotate_worker(
        enrolled.worker_id, tenant_id="ten_portable", locality="edge", trust_class="compute_only"
    )
    decision = h.fleet.place(project_id="proj_portable", preferred_locality="edge")
    assert decision.worker_id == enrolled.worker_id
    assert decision.locality == "edge"
