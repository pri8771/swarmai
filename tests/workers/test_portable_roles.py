"""P2 portable roles — process roles, WorkerIdentitySpec scheduling, support matrix."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.contracts.common import new_id
from swarm.contracts.fixtures import sample_task
from swarm.contracts.workspace import WorkerLease
from swarm.deploy.roles import (
    RoleConfigError,
    resolve_process_role,
    role_starts_server,
    role_starts_worker,
    validate_role_profile,
)
from swarm.product.portable_config import (
    PortableConfigError,
    PublicEndpointConfig,
    SupportMatrix,
    WorkerIdentitySpec,
    default_support_matrix,
)
from swarm.workers.capability_authority import CapabilityAuthority
from swarm.workers.connector import default_worker_executor, unsupported_result
from swarm.workers.identity import identity_from_authorization, normalize_architecture
from swarm.workers.placement_contracts import PlacementContract
from swarm.workers.registry import WorkerRegistryService
from swarm.workspace.grants import WorkspaceBoundError, WorkspaceGrantRegistry


def test_process_roles_resolve() -> None:
    assert resolve_process_role(explicit="server") == "server"
    assert resolve_process_role(explicit="mac_connector") == "worker"
    assert resolve_process_role(environ={}) == "combined"
    assert role_starts_server("combined") and role_starts_worker("combined")
    assert role_starts_server("server") and not role_starts_worker("server")
    validate_role_profile(role="worker", profile="worker")
    with pytest.raises(RoleConfigError):
        validate_role_profile(role="server", profile="mac_connector")


def test_worker_identity_spec_effective_caps_not_labels() -> None:
    auth = CapabilityAuthority()
    auth.set_project_grants("proj_a", {"chat", "extract"})
    result = auth.authorize(
        project_id="proj_a",
        requested=["chat", "admin", "extract"],
        labels=["admin", "gpu"],  # labels must not grant admin
    )
    assert "admin" not in result.granted
    assert set(result.granted) == {"chat", "extract"}
    identity = identity_from_authorization(
        worker_id="wk_1",
        node_identity="node-1",
        platform_name="linux",
        architecture="x86_64",
        authz=result,
        role="worker",
    )
    assert isinstance(identity, WorkerIdentitySpec)
    assert identity.architecture == "amd64"
    assert identity.effective_capabilities() == {"chat", "extract"}
    assert "admin" not in identity.effective_capabilities()


def test_placement_by_contract_not_hostname() -> None:
    contract = PlacementContract.for_task(
        required_capabilities=["extract"],
        scopes=["mac_local"],
    )
    assert contract.worker_eligible(
        granted_capabilities=["extract"],
        authorized_locality=["mac_local", "local"],
        labels=["bob-macbook"],
        host_alias="Bob's MacBook Pro",
    )
    assert not contract.worker_eligible(
        granted_capabilities=["extract"],
        authorized_locality=["local"],  # missing mac_local grant
        host_alias="Bob's MacBook Pro",
    )
    assert not contract.worker_eligible(
        granted_capabilities=[],  # labels alone ≠ access
        authorized_locality=["mac_local"],
        labels=["extract", "mac.local.extract"],
    )


@pytest.mark.asyncio
async def test_registry_labels_do_not_authorize() -> None:
    reg = WorkerRegistryService()
    token = new_id("wt_")
    lease = await reg.register(
        WorkerLease(
            node_identity="node-labelled",
            architecture="amd64",
            runtime_version="0.1.0",
            capacity_units=1.0,
            capabilities=[],  # no granted caps
            labels=["extract", "admin"],
        ),
        token=token,
        project_id="proj_a",
    )
    reg._workers[lease.worker_id].privacy_classes = {"local"}
    reg.enqueue(
        sample_task().model_copy(
            update={
                "id": new_id("tsk_"),
                "required_capabilities": ["extract"],
                "scopes": ["local_only"],
            }
        )
    )
    claimed = await reg.claim_work(lease.worker_id, token=token)
    assert claimed.claimed is False


def test_support_matrix_linux_baseline() -> None:
    matrix = default_support_matrix()
    assert isinstance(matrix, SupportMatrix)
    assert matrix.baseline == "linux/amd64"
    assert matrix.is_supported("linux", "amd64")
    with pytest.raises(PortableConfigError):
        matrix.require("windows", "amd64")
    payload = matrix.to_dict()
    assert payload["unqualified_claim"] is False


def test_public_endpoint_config_reusable() -> None:
    cfg = PublicEndpointConfig(
        public_hostname="worker.example.local",
        api_base_url="http://worker.example.local:8765",
    )
    assert cfg.matches_configured_hostname("worker.example.local")


def test_generic_executor_no_echo_success(tmp_path: Path) -> None:
    claim = {
        "task": {
            "id": "tsk_echo",
            "scopes": ["local"],
            "required_capabilities": ["chat"],
        }
    }
    produced = default_worker_executor(claim, tmp_path)
    assert produced["status"] in {"unsupported", "blocked"}
    assert produced["status"] != "completed"
    bare = unsupported_result({"id": "x"}, reason="test")
    assert bare["status"] == "unsupported"


def test_bounded_workspace_rejects_escape_and_repo(tmp_path: Path) -> None:
    registry = WorkspaceGrantRegistry()
    grant = registry.issue(
        worker_id="wk_1",
        project_id="proj_a",
        root_path=tmp_path / "ws",
    )
    ws = registry.bind(grant.grant_id)
    ws.write_text("out.txt", "ok")
    with pytest.raises(WorkspaceBoundError):
        ws.resolve("../escape.txt")
    # Refuse issuing grant on a fake whole-repo root.
    fake_repo = tmp_path / "checkout"
    (fake_repo / ".git").mkdir(parents=True)
    (fake_repo / "src").mkdir()
    with pytest.raises(WorkspaceBoundError, match="whole_repo"):
        registry.issue(worker_id="wk_1", project_id="proj_a", root_path=fake_repo)


def test_normalize_architecture_matches_matrix() -> None:
    assert normalize_architecture("x86_64") == "amd64"
    assert normalize_architecture("aarch64") == "arm64"
