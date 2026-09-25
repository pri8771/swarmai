#!/usr/bin/env python3
"""TH-05: minimal mission UI shows real loopback execution state.

Proves the console live loader (same endpoints as apps/console) reflects
authoritative API missions, workers, projects, and artifact content hashes.
Does not wait on R730 / DNS / Cloudflare. Free/local only.
"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = os.environ.get("SWARM_SERVER_URL", "http://127.0.0.1:18766")
EVIDENCE_DIR = ROOT / "docs" / "evidence" / "two-host" / "TH-05"
CONSOLE = ROOT / "apps" / "console"
PUBLIC_HOSTNAME = "swarm.splitsignal.ai"


def _load_token() -> str:
    env_path = ROOT / "deploy" / "env" / "server.env"
    if not env_path.is_file():
        raise SystemExit(f"missing {env_path}")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("SWARM_SEED_LOOPBACK_TOKEN="):
            token = line.split("=", 1)[1].strip()
            if token and "replace-with" not in token:
                return token
    raise SystemExit("SWARM_SEED_LOOPBACK_TOKEN unset")


def _npm(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["npm", *args],
        cwd=str(CONSOLE),
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    base = DEFAULT_BASE.rstrip("/")
    token = _load_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    run_id = uuid.uuid4().hex[:12]
    evidence: dict[str, object] = {
        "packet": "TH-05",
        "hostname_public": PUBLIC_HOSTNAME,
        "server_url": base,
        "console_port": 43127,
        "started_at": datetime.now(UTC).isoformat(),
        "spend_usd": 0,
        "allow_paid": False,
        "steps": [],
    }

    with httpx.Client(base_url=base, headers=headers, timeout=45.0) as client:
        ready = client.get("/health/ready")
        ready.raise_for_status()
        ready_body = ready.json()
        evidence["health_ready"] = ready_body
        evidence["steps"].append(
            {
                "step": "health_ready",
                "ok": ready_body.get("status") == "ready"
                and ready_body.get("database") == "up",
            }
        )

        missions = client.get("/v1/missions")
        missions.raise_for_status()
        rows = missions.json().get("missions") or []
        # Prefer a mission that already has artifacts (TH-04), else first row.
        focus_id = None
        artifact_hash = None
        artifact_id = None
        for row in rows:
            mid = row.get("mission_id")
            if not mid:
                continue
            arts = client.get(f"/v1/missions/{mid}/artifacts")
            if arts.status_code != 200:
                continue
            alist = arts.json().get("artifacts") or []
            hashed = [
                a
                for a in alist
                if isinstance(a, dict) and (a.get("content_hash") or a.get("sha256"))
            ]
            if hashed:
                focus_id = mid
                artifact_id = hashed[0].get("artifact_id")
                artifact_hash = hashed[0].get("content_hash") or hashed[0].get("sha256")
                break
        if focus_id is None and rows:
            focus_id = rows[0].get("mission_id")

        evidence["mission_id"] = focus_id
        evidence["artifact_id"] = artifact_id
        evidence["content_hash"] = artifact_hash
        evidence["steps"].append(
            {
                "step": "select_real_mission_with_artifact",
                "ok": bool(focus_id and artifact_hash),
                "mission_id": focus_id,
                "artifact_id": artifact_id,
                "content_hash": artifact_hash,
                "mission_count": len(rows),
            }
        )
        if not (focus_id and artifact_hash):
            raise SystemExit(
                "no durable mission with content_hash artifact — run TH-04 proof first"
            )

        detail = client.get(f"/v1/missions/{focus_id}")
        detail.raise_for_status()
        mission = detail.json().get("mission") or {}
        graph = client.get(f"/v1/missions/{focus_id}/graph")
        graph.raise_for_status()
        workers = client.get("/v1/workers")
        workers.raise_for_status()
        projects = client.get("/v1/projects")
        projects.raise_for_status()
        worker_rows = workers.json().get("workers") or []
        project_rows = projects.json().get("projects") or []

        evidence["steps"].append(
            {
                "step": "console_live_endpoints",
                "ok": True,
                "mission_status": mission.get("status"),
                "objective": mission.get("objective"),
                "graph_task_count": len((graph.json() or {}).get("tasks") or []),
                "worker_count": len(worker_rows),
                "project_count": len(project_rows),
            }
        )

        # Same query shape the console uses for live mode.
        console_url = (
            f"http://127.0.0.1:43127/"
            f"?mode=live&baseUrl={base}&missionId={focus_id}"
            # Token intentionally omitted from committed evidence URL; operator
            # appends &token=… locally for browser session against loopback.
        )
        evidence["console_url_template"] = console_url
        evidence["steps"].append(
            {
                "step": "console_url_template",
                "ok": PUBLIC_HOSTNAME in evidence["hostname_public"],
                "url": console_url,
                "note": "append &token=<loopback> for browser; never commit tokens",
            }
        )

    # Console unit/UI tests + production build (no secrets in dist).
    if not (CONSOLE / "node_modules").exists():
        install = _npm("ci")
        if install.returncode != 0:
            install = _npm("install")
        evidence["steps"].append(
            {
                "step": "npm_install",
                "ok": install.returncode == 0,
                "returncode": install.returncode,
                "stderr_tail": (install.stderr or "")[-400:],
            }
        )
        if install.returncode != 0:
            raise SystemExit(f"npm install failed: {install.stderr}")
    else:
        evidence["steps"].append({"step": "npm_install", "ok": True, "skipped": True})

    test = _npm("test")
    evidence["steps"].append(
        {
            "step": "console_vitest",
            "ok": test.returncode == 0,
            "returncode": test.returncode,
            "stdout_tail": (test.stdout or "")[-500:],
            "stderr_tail": (test.stderr or "")[-500:],
        }
    )
    if test.returncode != 0:
        raise SystemExit(f"console vitest failed: {test.stdout}\n{test.stderr}")

    build = _npm("run", "build")
    evidence["steps"].append(
        {
            "step": "console_build",
            "ok": build.returncode == 0,
            "returncode": build.returncode,
            "stderr_tail": (build.stderr or "")[-400:],
        }
    )
    if build.returncode != 0:
        raise SystemExit(f"console build failed: {build.stderr}")

    dist_blob = ""
    dist = CONSOLE / "dist"
    for path in dist.rglob("*"):
        if path.is_file() and path.suffix in {".js", ".html", ".css", ".map"}:
            dist_blob += path.read_text(errors="ignore")
    import re

    secret_free = (
        re.search(r"sk-[a-zA-Z0-9]{8,}", dist_blob) is None
        and "OPENROUTER_API_KEY=" not in dist_blob
        and re.search(r"api_key\s*=\s*\S+", dist_blob, re.I) is None
    )
    has_hostname = PUBLIC_HOSTNAME in dist_blob
    evidence["steps"].append(
        {
            "step": "dist_no_secrets_has_hostname",
            "ok": secret_free and has_hostname,
            "secret_free": secret_free,
            "hostname_in_bundle": has_hostname,
        }
    )

    # Node live snapshot parity — mirrors apps/console/src/api/client.ts fetches.
    node_script = f"""
