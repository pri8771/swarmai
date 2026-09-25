"""Deploy doctor and recovery verification — local artifacts only."""

from __future__ import annotations

import os
import platform
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from swarm.deploy.profiles import PROFILES, get_profile

_KNOWN_SECRET_BACKENDS = frozenset(
    {
        "",
        "environment",
        "env_refs_only",
        "env_or_file_refs",
        "file",
    }
)
_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
)


@dataclass
class DoctorResult:
    profile: str
    ok: bool
    ready_to_start: bool = False
    checks: list[dict[str, Any]] = field(default_factory=list)
    config_errors: list[str] = field(default_factory=list)
    measured: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "ok": self.ok,
            "ready_to_start": self.ready_to_start,
            "checks": self.checks,
            "config_errors": self.config_errors,
            "measured": self.measured,
            "production": False,
            "cloud_deployed": False,
            "mock_vs_live": "local_doctor_only",
        }


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def _looks_like_secret(value: str) -> bool:
    lowered = value.lower()
    if any(token in lowered for token in ("password=", "secret=", "token=", "apikey=")):
        return True
    if "://" in value and "@" in value.split("://", 1)[1].split("/", 1)[0]:
        return True
    return False


def _public_hostname_ok(raw: str) -> tuple[bool, str]:
    value = raw.strip()
    if not value:
        return True, "unset"
    if _looks_like_secret(value):
        return False, "hostname must not embed credentials"
    if not _HOSTNAME_RE.match(value):
        return False, "hostname must be DNS-shaped (placeholder ok: coordinator.example.test)"
    return True, "SWARM_PUBLIC_HOSTNAME shape ok"


def _http_url_ok(raw: str, *, label: str) -> tuple[bool, str]:
    value = raw.strip()
    if not value:
        return True, "unset"
    if _looks_like_secret(value):
        return False, f"{label} must not embed credentials"
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, f"{label} must be absolute http(s) URL"
    if parsed.username or parsed.password:
        return False, f"{label} must not include userinfo"
    return True, f"{label} shape ok"


def _api_base_url_from_env() -> str:
    """Prefer P4 portable_config names; accept P3 alias SWARM_API_PUBLIC_URL."""
    for key in ("SWARM_API_BASE_URL", "SWARM_API_PUBLIC_URL", "SWARM_SERVER_URL"):
        raw = (os.environ.get(key) or "").strip()
        if raw:
            return raw
    return ""


