#!/usr/bin/env python3
"""V2.0 acceptance campaign: freeze verify + gate-separated harness run.

Does not mark versions accepted. Does not invent LiveGrant or spend.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from swarm.acceptance.freeze import load_freeze  # noqa: E402
from swarm.acceptance.harness import run_acceptance_campaign  # noqa: E402
from swarm.acceptance.matrix import build_version_matrices  # noqa: E402

EVIDENCE_DIR = ROOT / "docs" / "evidence" / "v20"
PUBLIC_HOSTNAME = "swarm.splitsignal.ai"


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC).isoformat()
    freeze = load_freeze()
    assert freeze.public_hostname == PUBLIC_HOSTNAME

    freeze_out = {
        "packet": "V20-ACCEPTANCE-FREEZE",
        "started_at": started,
        "freeze": freeze.to_dict(),
        "version_claim_policy": freeze.version_claim_policy,
        "spend_policy": freeze.spend_policy,
        "any_version_accepted": False,
    }
    (EVIDENCE_DIR / "acceptance_campaign_freeze.json").write_text(
        json.dumps(freeze_out, indent=2, default=str) + "\n", encoding="utf-8"
    )

    report = run_acceptance_campaign(
        freeze=freeze,
        out_dir=EVIDENCE_DIR / "acceptance_campaign_runs",
        host_qualified=False,
        elapsed_window_started=False,
        live_grant=None,
    )
    matrices = build_version_matrices(freeze=freeze, campaign=report)
    (EVIDENCE_DIR / "acceptance_version_matrices.json").write_text(
        json.dumps(matrices, indent=2, default=str) + "\n", encoding="utf-8"
    )

    summary = {
        "packet": "V20-ACCEPTANCE-CAMPAIGN",
        "started_at": started,
        "finished_at": datetime.now(UTC).isoformat(),
        "freeze_id": freeze.freeze_id,
        "freeze_hash": freeze.content_hash,
        "run_id": report.run_id,
        "report_hash": report.report_hash,
        "spend_usd": report.spend_usd,
        "any_version_accepted": False,
        "gate_summary": report.gate_summary,
        "scenario_statuses": {r.scenario_id: r.status for r in report.results},
        "version_readiness": {
            ver: row["readiness"] for ver, row in matrices["versions"].items()
        },
        "public_hostname": PUBLIC_HOSTNAME,
        "note": report.note,
    }
    (EVIDENCE_DIR / "acceptance_campaign_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))
    # Harness failures (ok=False) fail the script; blocked gates do not.
    if any(not r.ok for r in report.results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