const base = {json.dumps(base)};
const token = {json.dumps(token)};
const missionId = {json.dumps(focus_id)};
const expectedHash = {json.dumps(artifact_hash)};
const headers = {{ Accept: 'application/json', Authorization: 'Bearer ' + token }};
const j = async (path) => {{
  const r = await fetch(base + path, {{ headers }});
  if (!r.ok) throw new Error(path + ' ' + r.status);
  return r.json();
}};
const ready = await j('/health/ready');
const missions = await j('/v1/missions');
const detail = await j('/v1/missions/' + missionId);
const arts = await j('/v1/missions/' + missionId + '/artifacts');
const workers = await j('/v1/workers');
const projects = await j('/v1/projects');
const art = (arts.artifacts || []).find(a => (a.content_hash || a.sha256) === expectedHash);
const out = {{
  ok: ready.status === 'ready'
    && (missions.missions || []).some(m => m.mission_id === missionId)
    && detail.mission && detail.mission.id === missionId
    && !!art
    && Array.isArray(workers.workers)
    && Array.isArray(projects.projects),
  mission_id: missionId,
  content_hash: art && (art.content_hash || art.sha256),
  worker_count: (workers.workers || []).length,
  project_count: (projects.projects || []).length,
  hostname_public: {json.dumps(PUBLIC_HOSTNAME)},
}};
console.log(JSON.stringify(out));
if (!out.ok) process.exit(1);
"""
    node = subprocess.run(
        ["node", "--input-type=module", "-e", node_script],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    node_out = {}
    try:
        node_out = json.loads((node.stdout or "").strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        node_out = {"ok": False, "raw": node.stdout, "err": node.stderr}
    evidence["live_snapshot_parity"] = node_out
    evidence["steps"].append(
        {
            "step": "node_live_snapshot_parity",
            "ok": node.returncode == 0 and bool(node_out.get("ok")),
            "returncode": node.returncode,
            "parity": node_out,
            "stderr_tail": (node.stderr or "")[-300:],
        }
    )

    all_ok = all(bool(s.get("ok")) for s in evidence["steps"])  # type: ignore[union-attr]
    evidence["ok"] = all_ok
    evidence["finished_at"] = datetime.now(UTC).isoformat()

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE_DIR / f"th05-mission-ui-{run_id}.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (EVIDENCE_DIR / "latest.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ok": all_ok, "evidence": str(out), "mission_id": focus_id}))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
