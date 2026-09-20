"""Qualification runs — mock by default; live only on P15-passed routes."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.envfile import load_repo_dotenv
from swarm.evals.plan import EvalPlan, build_plan
from swarm.onboarding.canary import LOCAL_ZERO_COST_PROVIDERS, load_canary_evidence


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
    live_routes_used: list[str] = field(default_factory=list)
    note: str = "Sparse/untested cells remain null — no invented rankings"

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
            "live_routes_used": list(self.live_routes_used),
            "note": self.note,
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


def _assert_live_routes_eligible(routes: list[str]) -> list[dict[str, Any]]:
    """Require P15 canary evidence for each live route; keep cloud blocked."""
    evidence_rows: list[dict[str, Any]] = []
    for route_id in routes:
        evidence = load_canary_evidence(route_id)
        if evidence is None:
            raise PermissionError(
                "live_qualification_blocked: missing P15 canary evidence for "
                f"{route_id}; run providers canary --mode live --billing-known-zero first"
            )
        if evidence.get("denied") or evidence.get("mock_vs_live") != "live_local_zero_cost":
            raise PermissionError(
                f"live_qualification_blocked: route {route_id} did not pass "
                "zero-spend local P15 canary"
            )
        provider = evidence.get("provider_id")
        if provider not in LOCAL_ZERO_COST_PROVIDERS:
            raise PermissionError(
                f"live_qualification_blocked: provider {provider!r} is not "
                "known-zero under spend=zero"
            )
        evidence_rows.append(evidence)
    return evidence_rows


def _live_probe_latency_ms(route_id: str, model_id: str) -> float | None:
    """One bounded live chat for latency observation — no ranking invention."""
    import asyncio
    import os
    from datetime import timedelta

    from swarm.contracts.enums import ReservationPhase, SettlementState
    from swarm.contracts.provider import InferenceRequest, Reservation
    from swarm.providers.catalog import DEFAULT_ENDPOINTS
    from swarm.providers.core.adapters import OllamaAdapter

    load_repo_dotenv(Path(__file__).resolve().parents[3])
    base_url = (os.environ.get("OLLAMA_BASE_URL") or DEFAULT_ENDPOINTS["ollama"]).rstrip(
        "/"
    )

    async def _probe() -> float | None:
        adapter = OllamaAdapter(
            mode="live",
            enabled=True,
            base_url=base_url,
            secret_ref_names=[],
            account_id="pa_local_ollama",
        )
        adapter.default_model = model_id
        adapter._routes.clear()
        adapter._seed_default_route()
        seeded = next(iter(adapter._routes.values()))
        adapter._routes.pop(seeded.route_id, None)
        seeded.route_id = route_id
        seeded.model_id = model_id
        adapter._routes[route_id] = seeded
        request = InferenceRequest(
            project_id="proj_qualify",
            attempt_id="att_qualify_live",
            route_id=route_id,
            purpose="evaluation",
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            estimated_input_tokens=16,
            max_output_tokens=8,
            secret_ref_names=[],
        )
        ticket = Reservation(
            logical_call_id="lc_qualify_live",
            attempt_id=request.attempt_id,
            route_id=route_id,
            expires_at=utc_now() + timedelta(minutes=2),
            phase=ReservationPhase.RESERVED,
        )
        started = time.perf_counter()
        receipt = await adapter.execute_one(request, ticket)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if receipt.error_class is not None:
            return None
        if receipt.settlement_state != SettlementState.SETTLED:
            return None
        return elapsed_ms

    return asyncio.run(_probe())


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
        if not routes:
            raise PermissionError(
                "live_qualification_blocked: complete P15 zero-charge verification "
                "and supply eligible routes before --mode live"
            )
        evidence_rows = _assert_live_routes_eligible(routes)
        primary = routes[0]
        primary_evidence = evidence_rows[0]
        fingerprint = str(
            primary_evidence.get("model_fingerprint")
            or primary_evidence.get("model_id")
            or "unknown"
        )
        latency = _live_probe_latency_ms(
            primary, str(primary_evidence.get("model_id") or "gemma3:4b")
        )
        cells: list[QualCell] = []
        for cell in plan.get("cells", []):
            # Live canary/probe is insufficient for qualification rankings.
            cells.append(
                QualCell(
                    family=cell["family"],
                    size=cell["size"],
                    route_id=primary,
                    sample_count=1 if latency is not None else None,
                    wilson_lower=None,
                    latency_ms_p50=latency,
                    error_rate=0.0 if latency is not None else None,
                    state="provisional" if latency is not None else "untested",
                    model_fingerprint=fingerprint if latency is not None else None,
                )
            )
            # Untested cells for any additional live-eligible routes stay null.
            for extra in routes[1:]:
                cells.append(
                    QualCell(
                        family=cell["family"],
                        size=cell["size"],
                        route_id=extra,
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
            mode="live",
            purpose=plan.get("purpose", "evaluation"),
            cells=cells,
            ledger_calls=sum(1 for c in cells if c.state != "untested"),
            mock_vs_live="live_local_zero_cost_partial",
            live_routes_used=[primary] if latency is not None else [],
            note=(
                "Sparse/untested cells remain null — no invented rankings; "
                "live probe observes latency/fingerprint only"
            ),
        )
        raw = json.dumps(run.to_dict(), sort_keys=True, default=str)
        run.report_hash = hashlib.sha256(raw.encode()).hexdigest()
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{run.run_id}.json").write_text(
            json.dumps(run.to_dict(), indent=2, default=str) + "\n"
        )
        return run

    routes = routes or ["rt_fake_alpha"]
    cells = []
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
