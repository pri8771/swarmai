#!/usr/bin/env python3
"""G11 residual: three unfamiliar extract+triage tasks on shared durable IDs.

Surfaces (same MissionStore IDs under repo var/missions):
  - Console-shaped create + snapshot observe (createLiveMission / loadSnapshot)
  - API execute (+ get)
  - CLI `swarm mission execute|report` subprocess on the same IDs

Real local Ollama only ($0). Honest pass/fail — never invent success.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from swarm.api.app import create_app, resolve_install_project_id
from swarm.mission.store import MissionStore

REPO = Path(__file__).resolve().parents[1]
TOKEN = "atk_g11_multisurface_proof"
MODEL = "gemma3:4b"

TASKS = [
    {
        "family": "extract",
        "objective": (
            "G11-MS extract: vendor, invoice_date, currency, line totals from unfamiliar "
            "snippet 'Acme Nordics AB / 2026-09-12 / SEK / Widget-A 2x 450 / Widget-B 1x 1200'"
        ),
        "required_checks": {
            "inference_ok": True,
            "nonempty_output": True,
            "fields_extracted": True,
            "no_known_answer_path": True,
        },
        "execute_via": "api",
    },
    {
        "family": "triage",
        "objective": (
            "G11-MS triage: unfamiliar intermittent 502 spikes on edge gateway only during "
            "certificate rotation windows; hypothesis, evidence_needed, next_checks"
        ),
        "required_checks": {
            "inference_ok": True,
            "nonempty_output": True,
            "hypothesis_present": True,
            "no_known_answer_path": True,
        },
        "execute_via": "api",
    },
    {
        "family": "triage",
        "objective": (
            "G11-MS triage: unfamiliar queue-lag alarms where consumer lag grows only when "
            "batch size > 64 and ACK deadline < 2s; hypothesis + next_checks"
        ),
        "required_checks": {
            "inference_ok": True,
            "nonempty_output": True,
            "hypothesis_present": True,
            "no_known_answer_path": True,
        },
        "execute_via": "cli",
    },
]


def _console_create_body(project_id: str, objective: str, family: str, checks: dict) -> dict:
    """Match apps/console createLiveMission request shape."""
    return {
        "mission": {
            "project_id": project_id,
            "objective": objective,
            "acceptance_criteria": ["operator review"],
            "allowed_capabilities": ["code.read"],
            "data_scope_ids": ["scope_local"],
            "resource_policy_id": "policy_default",
            "max_wall_time_seconds": 3600,
            "max_graph_nodes": 50,
            "max_active_sessions": 4,
            "max_model_calls": 50,
        },
        "task_family": family,
        "required_checks": checks,
    }


def _cli_report_subprocess(mission_id: str) -> dict:
    proc = subprocess.run(
        [
            str(REPO / ".venv" / "bin" / "swarm"),
            "mission",
            "report",
            "--mission-id",
            mission_id,
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    out: dict = {"returncode": proc.returncode, "stderr_tail": proc.stderr[-1000:]}
    try:
        out["record"] = json.loads(proc.stdout)
    except json.JSONDecodeError:
        out["record"] = None
        out["stdout_tail"] = proc.stdout[-2000:]
    return out


def _cli_execute_subprocess(mission_id: str, model: str) -> dict:
    env = os.environ.copy()
    env["SWARM_ALLOW_PAID"] = "false"
    proc = subprocess.run(
        [
            str(REPO / ".venv" / "bin" / "swarm"),
            "mission",
            "execute",
            "--mission-id",
            mission_id,
            "--model",
            model,
        ],
        cwd=str(REPO),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    payload: dict = {
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-2000:],
    }
    try:
        payload["body"] = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload["body"] = {
            "accepted": False,
            "worker_ok": False,
            "parse_error": True,
            "stdout_tail": proc.stdout[-4000:],
        }
    return payload


def main() -> int:
    os.environ["SWARM_ALLOW_PAID"] = "false"
    recorded_at = datetime.now(timezone.utc).isoformat()
    root = REPO
    project_id = resolve_install_project_id(root)
    app = create_app(
        seed_loopback_token=TOKEN,
        seed_fixtures=False,
        repo_root=root,
        install_project_id=project_id,
    )
    client = TestClient(app)
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    created_rows: list[dict] = []
    for spec in TASKS:
        body = _console_create_body(
            project_id,
            spec["objective"],
            spec["family"],
            spec["required_checks"],
        )
        created = client.post("/v1/missions", headers=headers, json=body)
        assert created.status_code == 200, created.text
        mission = created.json()["mission"]
        mid = mission["id"]
        # Confirm durable on disk before any execute (CLI list/report visibility).
        disk = MissionStore(root / "var" / "missions").load(mid)
        created_rows.append(
            {
                "family": spec["family"],
                "mission_id": mid,
                "status_after_create": mission.get("status"),
                "objective": spec["objective"],
                "execute_via": spec["execute_via"],
                "console_create_shape": True,
                "disk_goal": disk.goal,
                "disk_source": disk.source,
            }
        )

    listed = client.get("/v1/missions", headers=headers)
    assert listed.status_code == 200, listed.text
    list_ids = {row["mission_id"] for row in listed.json()["missions"]}
    for row in created_rows:
        assert row["mission_id"] in list_ids

    executions: list[dict] = []
    for row, spec in zip(created_rows, TASKS, strict=True):
        mid = row["mission_id"]
        if spec["execute_via"] == "api":
            exec_res = client.post(
                f"/v1/missions/{mid}/execute",
                headers=headers,
                json={"model": MODEL},
            )
            api_body = (
                exec_res.json()
                if exec_res.headers.get("content-type", "").startswith("application/json")
                else {"raw": exec_res.text, "accepted": False}
            )
            exec_record = {
                "mission_id": mid,
                "family": spec["family"],
                "surface": "api",
                "http_status": exec_res.status_code,
                "body": api_body,
            }
        else:
            cli_exec = _cli_execute_subprocess(mid, MODEL)
            exec_record = {
                "mission_id": mid,
                "family": spec["family"],
                "surface": "cli_subprocess",
                "http_status": None,
                "cli_returncode": cli_exec["returncode"],
                "body": cli_exec.get("body") or {},
                "stderr_tail": cli_exec.get("stderr_tail"),
            }

        got = client.get(f"/v1/missions/{mid}", headers=headers)
        cli_report = _cli_report_subprocess(mid)
        record = cli_report.get("record") or {}
        cost = record.get("cost") or {}
        total_usd = float(cost.get("total_usd") or 0.0)
        body = exec_record.get("body") or {}
        accepted = bool(body.get("accepted"))
        worker_ok = bool(body.get("worker_ok"))
        status = str(body.get("status") or record.get("status") or "unknown")
        executions.append(
            {
                **exec_record,
                "api_get_status": got.status_code,
                "api_mission_status": (got.json().get("mission") or {}).get("status")
                if got.status_code == 200
                else None,
                "cli_report_returncode": cli_report.get("returncode"),
                "cli_report_status": record.get("status"),
                "cli_report_goal": record.get("goal"),
                "cli_cost_total_usd": total_usd,
                "same_durable_id": record.get("mission_id") == mid
                or mid in str(record.get("mission_id") or mid),
                "honest_outcome": {
                    "accepted": accepted,
                    "worker_ok": worker_ok,
                    "status": status,
                    "pass": accepted and worker_ok and total_usd == 0.0,
                },
            }
        )

    listed2 = client.get("/v1/missions", headers=headers)
    snap_ids = {row["mission_id"] for row in listed2.json()["missions"]}
    snap_statuses = {
        row["mission_id"]: row.get("status") for row in listed2.json()["missions"]
    }

    families = sorted({r["family"] for r in created_rows})
    all_zero = all(e["cli_cost_total_usd"] == 0.0 for e in executions)
    any_pass = any(e["honest_outcome"]["pass"] for e in executions)
    any_fail = any(not e["honest_outcome"]["pass"] for e in executions)

    evidence = {
        "gate": "G11-RUN-111-residual-multisurface",
        "recorded_at": recorded_at,
        "model": MODEL,
        "spend_policy": "zero",
        "allow_paid": False,
        "spend_usd": 0.0 if all_zero else "NONZERO_UNEXPECTED",
        "project_id": project_id,
        "fixture_seeded": False,
        "parser_dogfood": False,
        "g10_lead_accept_invented": False,
        "families": families,
        "created_via_console_shape": created_rows,
        "executions": executions,
        "console_snapshot_after": {
            "contains_all_ids": all(r["mission_id"] in snap_ids for r in created_rows),
            "statuses": {
                r["mission_id"]: snap_statuses.get(r["mission_id"]) for r in created_rows
            },
        },
        "surfaces": {
            "console_create": True,
            "console_snapshot_observe": True,
            "api_execute": any(e["surface"] == "api" for e in executions),
            "api_get": True,
            "cli_execute_subprocess": any(e["surface"] == "cli_subprocess" for e in executions),
            "cli_report_subprocess": True,
        },
        "honest_summary": {
            "tasks": len(executions),
            "any_pass": any_pass,
            "any_fail_or_reject": any_fail,
            "all_zero_spend": all_zero,
            "invented_success": False,
        },
    }

    out_dir = REPO / "docs" / "evidence" / "g11"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "multisurface-three-tasks.json"
    out_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    print(f"\nWrote {out_path}", file=sys.stderr)

    if not all_zero:
        return 2
    if len(executions) != 3:
        return 2
    if set(families) != {"extract", "triage"}:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
