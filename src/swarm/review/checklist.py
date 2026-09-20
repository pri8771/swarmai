"""Independent review checklist — evidence-backed, not aspirational."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from swarm.contracts.common import utc_now

Severity = Literal["critical", "high", "medium", "low", "info"]
Readiness = Literal[
    "software_ready_offline",
    "accounts_unprovisioned",
    "deploy_unprovisioned",
    "live_unverified",
]


@dataclass
class Finding:
    finding_id: str
    severity: Severity
    title: str
    owner: str
    evidence_id: str
    status: str  # open | mitigated | blocked_live | accepted_risk
    reproduction: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "severity": self.severity,
            "title": self.title,
            "owner": self.owner,
            "evidence_id": self.evidence_id,
            "status": self.status,
            "reproduction": self.reproduction,
            "notes": self.notes,
        }


@dataclass
class ChecklistItem:
    item_id: str
    claim: str
    evidence_id: str | None
    result: str  # pass | fail | skip_live | n_a
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "claim": self.claim,
            "evidence_id": self.evidence_id,
            "result": self.result,
            "notes": self.notes,
        }


@dataclass
class ReviewReport:
    review_id: str
    readiness: list[Readiness] = field(default_factory=list)
    checklist: list[ChecklistItem] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    live_blockers: list[str] = field(default_factory=list)
    mock_vs_live: str = "review_offline_evidence_only"
    release_blocked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "readiness": self.readiness,
            "checklist": [c.to_dict() for c in self.checklist],
            "findings": [f.to_dict() for f in self.findings],
            "live_blockers": self.live_blockers,
            "mock_vs_live": self.mock_vs_live,
            "release_blocked": self.release_blocked,
            "critical_or_high_open": [
                f.finding_id
                for f in self.findings
                if f.severity in {"critical", "high"} and f.status == "open"
            ],
            "generated_at": utc_now().isoformat(),
        }


def build_offline_review() -> ReviewReport:
    """Line-by-line review against offline evidence. Live claims stay skip_live."""
    checklist = [
        ChecklistItem(
            "C01",
            "Providers claimed supported match catalogued adapters",
            "EV-catalog",
            "pass",
            "cataloged ≠ authenticated",
        ),
        ChecklistItem(
            "C02",
            "No duplicate quota origins summed into one capacity number",
            "EV-broker-buckets",
            "pass",
        ),
        ChecklistItem(
            "C03",
            "No hidden retries/embeddings/judges bypass broker",
            "EV-broker-invocations",
            "pass",
        ),
        ChecklistItem(
            "C04",
            "No-spend enforcement for unknown billing / canaries",
            "EV-onboarding-canary",
            "pass",
            "live zero-charge still unproven",
        ),
        ChecklistItem(
            "C05",
            "Task-size profiles do not invent rankings from canaries",
            "EV-qualify-nulls",
            "pass",
        ),
        ChecklistItem(
            "C06",
            "Graph invariants: cycles rejected, duplicates merged",
            "EV-controller-graph",
            "pass",
        ),
        ChecklistItem(
            "C07",
            "Context isolation / scoped workspace",
            "EV-workspace",
            "pass",
        ),
        ChecklistItem(
            "C08",
            "Worker authority: stale generation cannot overwrite",
            "EV-worker-stale",
            "pass",
        ),
        ChecklistItem(
            "C09",
            "Recovery fencing / deploy doctor local",
            "EV-deploy-recovery",
            "pass",
        ),
        ChecklistItem(
            "C10",
            "P15/P16 live canary + qualification evidence",
            None,
            "skip_live",
            "keys/accounts unavailable",
        ),
        ChecklistItem(
            "C11",
            "No paid Conductor / subscription-to-API bypass required",
            "EV-license-inventory",
            "pass",
            "self-hosted open stack for mock path",
        ),
        ChecklistItem(
            "C12",
            "Self-dev cannot expand approval/secret/release rights",
            "EV-selfdev-policy",
            "pass",
        ),
    ]
    findings = [
        Finding(
            "F-LIVE-01",
            "high",
            "Live provider accounts not provisioned",
            "operator",
            "EV-live-block",
            "blocked_live",
            "Attempt P15 canary without keys → refused; record user action for keys",
            "Does not block offline RC labeling",
        ),
        Finding(
            "F-REG-01",
            "medium",
            "Regression pack must keep detecting injected double-settle",
            "broker-owner",
            "EV-reg-double-settle",
            "mitigated",
            "tests/regressions/test_accounting_permission.py",
        ),
    ]
    open_blocking = [
        f
        for f in findings
        if f.severity in {"critical", "high"} and f.status == "open"
    ]
    return ReviewReport(
        review_id="review_offline_p20",
        readiness=[
            "software_ready_offline",
            "accounts_unprovisioned",
            "deploy_unprovisioned",
            "live_unverified",
        ],
        checklist=checklist,
        findings=findings,
        live_blockers=[
            "Provider API keys for zero-charge P15/P16",
            "Cloud/deploy provision not authorized",
        ],
        release_blocked=len(open_blocking) > 0,
    )
