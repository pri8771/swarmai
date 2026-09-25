#!/usr/bin/env python3
"""TH-06: qualify optional OpenCode/Hermes adapters honestly on Mac loopback.

Marks unqualified capabilities unavailable. Never claims framework config alone
enforces SwarmAI contracts. Does not install Hermes, start OpenCode services,
or authorize paid/live inference. Does not wait on R730/DNS/CF.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from swarm.runtime.adapters.qualify import qualification_report  # noqa: E402

DEFAULT_BASE = os.environ.get("SWARM_SERVER_URL", "http://127.0.0.1:18766")
EVIDENCE_DIR = ROOT / "docs" / "evidence" / "two-host" / "TH-06"
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


def main() -> int:
    base = DEFAULT_BASE.rstrip("/")
    token = _load_token()
    report = qualification_report()
    evidence: dict[str, object] = {
        "packet": "TH-06",
        "hostname_public": PUBLIC_HOSTNAME,
        "server_url": base,
        "started_at": datetime.now(UTC).isoformat(),
        "spend_usd": 0,
        "allow_paid": False,
        "config_alone_enforces_swarm_contracts": False,
        "steps": [],
        "qualification": report,
    }

    # Local report honesty checks.
    summary = report["summary"]
    policy = report["policy"]
    evidence["steps"].append(
        {
            "step": "native_available_partial_not_fully_admitted",
            "ok": (
                "native" in summary["available"]
                and "native" not in policy["mission_admissible_runtimes"]
            ),
            "available": summary["available"],
            "admissible": policy["mission_admissible_runtimes"],
        }
    )
    evidence["steps"].append(
        {
            "step": "opencode_not_mission_admissible",
            "ok": "opencode" not in policy["mission_admissible_runtimes"],
            "availability": next(
                (
                    r["availability"]
                    for r in report["runtimes"]
                    if r["runtime_id"] == "opencode"
                ),
                None,
            ),
        }
    )
    evidence["steps"].append(
        {
            "step": "hermes_unavailable",
            "ok": "hermes" in summary["unavailable"]
            or "hermes" in summary["discovered_unqualified"],
            "summary": summary,
        }
    )
    evidence["steps"].append(
        {
            "step": "config_alone_never_enforces",
            "ok": report["config_alone_enforces_swarm_contracts"] is False
            and all(
                r.get("config_alone_enforces_swarm_contracts") is False
                for r in report["runtimes"]
            ),
        }
    )
    evidence["steps"].append(
        {
            "step": "optional_runtimes_kernel_mediation_unproven",
            "ok": all(
                (r["runtime_id"] == "native")
                or (r.get("kernel_mediation_proven") is False)
                for r in report["runtimes"]
            ),
        }
    )

    # API surface on loopback server (may need image rebuild if route missing).
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    with httpx.Client(base_url=base, headers=headers, timeout=30.0) as client:
        ready = client.get("/health/ready")
        ready.raise_for_status()
        evidence["steps"].append(
            {
                "step": "health_ready",
                "ok": ready.json().get("status") == "ready",
            }
        )
        rt = client.get("/v1/runtimes")
        if rt.status_code == 404:
            evidence["steps"].append(
                {
                    "step": "api_runtimes_endpoint",
                    "ok": False,
                    "status_code": 404,
                    "note": "rebuild/recreate API image to pick up GET /v1/runtimes",
                }
            )
        else:
            rt.raise_for_status()
            body = rt.json()
            evidence["api_runtimes"] = {
                "summary": body.get("summary"),
                "mission_admissible": (body.get("policy") or {}).get(
                    "mission_admissible_runtimes"
                ),
                "config_alone_enforces_swarm_contracts": body.get(
                    "config_alone_enforces_swarm_contracts"
                ),
            }
            evidence["steps"].append(
                {
                    "step": "api_runtimes_endpoint",
                    "ok": body.get("config_alone_enforces_swarm_contracts") is False
                    and "native"
                    in ((body.get("summary") or {}).get("available") or [])
                    and "native"
                    not in (
                        (body.get("policy") or {}).get("mission_admissible_runtimes") or []
                    ),
                    "status_code": rt.status_code,
                }
            )

    all_ok = all(bool(s.get("ok")) for s in evidence["steps"])  # type: ignore[union-attr]
    evidence["ok"] = all_ok
    evidence["finished_at"] = datetime.now(UTC).isoformat()
    evidence["qualification_status"] = {
        "native": "available (partial capability proof; Mac loopback)",
        "opencode": next(
            (r["availability"] for r in report["runtimes"] if r["runtime_id"] == "opencode"),
            "unknown",
        ),
        "hermes": next(
            (r["availability"] for r in report["runtimes"] if r["runtime_id"] == "hermes"),
            "unknown",
        ),
    }

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(UTC).strftime("%H%M%S")
    out = EVIDENCE_DIR / f"th06-runtime-qualification-{run_id}.json"
    payload = json.dumps(evidence, indent=2) + "\n"
    out.write_text(payload, encoding="utf-8")
    (EVIDENCE_DIR / "latest.json").write_text(payload, encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": all_ok,
                "evidence": str(out),
                "qualification_status": evidence["qualification_status"],
            }
        )
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
