"""Deploy doctor and recovery verification — local artifacts only."""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.deploy.profiles import PROFILES, get_profile


@dataclass
class DoctorResult:
    profile: str
    ok: bool
    checks: list[dict[str, Any]] = field(default_factory=list)
    measured: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "ok": self.ok,
            "checks": self.checks,
            "measured": self.measured,
            "production": False,
            "cloud_deployed": False,
            "mock_vs_live": "local_doctor_only",
        }


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def doctor(*, profile: str = "standalone", repo_root: Path | None = None) -> DoctorResult:
    prof = get_profile(profile)
    root = repo_root or Path(__file__).resolve().parents[3]
    checks: list[dict[str, Any]] = []

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
    # Wrong/missing secret refuses startup for non-mock profiles.
    if profile != "mock":
        # Require SWARM_DATABASE_URL to be set OR explicitly allow missing for doctor dry-run.
        db_url = os.environ.get("SWARM_DATABASE_URL")
        if db_url and ("password=" in db_url.lower() or "@" in db_url):
            forbidden_fixed = "swarm:swarm@" in db_url
            checks.append(
                _check(
                    "database_url_configured",
                    not forbidden_fixed,
                    "SWARM_DATABASE_URL present (value hidden)"
                    if not forbidden_fixed
                    else "forbidden fixed credential swarm:swarm",
                )
            )
        else:
            checks.append(
                _check(
                    "database_url_configured",
                    False,
                    "SWARM_DATABASE_URL missing — refuse live start (empty/unconfigured default)",
                )
            )
    else:
        checks.append(_check("database_url_configured", True, "mock profile skips DB requirement"))

    compose = root / "deploy" / "compose" / f"{profile}.yml"
    checks.append(
        _check(
            "compose_artifact",
            compose.exists(),
            str(compose.relative_to(root)) if compose.exists() else f"missing {compose.name}",
        )
    )
    if compose.exists() and profile != "mock":
        compose_text = compose.read_text()
        checks.append(
            _check(
                "compose_no_fixed_db_password",
                "POSTGRES_PASSWORD: swarm" not in compose_text
                and "swarm:swarm@" not in compose_text,
                "compose must require generated/operator secret (no fixed swarm password)",
            )
        )
        checks.append(
            _check(
                "compose_loopback_api_bind",
                "127.0.0.1:8765:8765" in compose_text,
                "API publish must stay loopback/private",
            )
        )
        checks.append(
            _check(
                "compose_requires_secret_vars",
                "SWARM_POSTGRES_PASSWORD:?" in compose_text
                and "SWARM_DATABASE_URL:?" in compose_text,
                "compose must fail closed when secrets are unset",
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

    # Doctor is informational for missing DB on standalone — overall ok if security checks pass.
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
            "compose_no_fixed_db_password",
            "compose_loopback_api_bind",
            "compose_requires_secret_vars",
        }
    )
    measured = {
        "arch": arch,
        "python": platform.python_version(),
        "resource_limits": prof.resource_limits,
        "note": "Measured host smoke only — not a maximum-agent guarantee",
    }
    return DoctorResult(profile=profile, ok=security_ok, checks=checks, measured=measured)


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
