"""Mock qualification runs — never invent live rankings."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.evals.plan import EvalPlan, build_plan


@dataclass
class QualCell:
    family: str
    size: str
    route_id: str | None
    sample_count: int | None
    wilson_lower: float | None
    latency_ms_p50: float | None
    error_rate: float | None
    state: str  # provisional | untested | simulated
    model_fingerprint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "size": self.size,
            "route_id": self.route_id,
            "sample_count": self.sample_count,
            "wilson_lower": self.wilson_lower,
            "latency_ms_p50": self.latency_ms_p50,
            "error_rate": self.error_rate,
            "state": self.state,
            "model_fingerprint": self.model_fingerprint,
        }


@dataclass
class QualRun:
    run_id: str
    plan_id: str
    mode: str
    purpose: str
    cells: list[QualCell] = field(default_factory=list)
    ledger_calls: int = 0
    report_hash: str | None = None
    mock_vs_live: str = "simulated_qualification_not_live"

    def to_dict(self) -> dict[str, Any]:
        body = {
            "run_id": self.run_id,
            "plan_id": self.plan_id,
            "mode": self.mode,
            "purpose": self.purpose,
            "cells": [c.to_dict() for c in self.cells],
            "ledger_calls": self.ledger_calls,
            "report_hash": self.report_hash,
            "mock_vs_live": self.mock_vs_live,
            "generated_at": utc_now().isoformat(),
            "live_routes_used": [],
            "note": "Sparse/untested cells remain null — no invented rankings",
        }
        return body


def save_plan(plan: EvalPlan, *, purpose: str, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_id = new_id("plan_")
    payload = {
        "plan_id": plan_id,
        "purpose": purpose,
        **plan.to_dict(),
    }
    path = out_dir / f"{plan_id}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def run_qualification(
    plan_path: Path,
    *,
    mode: str = "mock",
    out_dir: Path,
    routes: list[str] | None = None,
) -> QualRun:
    plan = json.loads(plan_path.read_text())
    plan_id = plan["plan_id"]
    if mode == "live":
        # Hard stop — live requires verified zero-charge routes from P15.
        raise PermissionError(
            "live_qualification_blocked: complete P15 zero-charge verification "
            "and supply eligible routes before --mode live"
        )
    routes = routes or ["rt_fake_alpha"]
    cells: list[QualCell] = []
    for cell in plan.get("cells", []):
        # Simulate only the first route lightly; leave others untested nulls.
        cells.append(
            QualCell(
                family=cell["family"],
                size=cell["size"],
                route_id=routes[0],
                sample_count=cell.get("cases"),
                wilson_lower=None,  # canary/sim insufficient for qualification
                latency_ms_p50=None,
                error_rate=None,
                state="provisional" if (cell.get("cases") or 0) >= 2 else "untested",
                model_fingerprint="fake-alpha-v1.0",
            )
        )
        # Explicit untested cell for an alternate route — nulls required.
        if len(routes) > 1:
            cells.append(
                QualCell(
                    family=cell["family"],
                    size=cell["size"],
                    route_id=routes[1],
                    sample_count=None,
                    wilson_lower=None,
                    latency_ms_p50=None,
                    error_rate=None,
                    state="untested",
                    model_fingerprint=None,
                )
            )

    run = QualRun(
        run_id=new_id("run_"),
        plan_id=plan_id,
        mode="mock",
        purpose=plan.get("purpose", "evaluation"),
        cells=cells,
        ledger_calls=sum(1 for c in cells if c.state != "untested"),
        mock_vs_live="simulated_qualification_not_live",
    )
    raw = json.dumps(run.to_dict(), sort_keys=True, default=str)
    run.report_hash = hashlib.sha256(raw.encode()).hexdigest()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{run.run_id}.json").write_text(
        json.dumps(run.to_dict(), indent=2, default=str) + "\n"
    )
    return run


def load_report(run_id: str, report_dir: Path) -> dict[str, Any]:
    path = report_dir / f"{run_id}.json"
    if not path.exists():
        raise FileNotFoundError(run_id)
    raw: object = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError("report_not_object")
    data: dict[str, Any] = raw
    if data.get("mode") == "live" and data.get("mock_vs_live", "").startswith("simulated"):
        raise ValueError("report_mode_inconsistent")
    return data


def demotion_on_fingerprint_change(
    prior: dict[str, Any], *, new_fingerprint: str
) -> dict[str, Any]:
    """Changed alias/fingerprint demotes qualified/provisional cells."""
    cells = []
    for cell in prior.get("cells", []):
        updated = dict(cell)
        if cell.get("model_fingerprint") and cell["model_fingerprint"] != new_fingerprint:
            updated["state"] = "stale_recheck_required"
            updated["wilson_lower"] = None
        cells.append(updated)
    return {
        "prior_run_id": prior.get("run_id"),
        "new_fingerprint": new_fingerprint,
        "cells": cells,
        "mock_vs_live": prior.get("mock_vs_live"),
    }


def build_and_save_starter_plan(
    *,
    dataset: Path,
    purpose: str,
    mode: str,
    out_dir: Path,
    max_cases: int = 8,
) -> dict[str, Any]:
    plan = build_plan(dataset, suite="starter", mode=mode, max_cases=max_cases)
    return save_plan(plan, purpose=purpose, out_dir=out_dir)
