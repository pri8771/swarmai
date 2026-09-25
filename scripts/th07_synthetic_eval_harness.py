#!/usr/bin/env python3
"""TH-07: synthetic evaluation harness proof (no live grants required).

Prepares and runs the graded starter suite with sealed answers, calibration vs
holdout summaries, budget/provenance, and a blocked live gate. Does not wait on
R730/DNS/CF, does not call providers, and does not auto-change production routing.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from swarm.contracts.workspace import EvalResult  # noqa: E402
from swarm.evals.profiles import ProfileStore  # noqa: E402
from swarm.evals.synthetic_harness import (  # noqa: E402
    LiveGateBlocked,
    LiveGrant,
    prepare_harness_manifest,
    run_synthetic_harness,
)

EVIDENCE_DIR = ROOT / "docs" / "evidence" / "two-host" / "TH-07"
DATASET = ROOT / "benchmarks" / "starter.jsonl"
PUBLIC_HOSTNAME = "swarm.splitsignal.ai"


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC).isoformat()
    steps: list[dict[str, object]] = []

    manifest = prepare_harness_manifest(
        dataset_path=DATASET, public_hostname=PUBLIC_HOSTNAME
    )
    steps.append(
        {
            "step": "prepare_manifest",
            "ok": manifest["prepared_independently_of_live_grants"] is True,
            "case_count": manifest["coverage"]["case_count"],
            "live_gate_default": manifest["live_gate_default"],
        }
    )

    # Production store must remain untouched.
    prod = ProfileStore()
    prod.record_result(
        EvalResult(
            distinct_case_id="seed_a",
            split="holdout",
            route_fingerprint="rt_prod_seed",
            model_fingerprint="m_seed",
            exact_prompt_hash="h",
            outcome="pass",
            grader_version="1",
            correctness=True,
        ),
        task_family="extraction",
        size_band="S",
    )
    prod.record_result(
        EvalResult(
            distinct_case_id="seed_b",
            split="holdout",
            route_fingerprint="rt_prod_seed",
            model_fingerprint="m_seed",
            exact_prompt_hash="h",
            outcome="pass",
            grader_version="1",
            correctness=True,
        ),
        task_family="extraction",
        size_band="S",
    )
    before_keys = set(prod.profiles.keys())

    report = run_synthetic_harness(
        dataset_path=DATASET,
        mode="oracle",
        out_dir=EVIDENCE_DIR,
        public_hostname=PUBLIC_HOSTNAME,
        production_profile_store=prod,
        repeats=1,
    )
    steps.append(
        {
            "step": "oracle_full_suite",
            "ok": report.passed == 128 and report.failed == 0,
            "passed": report.passed,
            "failed": report.failed,
            "report_hash": report.report_hash,
            "difficulties": report.provenance.get("difficulties_covered"),
            "families": report.provenance.get("families_covered"),
        }
    )
    steps.append(
        {
            "step": "holdout_vs_calibration",
            "ok": all(s.passed == 64 for s in report.split_summaries),
            "summaries": [s.to_dict() for s in report.split_summaries],
        }
    )
    steps.append(
        {
            "step": "no_production_routing_mutation",
            "ok": (
                set(prod.profiles.keys()) == before_keys
                and report.routing_mutation["production_profiles_mutated"] is False
                and report.routing_mutation["auto_production_routing_changes"] is False
            ),
            "routing_mutation": report.routing_mutation,
        }
    )

    fail_report = run_synthetic_harness(
        dataset_path=DATASET,
        mode="fixture_fail",
        max_cases=8,
        public_hostname=PUBLIC_HOSTNAME,
    )
    steps.append(
        {
            "step": "fixture_fail_negative_control",
            "ok": fail_report.passed == 0 and fail_report.failed == 8,
            "passed": fail_report.passed,
            "failed": fail_report.failed,
        }
    )

    live_blocked = False
    live_detail = ""
    try:
        run_synthetic_harness(dataset_path=DATASET, mode="live", max_cases=1)
    except LiveGateBlocked as exc:
        live_blocked = True
        live_detail = str(exc)
    steps.append(
        {
            "step": "live_gate_blocked_without_grant",
            "ok": live_blocked and "live_qualification_blocked" in live_detail,
            "detail": live_detail,
        }
    )

    grant_dispatch_blocked = False
    grant_detail = ""
    try:
        run_synthetic_harness(
            dataset_path=DATASET,
            mode="live",
            max_cases=1,
            live_grant=LiveGrant(
                grant_id="th07_probe",
                routes=("rt_probe",),
                budget_usd=1.0,
                purpose="th07_probe",
                approved=True,
            ),
        )
    except LiveGateBlocked as exc:
        grant_dispatch_blocked = True
        grant_detail = str(exc)
    steps.append(
        {
            "step": "live_dispatch_not_enabled_even_with_grant",
            "ok": grant_dispatch_blocked,
            "detail": grant_detail,
        }
    )

    steps.append(
        {
            "step": "hostname",
            "ok": report.public_hostname == PUBLIC_HOSTNAME,
            "hostname": report.public_hostname,
        }
    )

    all_ok = all(bool(s.get("ok")) for s in steps)
    evidence = {
        "packet": "TH-07",
        "hostname_public": PUBLIC_HOSTNAME,
        "started_at": started,
        "finished_at": datetime.now(UTC).isoformat(),
        "spend_usd": 0,
        "allow_paid": False,
        "prepared_independently_of_live_grants": True,
        "auto_production_routing_changes": False,
        "r730_dns_cf_required": False,
        "manifest": manifest,
        "oracle_report_id": report.run_id,
        "oracle_report_hash": report.report_hash,
        "budget": report.budget,
        "provenance": report.provenance,
        "live_gate": report.live_gate,
        "routing_mutation": report.routing_mutation,
        "split_summaries": [s.to_dict() for s in report.split_summaries],
        "steps": steps,
        "ok": all_ok,
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = EVIDENCE_DIR / f"th07-synthetic-harness-{stamp}.json"
    out.write_text(json.dumps(evidence, indent=2, default=str) + "\n", encoding="utf-8")
    (EVIDENCE_DIR / "proof-latest.json").write_text(
        json.dumps(evidence, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (EVIDENCE_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8"
    )

    print(json.dumps({"ok": all_ok, "evidence": str(out), "steps": steps}, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
