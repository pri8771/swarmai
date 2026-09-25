"""LiveGrant preflight — validate grants without inventing approvals (PC-12)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.evals.synthetic_harness import LiveGateBlocked, LiveGrant


@dataclass
class LiveGrantPreflight:
    ready: bool
    blocked_reason: str | None = None
    grant_id: str | None = None
    routes: list[str] = field(default_factory=list)
    budget_usd: float | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "blocked_reason": self.blocked_reason,
            "grant_id": self.grant_id,
            "routes": list(self.routes),
            "budget_usd": self.budget_usd,
            "notes": list(self.notes),
            "invent_grant": False,
        }


def preflight_live_grant(
    grant: LiveGrant | None,
    *,
    purpose: str | None = None,
    required_route: str | None = None,
) -> LiveGrantPreflight:
    """Check whether an existing grant may authorize live dispatch.

    Never fabricates or auto-approves a grant. Missing/invalid grants return
    ``ready=False`` with a precise blocker.
    """
    if grant is None:
        return LiveGrantPreflight(
            ready=False,
            blocked_reason="missing_live_grant",
            notes=["finish_live_path_without_spend", "do_not_invent_grant"],
        )
    notes: list[str] = []
    try:
        grant.assert_usable()
    except LiveGateBlocked as exc:
        return LiveGrantPreflight(
            ready=False,
            blocked_reason=str(exc),
            grant_id=grant.grant_id,
            routes=list(grant.routes),
            budget_usd=grant.budget_usd,
            notes=["grant_present_but_not_usable"],
        )
    if purpose and grant.purpose and purpose not in {grant.purpose, "*"}:
        # Soft note: purpose mismatch is an authorization concern.
        notes.append(f"purpose_mismatch:requested={purpose}:granted={grant.purpose}")
        return LiveGrantPreflight(
            ready=False,
            blocked_reason="live_grant_purpose_mismatch",
            grant_id=grant.grant_id,
            routes=list(grant.routes),
            budget_usd=grant.budget_usd,
            notes=notes,
        )
    if required_route and required_route not in grant.routes:
        return LiveGrantPreflight(
            ready=False,
            blocked_reason=f"live_grant_route_not_permitted:{required_route}",
            grant_id=grant.grant_id,
            routes=list(grant.routes),
            budget_usd=grant.budget_usd,
            notes=notes,
        )
    notes.append("preflight_ok_no_dispatch")
    return LiveGrantPreflight(
        ready=True,
        grant_id=grant.grant_id,
        routes=list(grant.routes),
        budget_usd=grant.budget_usd,
        notes=notes,
    )


def refuse_invented_grant(*, invent: bool) -> None:
    """Hard refuse fabricated grant approval paths."""
    if invent:
        raise LiveGateBlocked("invent_live_grant_forbidden")
