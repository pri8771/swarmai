#!/usr/bin/env python3
"""V2.3 acceptance campaign: frozen deterministic probes plus honest external-gate status.

Never marks a version accepted, never invents a LiveGrant, never spends.
Writes ``docs/evidence/v23/acceptance_campaign.json``. Exit 0 only when every
deterministic probe passes; external gates are reported, not required.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from swarm.acceptance.v23_probes import run_v23_probes  # noqa: E402
from swarm.pursuit.native_loop import native_loop_from_env  # noqa: E402
from swarm.release.candidate import CURRENT_SCHEMA_REVISION  # noqa: E402

EVIDENCE = ROOT / "docs" / "evidence" / "v23" / "acceptance_campaign.json"
COMPOSE_SMOKE = ROOT / "docs" / "evidence" / "v20" / "compose-smoke" / "latest.json"


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _compose_status() -> str:
    if not COMPOSE_SMOKE.is_file():
        return "not_run"
    try:
        return str(json.loads(COMPOSE_SMOKE.read_text(encoding="utf-8")).get("status", "unknown"))
    except (OSError, json.JSONDecodeError):
        return "unreadable"


def _live_router_status() -> str:
    loop, reason = native_loop_from_env({}, grant=None)
    return "configured_but_not_run" if loop is not None else f"blocked:{reason}"


def main() -> int:
    os.chdir(ROOT)
    started = datetime.now(UTC).isoformat()
    with tempfile.TemporaryDirectory(prefix="v23_campaign_") as tmp:
        report = run_v23_probes(Path(tmp))
    deterministic_ok = report["deterministic_passed"] == report["deterministic_total"]
    summary = {
        "packet": "V23-ACCEPTANCE-CAMPAIGN",
        "started_at": started,
        "finished_at": datetime.now(UTC).isoformat(),
        "source_sha": _git_sha(),
        "schema_revision": CURRENT_SCHEMA_REVISION,
        "freeze_id": report["freeze_id"],
        "policy_version": report["policy_version"],
        "gates": {
            "deterministic": "pass" if deterministic_ok else "fail",
            "multi_process_private": "pending_owner_approval",
            "live_router_free_route": _live_router_status(),
            "compose_smoke_v20_e10": _compose_status(),
            "durable_postgres_flag": os.environ.get("SWARM_V23_DURABLE", "") == "1",
        },
        "deterministic_passed": report["deterministic_passed"],
        "deterministic_total": report["deterministic_total"],
        "results": [
            {k: r[k] for k in ("id", "probe", "gate", "ok", "status")} for r in report["results"]
        ],
        "pending": report["pending"],
        "version_claim": report["version_claim"],
        "any_version_accepted": False,
        "spend_usd": 0.0,
        "spend_basis": "no provider calls; probes are in-process fakes",
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("gates", "deterministic_passed", "version_claim")}))
    return 0 if deterministic_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
