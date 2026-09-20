"""Deployment profiles — mock, standalone, hybrid, recovery (offline-safe)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PROFILES = ("mock", "standalone", "hybrid", "recovery")


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
        ),
    }
    if name not in profiles:
        raise KeyError(f"unknown_profile:{name}")
    return profiles[name]