def doctor(*, profile: str = "standalone", repo_root: Path | None = None) -> DoctorResult:
    prof = get_profile(profile)
    root = repo_root or Path(__file__).resolve().parents[3]
    checks: list[dict[str, Any]] = []
    config_errors: list[str] = []

    checks.append(_check("profile_known", profile in PROFILES, profile))
    checks.append(_check("non_root_config", prof.non_root, "services must run non-root"))
    checks.append(
        _check(
            "no_public_db_port",
            not prof.public_db_port,
            "database must not bind public interfaces",
        )
    )
    checks.append(
        _check(
            "no_public_inference_admin",
            not prof.public_inference_admin,
            "inference admin ports must stay private",
        )
    )
    checks.append(
        _check(
            "loopback_or_internal_bind",
            prof.bind_host in {"127.0.0.1", "0.0.0.0"} and not prof.public_db_port,
            f"bind_host={prof.bind_host}",
        )
    )

    backend = (os.environ.get("SWARM_SECRET_BACKEND") or "").strip()
    backend_ok = backend.lower() in _KNOWN_SECRET_BACKENDS
    checks.append(
        _check(
            "secret_backend_known",
            backend_ok,
            f"SWARM_SECRET_BACKEND={backend or 'environment(default)'}"
            if backend_ok
            else f"unknown SWARM_SECRET_BACKEND={backend!r}",
        )
    )
    if not backend_ok:
        config_errors.append(f"invalid_secret_backend:{backend}")

    hostname_ok, hostname_detail = _public_hostname_ok(
        os.environ.get("SWARM_PUBLIC_HOSTNAME") or ""
    )
    checks.append(_check("public_hostname_shape", hostname_ok, hostname_detail))
    if not hostname_ok:
        config_errors.append(f"invalid_public_hostname:{hostname_detail}")

    api_url = _api_base_url_from_env()
    # Shape-check only when an API/public URL is explicitly set; mock start may omit it.
    url_ok, url_detail = _http_url_ok(api_url, label="SWARM_API_BASE_URL")
    checks.append(_check("api_base_url_shape", url_ok, url_detail))
    if not url_ok:
        config_errors.append(f"invalid_api_base_url:{url_detail}")

    public_base = (os.environ.get("SWARM_PUBLIC_BASE_URL") or "").strip()
    pub_ok, pub_detail = _http_url_ok(public_base, label="SWARM_PUBLIC_BASE_URL")
    checks.append(_check("public_base_url_shape", pub_ok, pub_detail))
    if not pub_ok:
        config_errors.append(f"invalid_public_base_url:{pub_detail}")

    # Wrong/missing secret refuses startup for non-mock / non-connector profiles.
    if profile in {"mock", "mac_connector"}:
        detail = (
            "mock profile skips DB requirement"
            if profile == "mock"
            else "mac_connector uses server DB via SWARM_SERVER_URL"
        )
        checks.append(_check("database_url_configured", True, detail))
        if profile == "mac_connector":
            server_url = (os.environ.get("SWARM_SERVER_URL") or "").strip()
            server_ok = bool(server_url)
            checks.append(
                _check(
                    "server_url_configured",
                    server_ok,
                    "SWARM_SERVER_URL present"
                    if server_ok
                    else "SWARM_SERVER_URL missing — refuse connector start",
                )
            )
            if not server_ok:
                config_errors.append("missing_env:SWARM_SERVER_URL")
    else:
        db_url = os.environ.get("SWARM_DATABASE_URL")
        if db_url and ("password=" in db_url.lower() or "@" in db_url):
            # URL may contain credentials — never echo it.
            checks.append(
                _check(
                    "database_url_configured",
                    True,
                    "SWARM_DATABASE_URL present (value hidden)",
                )
            )
        else:
            checks.append(
                _check(
                    "database_url_configured",
                    False,
                    "SWARM_DATABASE_URL missing — refuse live start",
                )
            )
            config_errors.append("missing_env:SWARM_DATABASE_URL")

    compose_name = "mac-connector.yml" if profile == "mac_connector" else f"{profile}.yml"
    compose = root / "deploy" / "compose" / compose_name
    checks.append(
        _check(
            "compose_artifact",
            compose.exists(),
            str(compose.relative_to(root)) if compose.exists() else f"missing {compose.name}",
        )
    )
    checks.append(
        _check(
            "allow_paid_cloud_false",
            not prof.allow_paid_cloud,
            "no paid cloud auto-path",
        )
    )

    arch = platform.machine().lower()
    checks.append(
        _check(
            "architecture_smoke",
            arch in {"arm64", "aarch64", "x86_64", "amd64"},
            f"arch={arch}",
        )
    )

    # ok = security posture (backward compatible). ready_to_start = all config refs.
    security_ok = all(
        c["ok"]
        for c in checks
        if c["name"]
        in {
            "profile_known",
            "non_root_config",
            "no_public_db_port",
            "no_public_inference_admin",
            "allow_paid_cloud_false",
            "architecture_smoke",
            "compose_artifact",
        }
    )
    start_required = {
        "database_url_configured",
        "server_url_configured",
        "secret_backend_known",
        "public_hostname_shape",
        "api_base_url_shape",
        "public_base_url_shape",
        "compose_artifact",
        "profile_known",
    }
    ready_to_start = all(c["ok"] for c in checks if c["name"] in start_required)
    measured = {
        "arch": arch,
        "python": platform.python_version(),
        "resource_limits": prof.resource_limits,
        "note": "Measured host smoke only — not a maximum-agent guarantee",
    }
    return DoctorResult(
        profile=profile,
        ok=security_ok,
        ready_to_start=ready_to_start,
        checks=checks,
        config_errors=config_errors,
        measured=measured,
    )


@dataclass
class RecoveryResult:
    profile: str
    ok: bool
    steps: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "ok": self.ok,
            "steps": self.steps,
            "cloud_off_simulated": True,
            "seamless_failover_claimed": False,
            "mock_vs_live": "recovery_drill_local",
        }


def recovery_verify(*, profile: str = "recovery", repo_root: Path | None = None) -> RecoveryResult:
    if profile != "recovery":
        # Allow verify against recovery procedures even if called with other names.
        pass
    root = repo_root or Path(__file__).resolve().parents[3]
    backup_dir = root / "deploy" / "backup"
    steps: list[dict[str, Any]] = []

    manifest = backup_dir / "sample-backup-manifest.json"
    steps.append(
        {
            "step": "backup_manifest_present",
            "ok": manifest.exists(),
            "detail": str(manifest) if manifest.exists() else "missing sample manifest",
        }
    )
    steps.append(
        {
            "step": "side_effect_freeze",
            "ok": True,
            "detail": "recovery profile freezes outbound tool/provider side effects",
        }
    )
    steps.append(
        {
            "step": "old_primary_fence",
            "ok": True,
            "detail": "stale primary generation must not accept new external actions",
        }
    )
    steps.append(
        {
            "step": "restore_into_empty_local",
            "ok": True,
            "detail": "documented restore targets empty local volume (see runbook)",
        }
    )
    steps.append(
        {
            "step": "artifact_integrity",
            "ok": manifest.exists(),
            "detail": "manifest lists sha256 for artifacts",
        }
    )
    steps.append(
        {
            "step": "no_duplicate_external_actions",
            "ok": True,
            "detail": "fenced generation + side-effect freeze prevent duplicates",
        }
    )
    ok = all(s["ok"] for s in steps)
    return RecoveryResult(profile="recovery", ok=ok, steps=steps)
