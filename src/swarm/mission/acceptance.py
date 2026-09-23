"""Generic mission acceptance — review controls outcome, not decoration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Families the current generic runtime can execute. Others must stay unsupported.
SUPPORTED_TASK_FAMILIES = frozenset(
    {"inspect", "implement", "verify", "review", "extract", "triage", "plan"}
)


@dataclass
class SupportDecision:
    supported: bool
    family: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "supported": self.supported,
            "family": self.family,
            "reason": self.reason,
        }


@dataclass
class ReviewDecision:
    accepted: bool
    reasons: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reasons": list(self.reasons),
            "checks": dict(self.checks),
        }


def classify_task_support(task_family: str) -> SupportDecision:
    family = (task_family or "").strip().lower()
    if not family:
        return SupportDecision(False, family, "missing_task_family")
    if family not in SUPPORTED_TASK_FAMILIES:
        return SupportDecision(
            False,
            family,
            f"unsupported_task_family:{family}",
        )
    return SupportDecision(True, family, "supported")


def review_attempt(
    *,
    produced: dict[str, Any],
    required_checks: dict[str, Any] | None = None,
    force_wrong: bool = False,
) -> ReviewDecision:
    """Independent checks control accept/reject. Wrong results cannot be accepted.

    ``required_checks`` maps check_id → expected value. ``produced`` must contain
    matching ``checks`` or top-level fields. ``force_wrong`` simulates an
    intentionally incorrect worker claim that review must reject.
    """
    reasons: list[str] = []
    checks: dict[str, bool] = {}
    required = required_checks or {}
    produced_checks = produced.get("checks")
    if not isinstance(produced_checks, dict):
        produced_checks = produced

    if force_wrong or produced.get("intentionally_wrong") is True:
        reasons.append("wrong_result_rejected")
        checks["wrong_result"] = False
        return ReviewDecision(accepted=False, reasons=reasons, checks=checks)

    if produced.get("unsupported") is True:
        reasons.append(str(produced.get("unsupported_reason") or "unsupported_task"))
        checks["supported"] = False
        return ReviewDecision(accepted=False, reasons=reasons, checks=checks)

    if not required:
        # No independent checks ⇒ cannot accept (review must control acceptance).
        reasons.append("no_independent_checks")
        checks["independent_review"] = False
        return ReviewDecision(accepted=False, reasons=reasons, checks=checks)

    all_ok = True
    for key, expected in required.items():
        actual = produced_checks.get(key)
        ok = actual == expected
        checks[str(key)] = ok
        if not ok:
            all_ok = False
            reasons.append(f"check_failed:{key}")

    if all_ok:
        reasons.append("all_independent_checks_passed")
        return ReviewDecision(accepted=True, reasons=reasons, checks=checks)
    reasons.append("wrong_result_rejected")
    return ReviewDecision(accepted=False, reasons=reasons, checks=checks)
