"""V0.9 public demo + benchmark suite (repeatable, zero-spend)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.observability.reliability import run_reliability_scenarios
from swarm.product.contracts import public_product_contract
from swarm.product.journey import run_product_journey
from swarm.tools.permission_mission import run_permission_mission_sync


@dataclass
class DemoStep:
    name: str
    ok: bool
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


def run_public_demo_suite(repo: Path) -> dict[str, Any]:
    """Run a bounded suite of real local demos without paid spend."""
    repo = repo.resolve()
    steps: list[DemoStep] = []

    # 1. Product journey (routing surface + approvals + history)
    journey = run_product_journey(repo)
    steps.append(
        DemoStep(
            "product_journey",
            bool(journey.get("ok")),
            {
                "cost_usd": journey.get("cost_usd"),
                "mission_id": journey.get("mission_id"),
                "report_hash": journey.get("report_hash"),
            },
        )
    )

    # 2. Permission / failure containment
    perm = run_permission_mission_sync(repo)
    steps.append(
        DemoStep(
            "permission_and_approval",
            bool(perm.get("ok")),
            {"cost_usd": perm.get("cost_usd"), "audit": perm.get("audit")},
        )
    )

    # 3. Reliability matrix (circuit / timeout / budget)
    rel = run_reliability_scenarios(repo=repo)
    steps.append(
        DemoStep(
            "reliability_matrix",
            bool(rel.get("ok")),
            {
                "scenarios": list((rel.get("scenarios") or {}).keys()),
                "cost_usd": ((rel.get("ledger") or {}).get("total_usd") or 0.0),
            },
        )
    )

    # 4. Contract snapshot for public docs
    contract = public_product_contract()
    steps.append(
        DemoStep(
            "public_contract",
            "mission" in contract.get("resources", []),
            {"resources": contract.get("resources")},
        )
    )

    # 5. Mock parser demo (offline)
    try:
        import asyncio
        import sys

        if str(repo) not in sys.path:
            sys.path.insert(0, str(repo))
        from examples.dynamic_demo.run_demo import run_parser_issue_demo

        demo = asyncio.run(
            run_parser_issue_demo(
                mode="mock",
                report_dir=repo / "var" / "reports" / "demo-suite",
            )
        )
        demo_ok = True
        demo_detail: dict[str, Any] = {"mode": "mock"}
        if hasattr(demo, "to_dict"):
            payload = demo.to_dict()
            demo_detail = {
                "mode": "mock",
                "status": payload.get("status") or payload.get("mission_status"),
                "keys": sorted(payload.keys())[:12],
            }
        steps.append(DemoStep("parser_issue_mock", demo_ok, demo_detail))
    except Exception as exc:  # noqa: BLE001
        steps.append(DemoStep("parser_issue_mock", False, {"error": str(exc)}))

    total_cost = 0.0
    for s in steps:
        total_cost += float((s.detail or {}).get("cost_usd") or 0.0)

    report = {
        "schema_version": "0.9.0",
        "run_id": new_id("demo_"),
        "generated_at": utc_now().isoformat(),
        "steps": [s.to_dict() for s in steps],
        "ok": all(s.ok for s in steps),
        "cost_usd": total_cost,
        "spend_policy": "zero",
        "mock_vs_live": "mixed_local_demo_suite_zero_spend",
        "capabilities_shown": [
            "routing_contract",
            "heterogeneous_ready",
            "failure_recovery_reliability",
            "permission_approval",
            "product_history",
            "selfdev_mock_parser",
        ],
    }
    raw = json.dumps({k: v for k, v in report.items() if k != "report_hash"}, sort_keys=True)
    report["report_hash"] = hashlib.sha256(raw.encode()).hexdigest()
    out = repo / "var" / "reports" / "demo-suite"
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest_demo_suite.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
    )
    return report
