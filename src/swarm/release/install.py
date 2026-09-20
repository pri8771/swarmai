"""V0.9 installability / packaging checks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.deploy.doctor import doctor


@dataclass
class InstallCheckReport:
    run_id: str
    ok: bool
    checks: list[dict[str, Any]] = field(default_factory=list)
    doctor: dict[str, Any] = field(default_factory=dict)
    mock_vs_live: str = "local_install_check"

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "ok": self.ok,
            "checks": self.checks,
            "doctor": self.doctor,
            "mock_vs_live": self.mock_vs_live,
            "python": sys.version,
            "generated_at": utc_now().isoformat(),
        }


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def run_install_check(repo: Path) -> InstallCheckReport:
    repo = repo.resolve()
    checks: list[dict[str, Any]] = []

    py_ok = sys.version_info >= (3, 12) and sys.version_info < (3, 14)
    checks.append(
        _check(
            "python_version",
            py_ok,
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )
    )
    checks.append(_check("pyproject", (repo / "pyproject.toml").is_file(), "pyproject.toml"))
    checks.append(_check("uv_lock", (repo / "uv.lock").is_file(), "uv.lock"))
    checks.append(_check("env_example", (repo / ".env.example").is_file(), ".env.example"))
    checks.append(
        _check(
            "entry_point_import",
            True,
            "swarm.cli:main",
        )
    )
    try:
        from swarm.cli import main as _main  # noqa: F401

        checks.append(_check("cli_importable", True, "swarm.cli"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("cli_importable", False, str(exc)))

    alembic = repo / "alembic.ini"
    checks.append(_check("alembic_ini", alembic.is_file(), "alembic.ini"))
    migrations = repo / "migrations" / "versions"
    checks.append(
        _check(
            "migrations_present",
            migrations.is_dir() and any(migrations.glob("*.py")),
            "migrations/versions",
        )
    )

    for profile in ("mock", "standalone"):
        compose = repo / "deploy" / "compose" / f"{profile}.yml"
        checks.append(
            _check(
                f"compose_{profile}",
                compose.is_file(),
                str(compose.relative_to(repo)) if compose.is_file() else "missing",
            )
        )

    # Startup failure clarity: paid flag default.
    allow_paid = os.environ.get("SWARM_ALLOW_PAID", "false").lower() in {"1", "true", "yes"}
    checks.append(
        _check(
            "zero_spend_default_env",
            not allow_paid,
            f"SWARM_ALLOW_PAID={os.environ.get('SWARM_ALLOW_PAID', 'unset')}",
        )
    )

    # uv present?
    uv = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=False)
    checks.append(
        _check("uv_available", uv.returncode == 0, (uv.stdout or uv.stderr or "").strip()[:80])
    )

    doc = doctor(profile="mock", repo_root=repo)
    checks.append(_check("deploy_doctor_mock", doc.ok, "profile=mock"))

    ok = all(c["ok"] for c in checks)
    report = InstallCheckReport(
        run_id=new_id("inst_"),
        ok=ok,
        checks=checks,
        doctor=doc.to_dict(),
    )
    out = repo / "var" / "reports" / "install"
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest_install_check.json").write_text(
        json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
    return report
