"""Worker enrollment helpers built on P4 ``WorkerIdentitySpec``.

Do not invent parallel identity types — use
:class:`~swarm.product.portable_config.WorkerIdentitySpec`,
:class:`~swarm.product.portable_config.SupportMatrix`, and
:class:`~swarm.product.portable_config.PublicEndpointConfig`.
"""

from __future__ import annotations

import platform
from typing import Any

from swarm.contracts.common import new_id
from swarm.product.portable_config import (
    SupportMatrix,
    WorkerIdentitySpec,
    default_support_matrix,
)
from swarm.workers.capability_authority import AuthorizationResult


def normalize_architecture(raw: str) -> str:
    machine = (raw or "unknown").strip().lower()
    return {
        "amd64": "amd64",
        "x86_64": "amd64",
        "x64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }.get(machine, machine or "unknown")


def normalize_platform(raw: str) -> str:
    system = (raw or "unknown").strip().lower()
    return {
        "linux": "linux",
        "darwin": "darwin",
        "macos": "darwin",
        "windows": "windows",
        "win32": "windows",
    }.get(system, system or "unknown")


def detect_platform_arch(*, container: bool = False) -> tuple[str, str]:
    """Return ``(platform, architecture)`` keys matching :class:`SupportMatrix`."""
    _ = container
    return (
        normalize_platform(platform.system()),
        normalize_architecture(platform.machine()),
    )


def primary_locality(privacy_classes: list[str] | None, data_locality: str | None = None) -> str:
    if data_locality and str(data_locality).strip():
        return str(data_locality).strip()
    classes = [str(c) for c in (privacy_classes or []) if str(c).strip()]
    for preferred in ("mac_local", "host_local", "site_bound", "region_bound", "local"):
        if preferred in classes:
            return preferred
    return classes[0] if classes else "local"


def build_worker_identity_spec(
    *,
    worker_id: str,
    node_identity: str,
    platform_name: str,
    architecture: str,
    runtime_version: str = "0.1.0",
    runtimes: list[str] | None = None,
    claimed_capabilities: list[str] | None = None,
    verified_capabilities: list[str] | None = None,
    resource_limits: dict[str, Any] | None = None,
    workspace_grants: list[str] | None = None,
    data_locality: str = "local",
    role: str = "worker",
) -> WorkerIdentitySpec:
    """Construct the shared P4 enrollment identity contract."""
    return WorkerIdentitySpec(
        worker_id=worker_id,
        node_identity=node_identity,
        platform=normalize_platform(platform_name),
        architecture=normalize_architecture(architecture),
        runtime_version=runtime_version,
        runtimes=list(runtimes or []),
        capabilities=list(claimed_capabilities or []),
        verified_capabilities=list(verified_capabilities or []),
        resource_limits=dict(resource_limits or {}),
        workspace_grants=list(workspace_grants or []),
        data_locality=data_locality,
        role=role,
    )


def identity_from_authorization(
    *,
    worker_id: str,
    node_identity: str,
    platform_name: str,
    architecture: str,
    authz: AuthorizationResult,
    runtime_version: str = "0.1.0",
    runtimes: list[str] | None = None,
    resource_limits: dict[str, Any] | None = None,
    workspace_grants: list[str] | None = None,
    privacy_classes: list[str] | None = None,
    data_locality: str | None = None,
    role: str = "worker",
    support_matrix: SupportMatrix | None = None,
) -> WorkerIdentitySpec:
    """Build identity; scheduling uses ``effective_capabilities()`` only when verified.

    Unsupported platforms remain inventoriable but must not receive verified
    (scheduling-eligible) capabilities. Default-allowlist grants without an
    explicit project policy stay ``authz.verified=False`` and are not written
    into ``verified_capabilities``.
    """
    matrix = support_matrix or default_support_matrix()
    plat = normalize_platform(platform_name)
    arch = normalize_architecture(architecture)
    platform_supported = matrix.is_supported(plat, arch)
    # Authority-granted caps become verified only with project policy + supported host.
    if platform_supported and authz.verified:
        verified = list(authz.granted)
    else:
        verified = []
    return build_worker_identity_spec(
        worker_id=worker_id,
        node_identity=node_identity,
        platform_name=plat,
        architecture=arch,
        runtime_version=runtime_version,
        runtimes=runtimes,
        claimed_capabilities=list(authz.claimed),
        verified_capabilities=verified,
        resource_limits=resource_limits,
        workspace_grants=workspace_grants,
        data_locality=primary_locality(privacy_classes, data_locality),
        role=role,
    )


def new_enrollment_nonce() -> str:
    return new_id("nonce_")
