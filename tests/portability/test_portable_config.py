"""P4 portability acceptance — alternate hostnames/URLs/identities/paths/platforms."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from swarm.product.portable_config import (
    EXAMPLE_HOSTNAMES,
    PortableConfigError,
    PortableInstallPaths,
    PublicEndpointConfig,
    SupportMatrix,
    WorkerIdentitySpec,
    default_support_matrix,
)


@pytest.mark.parametrize(
    "hostname,api",
    [
        ("swarm.example.local", "http://swarm.example.local:8765"),
        ("coordinator.example.test", "https://coordinator.example.test"),
        ("localhost", "http://127.0.0.1:8765"),
        ("api.internal.test", "http://api.internal.test:9000/v1"),
        # Named reference deploy remains valid *when configured* — not hard-required.
        ("swarm.splitsignal.ai", "https://swarm.splitsignal.ai"),
    ],
)
def test_alternate_hostnames_and_urls(hostname: str, api: str) -> None:
    cfg = PublicEndpointConfig(public_hostname=hostname, api_base_url=api)
    assert cfg.public_hostname == hostname.lower()
    assert cfg.api_base_url.startswith("http")
    assert cfg.matches_configured_hostname(hostname)


def test_endpoint_from_env_requires_explicit_config() -> None:
    with pytest.raises(PortableConfigError):
        PublicEndpointConfig.from_env({})
    cfg = PublicEndpointConfig.from_env(
        {
            "SWARM_PUBLIC_HOSTNAME": "worker-a.example.test",
            "SWARM_API_BASE_URL": "http://worker-a.example.test:8765",
            "SWARM_PUBLIC_BASE_URL": "https://edge.example.test",
        }
    )
    assert cfg.public_hostname == "worker-a.example.test"
    assert cfg.public_base_url == "https://edge.example.test"


def test_invalid_hostname_rejected() -> None:
    with pytest.raises(ValidationError):
        PublicEndpointConfig(public_hostname="", api_base_url="http://x")
    with pytest.raises(ValidationError):
        PublicEndpointConfig(public_hostname="-bad-.host", api_base_url="http://x.example")


def test_worker_identities_vary() -> None:
    a = WorkerIdentitySpec(
        worker_id="wk_alpha",
        node_identity="node-alpha",
        platform="linux",
        architecture="amd64",
        capabilities=["chat", "admin"],
        verified_capabilities=["chat"],  # admin not verified → not effective
        role="worker",
    )
    b = WorkerIdentitySpec(
        worker_id="wk_bravo",
        node_identity="node-bravo",
        platform="darwin",
        architecture="arm64",
        capabilities=["chat"],
        verified_capabilities=["chat"],
        role="combined",
    )
    assert a.effective_capabilities() == {"chat"}
    assert "admin" not in a.effective_capabilities()
    assert b.role == "combined"
    with pytest.raises(ValidationError):
        WorkerIdentitySpec(
            worker_id="wk_x",
            node_identity="n",
            platform="linux",
            architecture="amd64",
            role="peer_consensus",  # deferred — not MVP
        )


def test_install_and_workspace_paths(tmp_path: Path) -> None:
    paths = PortableInstallPaths(
        install_root=str(tmp_path / "opt" / "swarm"),
        workspace_root=str(tmp_path / "var" / "workspaces" / "t1"),
        data_root=str(tmp_path / "var" / "data"),
        config_path=str(tmp_path / "etc" / "swarm.toml"),
    )
    as_paths = paths.as_paths()
    assert as_paths["install_root"] == tmp_path / "opt" / "swarm"
    with pytest.raises(ValidationError, match="personal_path_forbidden"):
        PortableInstallPaths(
            install_root="/Users/pchordia/Downloads/swarm-ai-v2-runtime",
            workspace_root=str(tmp_path / "ws"),
        )


def test_support_matrix_accepts_and_rejects() -> None:
    matrix = default_support_matrix()
    assert matrix.is_supported("linux", "amd64")
    assert matrix.is_supported("darwin", "arm64")
    matrix.require("linux", "arm64")
    with pytest.raises(PortableConfigError, match="unsupported_platform_arch"):
        matrix.require("windows", "amd64")
    with pytest.raises(PortableConfigError, match="unsupported_platform_arch"):
        matrix.require("freebsd", "amd64")
    payload = matrix.to_dict()
    assert payload["unqualified_claim"] is False
    assert "linux/amd64" in payload["supported"]


def test_example_hostnames_documented() -> None:
    assert "coordinator.example.test" in EXAMPLE_HOSTNAMES
    assert "swarm.example.local" in EXAMPLE_HOSTNAMES


def test_custom_support_matrix_narrow() -> None:
    matrix = SupportMatrix(supported={"linux/amd64"}, baseline="linux/amd64")
    matrix.require("linux", "amd64")
    with pytest.raises(PortableConfigError):
        matrix.require("linux", "arm64")
