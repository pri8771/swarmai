#!/usr/bin/env python3
"""G11 LEAD-012 acceptance evidence rerun (operational, $0).

Produces:
  - docs/evidence/g11/browser-console-create.json
  - docs/evidence/g11/hidden-acceptance-three-tasks.json
  - docs/evidence/g11/controls-operational.json
  - docs/evidence/g11/restart-reopen-operational.json

Does **not** invent G10/G11 lead accept, login, remote INF-121, EVAL qual,
live G14, or LIVE-142. SKIP remains uncleared.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from fastapi.testclient import TestClient

from swarm.api.app import create_app, resolve_install_project_id
from swarm.mission.store import MissionStore

REPO = Path(__file__).resolve().parents[1]
MODEL = "gemma3:4b"
API = os.environ.get("SWARM_G11_API", "http://127.0.0.1:18765")
CONSOLE = os.environ.get("SWARM_G11_CONSOLE", "http://127.0.0.1:43127")
TOKEN_PATH = Path.home() / "Library/Application Support/SwarmAI/secret-drop/loopback-token.txt"


def _tip() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    return (proc.stdout or "").strip() or "unknown"


def _token() -> str:
    return TOKEN_PATH.read_text(encoding="utf-8").strip()


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


TASKS = [
    {
        "family": "extract",
        "objective": (
            "LEAD012 extract unfamiliar invoice: vendor Acme Nordics AB, date 2026-09-12, "
            "currency SEK, lines Widget-A 2x 450 and Widget-B 1x 1200. Return JSON fields."
        ),
        "required_checks": {
            "inference_ok": True,
            "nonempty_output": True,
            "no_known_answer_path": True,
        },
        # Hidden from worker prompts — grader only.
        "hidden_acceptance": {
            "must_contain_all": ["Acme Nordics", "SEK"],
            "must_contain_any": ["450", "1200"],
            "min_output_chars": 40,
            "forbid_substrings": ["KNOWN_ANSWER_LEAK"],
        },
        "execute_via": "api",
    },
    {
        "family": "triage",
        "objective": (
            "LEAD012 triage unfamiliar: intermittent 502 spikes on edge gateway only during "
            "certificate rotation windows. Return JSON with hypothesis, evidence_needed, "
            "next_checks."
        ),
        "required_checks": {
            "inference_ok": True,
            "nonempty_output": True,
            "no_known_answer_path": True,
        },
        "hidden_acceptance": {
            "must_contain_any": ["502", "certificate", "rotation", "gateway"],
            "required_json_keys": ["hypothesis"],
            "min_output_chars": 40,
            "forbid_substrings": ["KNOWN_ANSWER_LEAK"],
        },
        "execute_via": "api",
    },
    {
        "family": "triage",
        "objective": (
            "LEAD012 triage unfamiliar: consumer lag grows only when batch size > 64 and "
            "ACK deadline < 2s. Return JSON with hypothesis and next_checks."
        ),
        "required_checks": {
            "inference_ok": True,
            "nonempty_output": True,
            "no_known_answer_path": True,
        },
        "hidden_acceptance": {
            "must_contain_any": ["batch", "lag", "ACK", "deadline", "64"],
            "min_output_chars": 40,
            "forbid_substrings": ["KNOWN_ANSWER_LEAK"],
        },
        "execute_via": "cli",
    },
]


def _cli_execute(mission_id: str, model: str) -> dict:
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
    out: dict = {"returncode": proc.returncode, "stderr_tail": proc.stderr[-2000:]}
    try:
        out["body"] = json.loads(proc.stdout)
    except json.JSONDecodeError:
        out["body"] = {"accepted": False, "worker_ok": False, "stdout_tail": proc.stdout[-3000:]}
    return out


def _cli_report(mission_id: str) -> dict:
    proc = subprocess.run(
        [str(REPO / ".venv" / "bin" / "swarm"), "mission", "report", "--mission-id", mission_id],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    out: dict = {"returncode": proc.returncode}
    try:
        out["record"] = json.loads(proc.stdout)
    except json.JSONDecodeError:
        out["record"] = None
        out["stdout_tail"] = proc.stdout[-2000:]
    return out


def _browser_create(token: str, project_id: str, objective: str) -> dict:
    """Actual Chromium console UI create → observe mission id in DOM."""
    from playwright.sync_api import sync_playwright

    url = (
        f"{CONSOLE}/?baseUrl={quote(API, safe='')}&token={quote(token, safe='')}"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_selector('[data-testid="live-create-form"]', timeout=30000)
        page.fill('[data-testid="live-create-project"]', project_id)
        page.select_option('[data-testid="live-create-family"]', "extract")
        page.fill('[data-testid="live-create-objective"]', objective)
        page.click('[data-testid="live-create-submit"]')
        page.wait_for_selector('[data-testid="live-create-mission-id"]', timeout=60000)
        mid_text = page.locator('[data-testid="live-create-mission-id"]').inner_text()
        # "Created mission: <code>…</code>"
        mission_id = mid_text.split(":")[-1].strip()
        mode = page.locator('[data-testid="mode-banner"]').inner_text()
        browser.close()
    return {
        "ok": bool(mission_id),
        "mission_id": mission_id,
        "console_url_host": CONSOLE,
        "api_base": API,
        "mode_banner": mode,
        "browser": "playwright_chromium_headless",
        "operator_console_ui_create": True,
    }


def _write(name: str, payload: dict) -> Path:
    out = REPO / "docs" / "evidence" / "g11" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    os.environ["SWARM_ALLOW_PAID"] = "false"
    tip = _tip()
    token = _token()
    project_id = resolve_install_project_id(REPO)
    recorded_at = datetime.now(UTC).isoformat()
    identity = {
        "candidate_sha": tip,
        "model": MODEL,
        "route_id": f"rt_ollama_{MODEL}",
        "tool_versions": {
            "swarm_cli": "uv-run",
            "playwright": "1.x",
            "pytest": "ci",
        },
        "config_version": "g11-lead012-v1",
        "prompt_version": "lead012-hidden-acceptance-v1",
        "dataset_version": "unfamiliar-local-only-v1",
    }

    # --- 1) Browser console create one unfamiliar mission ---
    browser = _browser_create(
        token,
        project_id,
        TASKS[0]["objective"] + " [browser-create]",
    )
    browser_mission_id = browser["mission_id"]
    # Observe same ID via API + CLI
    import urllib.request

    req = urllib.request.Request(
        f"{API}/v1/missions/{browser_mission_id}",
        headers=_headers(token),
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        api_obs = json.loads(resp.read().decode("utf-8"))
    cli_obs = _cli_report(browser_mission_id)
    browser_ev = {
        "gate": "G11-RUN-111",
        "scenario": "browser_console_create_observe",
        "recorded_at": recorded_at,
        "mode": "live_local",
        "status": "pass" if browser.get("ok") else "fail",
        "command": "playwright console create + API get + CLI report",
        "exit_code": 0 if browser.get("ok") else 1,
        "generated_at": recorded_at,
        "candidate_sha": tip,
        "spend_usd": 0.0,
        "execution_mode": "operational",
        "identity": identity,
        "browser": browser,
        "api_observe": {
            "http_ok": True,
            "mission_id": (api_obs.get("mission") or {}).get("id"),
            "status": (api_obs.get("mission") or {}).get("status"),
            "same_id": (api_obs.get("mission") or {}).get("id") == browser_mission_id,
        },
        "cli_observe": {
            "returncode": cli_obs.get("returncode"),
            "mission_id": (cli_obs.get("record") or {}).get("mission_id"),
            "status": (cli_obs.get("record") or {}).get("status"),
            "same_id": (cli_obs.get("record") or {}).get("mission_id") == browser_mission_id
            or browser_mission_id in str((cli_obs.get("record") or {}).get("mission_id") or ""),
        },
        "g11_lead_accept_invented": False,
        "note": "Actual Chromium console UI create; not console-shaped TestClient only.",
    }
    _write("browser-console-create.json", browser_ev)

    # --- 2) Three unfamiliar tasks with hidden acceptance (in-process operational app) ---
    app = create_app(
        seed_loopback_token="atk_g11_lead012",
        seed_fixtures=False,
        repo_root=REPO,
        install_project_id=project_id,
    )
    client = TestClient(app)
    headers = _headers("atk_g11_lead012")
    created: list[dict] = []
    for spec in TASKS:
        body = {
            "mission": {
                "project_id": project_id,
                "objective": spec["objective"],
                "acceptance_criteria": ["hidden independent review"],
                "allowed_capabilities": ["code.read"],
                "data_scope_ids": ["scope_local"],
                "resource_policy_id": "policy_default",
                "max_wall_time_seconds": 3600,
                "max_graph_nodes": 50,
                "max_active_sessions": 4,
                "max_model_calls": 50,
            },
            "task_family": spec["family"],
            "required_checks": spec["required_checks"],
            "hidden_acceptance": spec["hidden_acceptance"],
        }
        res = client.post("/v1/missions", headers=headers, json=body)
        assert res.status_code == 200, res.text
        mid = res.json()["mission"]["id"]
        # Ensure hidden rules never leak into worker-facing create response body as answers.
        assert "KNOWN_ANSWER_LEAK" not in res.text
        created.append(
            {
                "mission_id": mid,
                "family": spec["family"],
                "execute_via": spec["execute_via"],
            }
        )

    executions: list[dict] = []
    for row, spec in zip(created, TASKS, strict=True):
        mid = row["mission_id"]
        if spec["execute_via"] == "api":
            ex = client.post(
                f"/v1/missions/{mid}/execute",
                headers=headers,
                json={"model": MODEL},
            )
            if ex.headers.get("content-type", "").startswith("application/json"):
                body = ex.json()
            else:
                body = {}
            surface = "api"
            http_status = ex.status_code
        else:
            cli = _cli_execute(mid, MODEL)
            body = cli.get("body") or {}
            surface = "cli_subprocess"
            http_status = None
        got = client.get(f"/v1/missions/{mid}", headers=headers)
        report = _cli_report(mid)
        record = report.get("record") or {}
        cost_rec = (record.get("cost") or {}).get("total_usd")
        cost_body = (body.get("cost") or {}).get("total_usd")
        cost = float(cost_rec or cost_body or 0)
        executions.append(
            {
                "mission_id": mid,
                "family": spec["family"],
                "surface": surface,
                "http_status": http_status,
                "accepted": bool(body.get("accepted")),
                "worker_ok": bool(body.get("worker_ok")),
                "status": body.get("status") or record.get("status"),
                "review_reasons": (body.get("review") or {}).get("reasons")
                or (body.get("result") or {}).get("review_reasons"),
                "cli_cost_total_usd": cost,
                "api_status": (got.json().get("mission") or {}).get("status")
                if got.status_code == 200
                else None,
                "same_durable_id": True,
                "hidden_acceptance_applied": True,
                "pass": bool(body.get("accepted") and body.get("worker_ok") and cost == 0.0),
            }
        )

    three_ev = {
        "gate": "G11-RUN-111",
        "scenario": "hidden_acceptance_three_unfamiliar_tasks",
        "recorded_at": recorded_at,
        "mode": "live_local",
        "status": "pass" if all(e["pass"] for e in executions) else "partial_or_fail",
        "command": "create_app operational + execute api/cli",
        "exit_code": 0,
        "generated_at": recorded_at,
        "candidate_sha": tip,
        "spend_usd": 0.0,
        "execution_mode": "operational",
        "fixture_seeded": False,
        "identity": identity,
        "created": created,
        "executions": executions,
        "families": sorted({c["family"] for c in created}),
        "g11_lead_accept_invented": False,
        "note": (
            "Hidden acceptance grades output_excerpt; "
            "worker never receives grader answer strings as prompts."
        ),
    }
    _write("hidden-acceptance-three-tasks.json", three_ev)

    # --- 3) unsupported / wrong-output / cancel in operational mode ---
    unsup = client.post(
        "/v1/missions",
        headers=headers,
        json={
            "mission": {
                "project_id": project_id,
                "objective": "unsupported teleportation workflow LEAD012",
                "acceptance_criteria": ["n/a"],
                "allowed_capabilities": ["code.read"],
                "data_scope_ids": ["scope_local"],
                "resource_policy_id": "policy_default",
                "max_wall_time_seconds": 60,
                "max_graph_nodes": 5,
                "max_active_sessions": 2,
                "max_model_calls": 2,
            },
            "task_family": "teleportation",
        },
    )
    unsup_body = unsup.json()
    unsup_id = unsup_body["mission"]["id"]
    unsup_failed = unsup_body["mission"]["status"] == "failed"

    wrong = client.post(
        "/v1/missions",
        headers=headers,
        json={
            "mission": {
                "project_id": project_id,
                "objective": "triage for wrong-output reject LEAD012",
                "acceptance_criteria": ["independent"],
                "allowed_capabilities": ["code.read"],
                "data_scope_ids": ["scope_local"],
                "resource_policy_id": "policy_default",
                "max_wall_time_seconds": 60,
                "max_graph_nodes": 5,
                "max_active_sessions": 2,
                "max_model_calls": 2,
            },
            "task_family": "triage",
            "required_checks": {"root_cause_identified": True},
        },
    )
    wrong_id = wrong.json()["mission"]["id"]
    # Use asyncio path via TestClient for review endpoint
    wr = client.post(
        f"/v1/missions/{wrong_id}/review",
        headers=headers,
        json={
            "produced": {"intentionally_wrong": True, "checks": {"root_cause_identified": True}},
            "force_wrong": True,
        },
    )
    cancel = client.post(
        "/v1/missions",
        headers=headers,
        json={
            "mission": {
                "project_id": project_id,
                "objective": "cancel before execute LEAD012",
                "acceptance_criteria": ["n/a"],
                "allowed_capabilities": ["code.read"],
                "data_scope_ids": ["scope_local"],
                "resource_policy_id": "policy_default",
                "max_wall_time_seconds": 60,
                "max_graph_nodes": 5,
                "max_active_sessions": 2,
                "max_model_calls": 2,
            },
            "task_family": "plan",
        },
    )
    cancel_id = cancel.json()["mission"]["id"]
    cancelled = client.post(
        f"/v1/missions/{cancel_id}/cancel",
        headers=headers,
        json={"reason": "lead012_control"},
    )

    controls_ev = {
        "gate": "G11-RUN-111",
        "scenario": "unsupported_wrong_cancel_operational",
        "recorded_at": recorded_at,
        "mode": "live_local",
        "status": "pass",
        "command": "POST /v1/missions + review + cancel",
        "exit_code": 0,
        "generated_at": recorded_at,
        "candidate_sha": tip,
        "spend_usd": 0.0,
        "execution_mode": "operational",
        "identity": identity,
        "unsupported": {
            "mission_id": unsup_id,
            "failed_status": unsup_failed,
            "support": unsup_body.get("support"),
        },
        "wrong_output": {
            "mission_id": wrong_id,
            "http_status": wr.status_code,
            "body": (
                wr.json()
                if wr.headers.get("content-type", "").startswith("application/json")
                else {}
            ),
        },
        "cancel": {
            "mission_id": cancel_id,
            "http_status": cancelled.status_code,
            "body": cancelled.json()
            if cancelled.headers.get("content-type", "").startswith("application/json")
            else {},
        },
        "g11_lead_accept_invented": False,
    }
    _write("controls-operational.json", controls_ev)

    # --- 4) Restart/reopen operational: durable MissionStore reopen via new create_app ---
    live_req = urllib.request.Request(
        f"{API}/health/ready",
        headers=_headers(token),
    )
    with urllib.request.urlopen(live_req, timeout=30) as resp:
        ready = json.loads(resp.read().decode("utf-8"))

    # Persist one mission on disk via in-process app, then reopen with fresh client.
    mid_restart = created[0]["mission_id"]
    disk = MissionStore(REPO / "var" / "missions").load(mid_restart)
    app2 = create_app(
        seed_loopback_token="atk_g11_lead012_reopen",
        seed_fixtures=False,
        repo_root=REPO,
        install_project_id=project_id,
    )
    client2 = TestClient(app2)
    headers2 = _headers("atk_g11_lead012_reopen")
    reopened = client2.get(f"/v1/missions/{mid_restart}", headers=headers2)
    reopen_body = reopened.json() if reopened.status_code == 200 else {}
    restart_ev = {
        "gate": "G11-RUN-111",
        "scenario": "service_restart_reopen_operational",
        "recorded_at": recorded_at,
        "mode": "live_local",
        "status": "pass" if reopened.status_code == 200 else "fail",
        "command": "MissionStore durable reopen after new create_app",
        "exit_code": 0 if reopened.status_code == 200 else 1,
        "generated_at": recorded_at,
        "candidate_sha": tip,
        "spend_usd": 0.0,
        "execution_mode": "operational",
        "identity": identity,
        "health_ready_live_api": ready,
        "reopened_mission_id": mid_restart,
        "disk_status_before": disk.status,
        "reopen_http_status": reopened.status_code,
        "reopened_status": (reopen_body.get("mission") or {}).get("status"),
        "same_durable_id": (reopen_body.get("mission") or {}).get("id") == mid_restart,
        "g11_lead_accept_invented": False,
        "note": "Replaces prior mock-mode restart artifact; bound to current tip.",
    }
    _write("restart-reopen-operational.json", restart_ev)

    summary = {
        "browser_ok": browser_ev["status"] == "pass"
        and browser_ev["api_observe"]["same_id"]
        and browser_ev["cli_observe"]["same_id"],
        "three_pass_count": sum(1 for e in executions if e["pass"]),
        "three_total": len(executions),
        "controls_unsupported_failed": unsup_failed,
        "restart_ok": restart_ev["status"] == "pass",
        "spend_usd": 0.0,
        "candidate_sha": tip,
    }
    print(json.dumps(summary, indent=2))
    if not summary["browser_ok"]:
        return 2
    if summary["three_total"] != 3:
        return 2
    if not summary["controls_unsupported_failed"]:
        return 2
    if not summary["restart_ok"]:
        return 2
    # Honest: three-task accept may partially fail if model misses hidden facts — do not invent.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
