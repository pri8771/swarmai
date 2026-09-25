"""Deployment profiles — topology + portable process roles.

Process roles (``server`` / ``worker`` / ``combined``) live in
:mod:`swarm.deploy.roles` and :class:`~swarm.product.portable_config.WorkerIdentitySpec`.
Profiles describe compose/DB binds; personal host names belong in labelled examples only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PROFILES = (
    "mock",
    "standalone",
    "hybrid",
    "recovery",
    "server",
    "worker",
    "combined",
    "mac_connector",  # labelled example / optional macOS adapter profile
)


@dataclass(frozen=True)
class DeployProfile:
    name: str
    description: str
    database: str
    bind_host: str
    public_db_port: bool
    public_inference_admin: bool
    non_root: bool
    allow_paid_cloud: bool
    secret_backend: str
    network_mode: str
    resource_limits: dict[str, Any] = field(default_factory=dict)
    process_role: str = "combined"  # server | worker | combined

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "database": self.database,
            "bind_host": self.bind_host,
            "public_db_port": self.public_db_port,
            "public_inference_admin": self.public_inference_admin,
            "non_root": self.non_root,
            "allow_paid_cloud": self.allow_paid_cloud,
            "secret_backend": self.secret_backend,
            "network_mode": self.network_mode,
            "resource_limits": self.resource_limits,
            "process_role": self.process_role,
            "production": False,
            "mock_vs_live": "local_artifacts_only",
        }


def get_profile(name: str) -> DeployProfile:
    profiles = {
        "mock": DeployProfile(
            name="mock",
            description="In-memory / fixture stack; no external providers",
            database="sqlite+memory or local postgres optional",
            bind_host="127.0.0.1",
            public_db_port=False,
            public_inference_admin=False,
            non_root=True,
            allow_paid_cloud=False,
            secret_backend="env_refs_only",
            network_mode="loopback",
            resource_limits={"api_workers": 1, "pool_size": 5, "max_sessions": 32},
            process_role="combined",
        ),
        "standalone": DeployProfile(
            name="standalone",
            description="Single-node local/docker compose; loopback binds",
            database="postgresql on internal network only",
            bind_host="127.0.0.1",
            public_db_port=False,
            public_inference_admin=False,
            non_root=True,
            allow_paid_cloud=False,
            secret_backend="env_or_file_refs",
            network_mode="bridge_internal",
            resource_limits={"api_workers": 2, "pool_size": 10, "max_sessions": 64},
            process_role="combined",
        ),
        "hybrid": DeployProfile(
            name="hybrid",
            description="Local control plane + optional private model endpoints",
            database="postgresql internal",
            bind_host="127.0.0.1",
            public_db_port=False,
            public_inference_admin=False,
            non_root=True,
            allow_paid_cloud=False,
            secret_backend="env_refs_only",
            network_mode="bridge_internal",
            resource_limits={"api_workers": 2, "pool_size": 10, "max_sessions": 64},
            process_role="combined",
        ),
        "recovery": DeployProfile(
            name="recovery",
            description="Restore-from-backup / fence-old-primary drills",
            database="restored postgresql snapshot",
            bind_host="127.0.0.1",
            public_db_port=False,
            public_inference_admin=False,
            non_root=True,
            allow_paid_cloud=False,
            secret_backend="env_refs_only",
            network_mode="loopback",
            resource_limits={"api_workers": 1, "pool_size": 5, "max_sessions": 16},
            process_role="server",
        ),
        "server": DeployProfile(
            name="server",
            description="Control-plane server role (Linux container baseline)",
            database="postgresql on compose network only",
            bind_host="127.0.0.1",
            public_db_port=False,
            public_inference_admin=False,
            non_root=True,
            allow_paid_cloud=False,
            secret_backend="env_or_file_refs",
            network_mode="bridge_internal",
            resource_limits={"api_workers": 2, "pool_size": 10, "max_sessions": 128},
            process_role="server",
        ),
        "worker": DeployProfile(
            name="worker",
            description="Generic worker connector; outbound to server; bounded task workspaces",
            database="none_on_worker_authoritative_on_server",
            bind_host="127.0.0.1",
            public_db_port=False,
            public_inference_admin=False,
            non_root=True,
            allow_paid_cloud=False,
            secret_backend="env_refs_only",
            network_mode="bridge_outbound",
            resource_limits={"api_workers": 0, "pool_size": 0, "max_sessions": 8},
            process_role="worker",
        ),
        "combined": DeployProfile(
            name="combined",
            description="Single process hosting server + worker roles",
            database="postgresql on compose network only",
            bind_host="127.0.0.1",
            public_db_port=False,
            public_inference_admin=False,
            non_root=True,
            allow_paid_cloud=False,
            secret_backend="env_or_file_refs",
            network_mode="bridge_internal",
            resource_limits={"api_workers": 2, "pool_size": 10, "max_sessions": 64},
            process_role="combined",
        ),
        "mac_connector": DeployProfile(
            name="mac_connector",
            description="Optional macOS adapter example; outbound to server; no local Postgres",
            database="none_on_mac_authoritative_on_server",
            bind_host="127.0.0.1",
            public_db_port=False,
            public_inference_admin=False,
            non_root=True,
            allow_paid_cloud=False,
            secret_backend="env_refs_only",
            network_mode="bridge_outbound",
            resource_limits={"api_workers": 0, "pool_size": 0, "max_sessions": 8},
            process_role="worker",
        ),
    }
    if name not in profiles:
        raise KeyError(f"unknown_profile:{name}")
    return profiles[name]
