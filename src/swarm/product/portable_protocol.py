"""In-process portable protocol proof: coordinator + worker roles.

Exercises server-created task → eligible worker claim → executor-backed result →
control-plane accept, plus revocation / isolation / unsupported rejection.
Two local containers (deploy/compose/portable-protocol.yml) are the Docker twin;
this module is the deterministic offline twin used by pytest.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.capabilities import CapabilityPackManifest, CapabilityPackRegistry, ProjectPackGrant
from swarm.contracts.common import new_id, utc_now
from swarm.contracts.fixtures import sample_task
from swarm.contracts.workspace import WorkerLease
from swarm.extensions.registry import ExtensionAuthzError
from swarm.product.portability import PortabilityService
from swarm.product.portable_config import (
    PortableConfigError,
    PortableInstallPaths,
    PublicEndpointConfig,
    SupportMatrix,
    WorkerIdentitySpec,
    default_support_matrix,
)
from swarm.workers.fleet import FleetError, FleetPlacementService
from swarm.workers.registry import WorkerAuthError, WorkerRegistryService


@dataclass
class ProtocolStepResult:
    name: str
    ok: bool
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": dict(self.detail)}


@dataclass
class PortableProtocolReport:
    scenario: str
    ok: bool
    steps: list[ProtocolStepResult] = field(default_factory=list)
    endpoint: dict[str, Any] = field(default_factory=dict)
    note: str = "in_process_two_role_protocol; docker twin optional"

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "ok": self.ok,
            "steps": [s.to_dict() for s in self.steps],
            "endpoint": dict(self.endpoint),
            "note": self.note,
            "named_r730_required": False,
        }


class PortableProtocolHarness:
    """Coordinator (server) + worker protocol without personal hostnames."""

    def __init__(
        self,
        *,
        endpoint: PublicEndpointConfig,
        install_paths: PortableInstallPaths,
        support: SupportMatrix | None = None,
        workspace: Path | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.install_paths = install_paths
        self.support = support or default_support_matrix()
        self.workspace = workspace or Path(install_paths.workspace_root)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.registry = WorkerRegistryService(heartbeat_ttl_seconds=30, lease_ttl_seconds=60)
        self.fleet = FleetPlacementService(self.registry)
        self.packs = CapabilityPackRegistry(require_signature=False)
        self.portability = PortabilityService()

    async def enroll_worker_async(
        self, identity: WorkerIdentitySpec, *, token: str, project_id: str | None = None
    ) -> WorkerLease:
        self.support.require(identity.platform, identity.architecture)
        effective = sorted(identity.effective_capabilities())
        if not effective:
            raise PortableConfigError("no_verified_capabilities")
        lease = WorkerLease(
            worker_id=identity.worker_id,
            node_identity=identity.node_identity,
            architecture=identity.architecture,
            runtime_version=identity.runtime_version,
            capacity_units=float(identity.resource_limits.get("capacity_units", 1.0)),
            capabilities=effective,
            labels=[identity.platform, identity.data_locality, identity.role],
        )
        return await self.registry.register(lease, token=token, project_id=project_id)

    def grant_pack(
        self,
        *,
        project_id: str,
        pack_id: str,
        version: str,
        declarations: list[str],
        granted: list[str],
    ) -> set[str]:
        manifest = CapabilityPackManifest(
            pack_id=pack_id,
            version=version,
            content_digest=hashlib.sha256(f"{pack_id}:{version}".encode()).hexdigest(),
            capability_declarations=declarations,
        )
        self.packs.register(manifest)
        self.packs.grant(
            ProjectPackGrant(
                project_id=project_id,
                pack_id=pack_id,
                version=version,
                granted_capabilities=granted,
            )
        )
        return self.packs.effective(project_id, pack_id, version)

    async def run_happy_path(
        self,
        *,
        worker: WorkerIdentitySpec,
        token: str,
        project_id: str = "proj_portable",
        tenant_id: str = "ten_portable",
    ) -> PortableProtocolReport:
        steps: list[ProtocolStepResult] = []
        report = PortableProtocolReport(
            scenario="happy_path_claim_execute_accept",
            ok=False,
            endpoint=self.endpoint.model_dump(),
        )

        # 1) Capability grant (authoritative) — self-labels cannot widen.
        try:
            effective = self.grant_pack(
                project_id=project_id,
                pack_id="pack.portable.exec",
                version="1",
                declarations=["chat", "tools.execute"],
                granted=["chat", "tools.execute"],
            )
            steps.append(
                ProtocolStepResult("capability_grant", True, {"effective": sorted(effective)})
            )
        except ExtensionAuthzError as exc:
            steps.append(ProtocolStepResult("capability_grant", False, {"error": str(exc)}))
            report.steps = steps
            return report

        # 2) Enroll eligible worker.
        try:
            enrolled = await self.enroll_worker_async(
                worker, token=token, project_id=project_id
            )
            self.fleet.bind_project_tenant(project_id, tenant_id)
            self.fleet.annotate_worker(
                enrolled.worker_id,
                tenant_id=tenant_id,
                locality=worker.data_locality,
                trust_class="compute_only",
            )
            placement = self.fleet.place(project_id=project_id)
            steps.append(
                ProtocolStepResult(
                    "enroll_and_place",
                    True,
                    {
                        "worker_id": enrolled.worker_id,
                        "placement": placement.to_dict(),
                        "capabilities": list(enrolled.capabilities),
                    },
                )
            )
        except (PortableConfigError, FleetError, WorkerAuthError) as exc:
            steps.append(ProtocolStepResult("enroll_and_place", False, {"error": str(exc)}))
            report.steps = steps
            return report

        # 3) Server creates task → worker claims → executes into workspace → submit.
        task = sample_task().model_copy(
            update={
                "id": new_id("task_"),
                "project_id": project_id,
                "required_capabilities": ["chat"],
                "objective": "portable_protocol_echo",
            }
        )
        self.registry.enqueue(task)
        claimed = await self.registry.claim_work(enrolled.worker_id, token=token)
        if not claimed.claimed or claimed.lease is None:
            steps.append(ProtocolStepResult("claim", False, {"error": "no_claim"}))
            report.steps = steps
            return report
        lease = claimed.lease
        artifact_path = self.workspace / f"{lease.task.id}.out"
        artifact_body = f"executed:{lease.task.objective}:{self.endpoint.public_hostname}\n"
        artifact_path.write_text(artifact_body, encoding="utf-8")
        digest = hashlib.sha256(artifact_body.encode()).hexdigest()
        submitted = self.registry.submit_result(
            lease_id=lease.lease_id,
            worker_id=enrolled.worker_id,
            generation=enrolled.lease_generation,
            token=token,
            status="succeeded",
            checks={"artifact_written": True},
            artifact_manifest={
                "path": str(artifact_path),
                "sha256": digest,
                "bytes": len(artifact_body.encode()),
            },
            summary="portable_protocol_ok",
        )
        accepted = self.registry.control_plane_accept_result(
            submitted["result_id"], accepted=True
        )
        steps.append(
            ProtocolStepResult(
                "claim_execute_accept",
                accepted.get("acceptance_state") == "accepted",
                {
                    "lease_id": lease.lease_id,
                    "result_id": submitted["result_id"],
                    "artifact_sha256": digest,
                    "acceptance_state": accepted.get("acceptance_state"),
                },
            )
        )

        report.steps = steps
        report.ok = all(s.ok for s in steps)
        return report

    async def run_reject_unsupported(
        self, *, worker: WorkerIdentitySpec, token: str
    ) -> PortableProtocolReport:
        steps: list[ProtocolStepResult] = []
        try:
            await self.enroll_worker_async(worker, token=token)
            steps.append(ProtocolStepResult("reject_unsupported", False, {"error": "enrolled"}))
            ok = False
        except PortableConfigError as exc:
            steps.append(
                ProtocolStepResult(
                    "reject_unsupported",
                    True,
                    {"error": str(exc), "platform": worker.platform, "arch": worker.architecture},
                )
            )
            ok = True
        return PortableProtocolReport(
            scenario="reject_unsupported_platform",
            ok=ok,
            steps=steps,
            endpoint=self.endpoint.model_dump(),
        )

    async def run_revocation(
        self,
        *,
        worker: WorkerIdentitySpec,
        token: str,
        project_id: str = "proj_portable",
    ) -> PortableProtocolReport:
        steps: list[ProtocolStepResult] = []
        enrolled = await self.enroll_worker_async(worker, token=token, project_id=project_id)
        task = sample_task().model_copy(
            update={
                "id": new_id("task_"),
                "project_id": project_id,
                "required_capabilities": list(enrolled.capabilities)[:1] or ["chat"],
            }
        )
        self.registry.enqueue(task)
        await self.registry.revoke_generation(enrolled.worker_id)
        try:
            await self.registry.claim_work(enrolled.worker_id, token=token)
            steps.append(ProtocolStepResult("revocation_blocks_claim", False, {}))
            ok = False
        except WorkerAuthError as exc:
            steps.append(
                ProtocolStepResult("revocation_blocks_claim", True, {"error": str(exc)})
            )
            ok = True
        return PortableProtocolReport(
            scenario="revocation",
            ok=ok,
            steps=steps,
            endpoint=self.endpoint.model_dump(),
        )

    async def run_isolation(
        self,
        *,
        worker_a: WorkerIdentitySpec,
        token_a: str,
        worker_b: WorkerIdentitySpec,
        token_b: str,
    ) -> PortableProtocolReport:
        steps: list[ProtocolStepResult] = []
        a = await self.enroll_worker_async(
            worker_a, token=token_a, project_id="proj_a"
        )
        b = await self.enroll_worker_async(
            worker_b, token=token_b, project_id="proj_b"
        )
        self.fleet.bind_project_tenant("proj_a", "ten_a")
        self.fleet.bind_project_tenant("proj_b", "ten_b")
        self.fleet.annotate_worker(a.worker_id, tenant_id="ten_a")
        self.fleet.annotate_worker(b.worker_id, tenant_id="ten_b")
        placed_a = self.fleet.place(project_id="proj_a")
        try:
            self.fleet.place(project_id="proj_a", preferred_locality="nonexistent")
            cross = False
        except FleetError:
            cross = True
        # Cross-tenant assert
        try:
            self.fleet.assert_same_tenant(
                actor_tenant="ten_a", resource_tenant="ten_b", action="read_workspace"
            )
            denied = False
        except FleetError:
            denied = True
        ok = placed_a.worker_id == a.worker_id and cross and denied and b.worker_id != a.worker_id
        steps.append(
            ProtocolStepResult(
                "tenant_isolation",
                ok,
                {
                    "placed_a": placed_a.worker_id,
                    "worker_b": b.worker_id,
                    "cross_locality_rejected": cross,
                    "cross_tenant_denied": denied,
                    "at": utc_now().isoformat(),
                },
            )
        )
        return PortableProtocolReport(
            scenario="isolation",
            ok=ok,
            steps=steps,
            endpoint=self.endpoint.model_dump(),
        )

    def run_recovery_persist(self, *, out_dir: Path) -> PortableProtocolReport:
        """Export/import portability bundle across install roots (persistent recovery)."""
        steps: list[ProtocolStepResult] = []
        out_dir.mkdir(parents=True, exist_ok=True)
        bundle = self.portability.export_project(
            project_id="proj_portable",
            project_config={
                "public_hostname": self.endpoint.public_hostname,
                "api_base_url": self.endpoint.api_base_url,
                "install_root": self.install_paths.install_root,
                "workspace_root": self.install_paths.workspace_root,
                "db_url": "env:SWARM_DATABASE_URL",
            },
            capability_pack_config={"pack.portable.exec": "1"},
            version_manifest={"portable_protocol": "1"},
            out_dir=out_dir,
        )
        loaded = self.portability.import_bundle(out_dir / f"{bundle.bundle_id}.json")
        ok = loaded.integrity_digest == bundle.integrity_digest
        steps.append(
            ProtocolStepResult(
                "portability_export_import",
                ok,
                {
                    "bundle_id": bundle.bundle_id,
                    "integrity_digest": bundle.integrity_digest,
                    "hostname": loaded.project_config.get("public_hostname"),
                },
            )
        )
        return PortableProtocolReport(
            scenario="persistent_recovery",
            ok=ok,
            steps=steps,
            endpoint=self.endpoint.model_dump(),
        )
