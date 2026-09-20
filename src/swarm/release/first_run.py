"""V1.0 first-run stable UX — guided setup checks with clear failures."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.deploy.doctor import doctor
from swarm.product.projects import ProjectStore
from swarm.release.install import run_install_check


@dataclass
class FirstRunReport:
    run_id: str
    ok: bool
    steps: list[dict[str, Any]] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    project_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "ok": self.ok,
            "steps": self.steps,
            "next_actions": self.next_actions,
            "project_id": self.project_id,
            "generated_at": utc_now().isoformat(),
            "mock_vs_live": "first_run_local",
            "spend_policy": "zero" if os.environ.get("SWARM_ALLOW_PAID", "false").lower()
            not in {"1", "true", "yes"} else "paid_enabled",
        }


def _step(name: str, ok: bool, detail: str, *, fix: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"name": name, "ok": ok, "detail": detail}
    if not ok and fix:
        row["fix"] = fix
    return row


def run_first_run(repo: Path, *, project_name: str = "Local workspace") -> FirstRunReport:
    """Guide a fresh user through install → project → ready-to-mission."""
    repo = repo.resolve()
    steps: list[dict[str, Any]] = []
    next_actions: list[str] = []

    py_ok = sys.version_info >= (3, 12) and sys.version_info < (3, 14)
    steps.append(
        _step(
            "python",
            py_ok,
            f"{sys.version_info.major}.{sys.version_info.minor}",
            fix="Install Python 3.12 (and <3.14), then re-run `uv sync`",
        )
    )

    env_example = (repo / ".env.example").is_file()
    steps.append(
        _step(
            "env_example",
            env_example,
            "present" if env_example else "missing",
            fix="Restore `.env.example` from the repository",
        )
    )
    if not (repo / ".env").exists():
        next_actions.append("cp .env.example .env  # optional for mock mode")

    allow_paid = os.environ.get("SWARM_ALLOW_PAID", "false").lower() in {"1", "true", "yes"}
    steps.append(
        _step(
            "zero_spend_default",
            not allow_paid,
            f"SWARM_ALLOW_PAID={os.environ.get('SWARM_ALLOW_PAID', 'unset')}",
            fix="Export SWARM_ALLOW_PAID=false for first-run dogfood",
        )
    )

    inst = run_install_check(repo)
    steps.append(
        _step(
            "install_check",
            inst.ok,
            f"checks={len(inst.checks)}",
            fix="Run `uv run swarm release install-check` and fix failing checks",
        )
    )

    doc = doctor(profile="mock", repo_root=repo)
    steps.append(
        _step(
            "deploy_doctor_mock",
            doc.ok,
            "mock profile",
            fix="Inspect `swarm deploy doctor --profile mock`",
        )
    )

    projects = ProjectStore(repo / "var" / "projects")
    existing = projects.list_projects()
    if any(p.get("project_id") == "proj_demo" for p in existing):
        cfg = projects.get("proj_demo")
        steps.append(_step("project", True, f"reused {cfg.project_id}"))
        project_id = cfg.project_id
    else:
        cfg = projects.create(
            name=project_name,
            repo_path=repo,
            project_id="proj_demo",
        )
        steps.append(_step("project", True, f"created {cfg.project_id}"))
        project_id = cfg.project_id

    next_actions.extend(
        [
            "uv run swarm mission plan --goal \"Inspect the sandbox parser helper\"",
            "uv run swarm product journey",
            "uv run swarm release demo-suite",
            "npm --prefix apps/console install && npm --prefix apps/console run dev",
        ]
    )

    ok = all(s["ok"] for s in steps)
    report = FirstRunReport(
        run_id=new_id("firstrun_"),
        ok=ok,
        steps=steps,
        next_actions=next_actions,
        project_id=project_id,
    )
    out = repo / "var" / "reports" / "v1"
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest_first_run.json").write_text(
        json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
    return report
