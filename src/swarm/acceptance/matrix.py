"""Version acceptance matrices for V1.7–V2.0 (never auto-accepted)."""

from __future__ import annotations

from typing import Any

from swarm.acceptance.freeze import AcceptanceFreeze, load_freeze
from swarm.acceptance.harness import CampaignReport, ScenarioResult


def _cell_for_scenario(
    scenario_id: str,
    results_by_id: dict[str, ScenarioResult],
) -> dict[str, Any]:
    result = results_by_id.get(scenario_id)
    if result is None:
        return {
            "scenario_id": scenario_id,
            "status": "not_run",
            "ok": None,
            "evidence_gate": None,
            "version_accepted_contribution": False,
        }
    return {
        "scenario_id": scenario_id,
        "status": result.status,
        "ok": result.ok,
        "evidence_gate": result.primary_gate,
        "version_accepted_contribution": False,
        "detail_status": result.status,
    }


def build_version_matrices(
    *,
    freeze: AcceptanceFreeze | None = None,
    campaign: CampaignReport | None = None,
) -> dict[str, Any]:
    """Build V1.7–V2.0 matrices from freeze (+ optional campaign results).

    Every version cell has ``accepted: false``. Harness output cannot flip it.
    """
    catalog = freeze or load_freeze()
    results_by_id: dict[str, ScenarioResult] = {}
    if campaign is not None:
        results_by_id = {r.scenario_id: r for r in campaign.results}

    versions: dict[str, Any] = {}
    for ver, meta in catalog.version_matrices.items():
        required = list(meta.get("required_scenarios") or [])
        cells = [_cell_for_scenario(sid, results_by_id) for sid in required]
        statuses = {c["status"] for c in cells}
        # Summarize readiness without accepting.
        if any(c["status"] == "fail" for c in cells):
            readiness = "has_failures"
        elif statuses <= {"not_run"}:
            readiness = "not_run"
        elif all(
            c["status"]
            in {
                "pass_deterministic",
                "pass_deterministic_gate_only",
                "scaffold_ready_not_integrated",
                "blocked_live_grant",
                "blocked_host_gate",
                "blocked_elapsed_window",
                "not_run",
            }
            for c in cells
        ):
            if any(str(c["status"]).startswith("blocked_") for c in cells):
                readiness = "harness_ready_external_gates_blocked"
            elif any(c["status"] == "scaffold_ready_not_integrated" for c in cells):
                readiness = "harness_ready_scaffolds_pending_integration"
            else:
                readiness = "harness_deterministic_portion_green"
        else:
            readiness = "mixed"

        versions[ver] = {
            "title": meta.get("title"),
            "accepted": False,
            "readiness": readiness,
            "required_scenarios": required,
            "cells": cells,
            "policy": "code_existing_neq_version_accepted",
        }

    return {
        "schema_version": "2.0.0",
        "freeze_id": catalog.freeze_id,
        "freeze_hash": catalog.content_hash,
        "public_hostname": catalog.public_hostname,
        "any_version_accepted": False,
        "gates": {
            "deterministic": "local mechanics / fake upstreams",
            "live": "approved LiveGrant only — never invented",
            "host": "R730/two-host/DNS — external",
            "elapsed": "wall-clock windows — never simulated",
        },
        "versions": versions,
        "campaign_run_id": campaign.run_id if campaign else None,
        "note": (
            "Matrices report harness/evidence readiness only. "
            "Independent review + operator acceptance remain separate."
        ),
    }
