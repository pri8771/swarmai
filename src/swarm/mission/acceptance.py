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


def _grade_hidden_acceptance(
    *,
    output_text: str,
    hidden: dict[str, Any],
) -> tuple[bool, dict[str, bool], list[str]]:
    """Grade model output with task-defined rules the worker never sees.

    Supported keys (all optional; at least one must be present for a useful gate):
    - must_contain_all: every substring must appear (case-insensitive)
    - must_contain_any: at least one substring must appear
    - forbid_substrings: none of these may appear
    - min_output_chars: minimum length of output_text
    - required_json_keys: if output looks like JSON object, these keys must exist
    """
    text = output_text or ""
    lowered = text.lower()
    checks: dict[str, bool] = {}
    reasons: list[str] = []

    min_chars = hidden.get("min_output_chars")
    if min_chars is not None:
        ok = len(text) >= int(min_chars)
        checks["min_output_chars"] = ok
        if not ok:
            reasons.append("hidden_failed:min_output_chars")

    must_all = hidden.get("must_contain_all") or []
    if must_all:
        ok = all(str(s).lower() in lowered for s in must_all)
        checks["must_contain_all"] = ok
        if not ok:
            reasons.append("hidden_failed:must_contain_all")

    must_any = hidden.get("must_contain_any") or []
    if must_any:
        ok = any(str(s).lower() in lowered for s in must_any)
        checks["must_contain_any"] = ok
        if not ok:
            reasons.append("hidden_failed:must_contain_any")

    forbid = hidden.get("forbid_substrings") or []
    if forbid:
        ok = not any(str(s).lower() in lowered for s in forbid)
        checks["forbid_substrings"] = ok
        if not ok:
            reasons.append("hidden_failed:forbid_substrings")

    json_keys = hidden.get("required_json_keys") or []
    if json_keys:
        parsed: dict[str, Any] | None = None
        try:
            import json

            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                candidate = json.loads(text[start : end + 1])
                if isinstance(candidate, dict):
                    parsed = candidate
        except Exception:
            parsed = None
        if parsed is None:
            checks["required_json_keys"] = False
            reasons.append("hidden_failed:required_json_keys_not_json")
        else:
            ok = all(str(k) in parsed for k in json_keys)
            checks["required_json_keys"] = ok
            if not ok:
                reasons.append("hidden_failed:required_json_keys")

    if not checks:
        reasons.append("hidden_acceptance_empty")
        return False, checks, reasons
    return all(checks.values()), checks, reasons


def review_attempt(
    *,
    produced: dict[str, Any],
    required_checks: dict[str, Any] | None = None,
    force_wrong: bool = False,
    hidden_acceptance: dict[str, Any] | None = None,
) -> ReviewDecision:
    """Independent checks control accept/reject. Wrong results cannot be accepted.

    ``required_checks`` maps check_id → expected value. ``produced`` must contain
    matching ``checks`` or top-level fields. ``force_wrong`` simulates an
    intentionally incorrect worker claim that review must reject.

    ``hidden_acceptance`` grades ``produced['output_excerpt']`` (or ``output``)
    with deterministic rules that must not be shown to the worker.
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

    if not required and not hidden_acceptance:
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

    if hidden_acceptance:
        output = str(
            produced.get("output_excerpt")
            or produced.get("output")
            or produced_checks.get("output_excerpt")
            or ""
        )
        hidden_ok, hidden_checks, hidden_reasons = _grade_hidden_acceptance(
            output_text=output, hidden=hidden_acceptance
        )
        for k, v in hidden_checks.items():
            checks[f"hidden:{k}"] = v
        reasons.extend(hidden_reasons)
        if not hidden_ok:
            all_ok = False

    if all_ok:
        reasons.append("all_independent_checks_passed")
        return ReviewDecision(accepted=True, reasons=reasons, checks=checks)
    reasons.append("wrong_result_rejected")
    return ReviewDecision(accepted=False, reasons=reasons, checks=checks)
