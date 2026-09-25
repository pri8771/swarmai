"""Portable deployment contracts shared by P1/P2/P4.

Hostname, API/public URLs, worker identity, install/workspace paths, and the
explicit support matrix are config — never personal machine names. Self-reported
capability labels alone cannot grant access; grants and placement remain
authoritative (capability packs + fleet).

P1 owns freeze/harness hostname wiring against this config.
P2 owns roles / enrollment / support-matrix expansion.
P4 owns acceptance probes that exercise alternate values.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import Field, field_validator

from swarm.contracts.common import StrictModel

# Examples / docs should prefer these generic stand-ins.
EXAMPLE_HOSTNAMES = frozenset(
    {
        "swarm.example.local",
        "coordinator.example.test",
        "worker-a.example.test",
        "localhost",
        "127.0.0.1",
    }
)

# Personal checkout path fragments must not appear in portable install configs.
PERSONAL_PATH_FRAGMENTS = (
    "/users/pchordia",
    "/home/pchordia",
    "downloads/swarm-ai",
)

_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
)


class PortableConfigError(ValueError):
    """Raised when portable deployment config is missing or unsafe."""


class PublicEndpointConfig(StrictModel):
    """Deployment endpoint surface — validated from explicit config / env.

    Any syntactically valid hostname is accepted when supplied by the operator
    (including a named reference deploy). Product code must not hard-require one
    literal hostname; P1 freeze integrity checks against this config instead.
    """

    public_hostname: str
    api_base_url: str
    public_base_url: str | None = None
    bind_host: str = "127.0.0.1"
    bind_port: int = 8765

    @field_validator("public_hostname")
    @classmethod
    def _hostname_ok(cls, value: str) -> str:
        host = value.strip().lower()
        if not host:
            raise ValueError("public_hostname_required")
        if host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
            return host
        if not _HOSTNAME_RE.match(host):
            raise ValueError(f"invalid_hostname:{host}")
        return host

    @field_validator("api_base_url", "public_base_url")
    @classmethod
    def _url_ok(cls, value: str | None) -> str | None:
        if value is None:
            return None
        raw = value.strip()
        if not raw:
            raise ValueError("url_empty")
        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"unsupported_url_scheme:{parsed.scheme}")
        if not parsed.netloc:
            raise ValueError("url_missing_netloc")
        return raw.rstrip("/")

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> PublicEndpointConfig:
        env = environ if environ is not None else dict(os.environ)
        hostname = (env.get("SWARM_PUBLIC_HOSTNAME") or env.get("SWARM_HOSTNAME") or "").strip()
        api = (env.get("SWARM_API_BASE_URL") or env.get("SWARM_SERVER_URL") or "").strip()
        public = (env.get("SWARM_PUBLIC_BASE_URL") or "").strip() or None
        if not hostname and api:
            hostname = (urlparse(api).hostname or "").lower()
        if not hostname:
            raise PortableConfigError("SWARM_PUBLIC_HOSTNAME_or_SWARM_API_BASE_URL_required")
        if not api:
            raise PortableConfigError("SWARM_API_BASE_URL_or_SWARM_SERVER_URL_required")
        bind_host = (env.get("SWARM_BIND_HOST") or "127.0.0.1").strip()
        bind_port = int(env.get("SWARM_PORT") or env.get("SWARM_BIND_PORT") or "8765")
        return cls(
            public_hostname=hostname,
            api_base_url=api,
            public_base_url=public,
            bind_host=bind_host,
            bind_port=bind_port,
        )

    def matches_configured_hostname(self, configured: str) -> bool:
        """True when freeze/deployment hostname matches this endpoint config."""
        return self.public_hostname == configured.strip().lower()


class WorkerIdentitySpec(StrictModel):
    """Enrolled worker identity contract (P2) — labels alone do not grant access."""

    worker_id: str
    node_identity: str
    platform: str
    architecture: str
    runtime_version: str = "0.1.0"
    runtimes: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    verified_capabilities: list[str] = Field(default_factory=list)
    resource_limits: dict[str, Any] = Field(default_factory=dict)
    workspace_grants: list[str] = Field(default_factory=list)
    data_locality: str = "local"
    role: str = "worker"  # server | worker | combined

    @field_validator("role")
    @classmethod
    def _role_ok(cls, value: str) -> str:
        role = value.strip().lower()
        if role not in {"server", "worker", "combined"}:
            raise ValueError(f"unsupported_role:{role}")
        return role

    def effective_capabilities(self) -> set[str]:
        """Only verified ∩ declared capabilities are scheduling-eligible."""
        declared = set(self.capabilities)
        verified = set(self.verified_capabilities)
        if not verified:
            return set()
        return declared & verified


class PortableInstallPaths(StrictModel):
    """Install / workspace roots — must not encode personal checkout paths."""

    install_root: str
    workspace_root: str
    data_root: str | None = None
    config_path: str | None = None

    @field_validator("install_root", "workspace_root", "data_root", "config_path")
    @classmethod
    def _path_ok(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            raise ValueError("path_empty")
        lowered = text.lower().replace("\\", "/")
        for frag in PERSONAL_PATH_FRAGMENTS:
            if frag in lowered:
                raise ValueError(f"personal_path_forbidden:{text}")
        return text

    def as_paths(self) -> dict[str, Path]:
        out = {
            "install_root": Path(self.install_root),
            "workspace_root": Path(self.workspace_root),
        }
        if self.data_root:
            out["data_root"] = Path(self.data_root)
        if self.config_path:
            out["config_path"] = Path(self.config_path)
        return out


@dataclass(frozen=True)
class PlatformArch:
    platform: str
    architecture: str

    def key(self) -> str:
        return f"{self.platform}/{self.architecture}"


@dataclass
class SupportMatrix:
    """Explicit support matrix (P2) — prefer Linux container + narrow native adapters."""

    supported: set[str] = field(
        default_factory=lambda: {
            "linux/amd64",
            "linux/arm64",
            "darwin/arm64",  # narrow macOS adapter — not unqualified
        }
    )
    baseline: str = "linux/amd64"
    notes: dict[str, str] = field(
        default_factory=lambda: {
            "linux/amd64": "container_baseline",
            "linux/arm64": "container_baseline",
            "darwin/arm64": "narrow_native_adapter",
        }
    )

    def is_supported(self, platform: str, architecture: str) -> bool:
        return PlatformArch(platform.lower(), architecture.lower()).key() in self.supported

    def require(self, platform: str, architecture: str) -> PlatformArch:
        pa = PlatformArch(platform.lower(), architecture.lower())
        if pa.key() not in self.supported:
            raise PortableConfigError(f"unsupported_platform_arch:{pa.key()}")
        return pa

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline": self.baseline,
            "supported": sorted(self.supported),
            "notes": dict(self.notes),
            "unqualified_claim": False,
        }


def default_support_matrix() -> SupportMatrix:
    return SupportMatrix()
