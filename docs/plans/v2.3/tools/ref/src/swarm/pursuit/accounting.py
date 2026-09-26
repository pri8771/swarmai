"""Goal-scoped usage and budget accounting (PC-06).

Tracks holds and settlements against a goal resource envelope. Unknown usage
stays unknown — never invent refunds or LiveGrant approvals. Paid spend is
denied under a zero ceiling.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from swarm.contracts.common import new_id, utc_now


class AccountingError(PermissionError):
    """Raised for envelope violations or double-settle attempts."""


HoldState = Literal["held", "settled", "released", "unknown"]


@dataclass
class UsageAmounts:
    spend_usd: float = 0.0
    model_calls: int = 0
    tool_calls: int = 0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    route_id: str | None = None
    runtime: str | None = None
    usage_unknown: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "spend_usd": self.spend_usd,
            "model_calls": self.model_calls,
            "tool_calls": self.tool_calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "route_id": self.route_id,
            "runtime": self.runtime,
            "usage_unknown": self.usage_unknown,
        }


@dataclass
class ResourceHold:
    hold_id: str
    goal_id: str
    mission_id: str
    reserved: UsageAmounts
    state: HoldState = "held"
    settled: UsageAmounts | None = None
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "hold_id": self.hold_id,
            "goal_id": self.goal_id,
            "mission_id": self.mission_id,
            "reserved": self.reserved.to_dict(),
            "state": self.state,
            "settled": self.settled.to_dict() if self.settled else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class GoalResourceLedger:
    """Parent-goal ledger: child missions reserve from remaining envelope."""

    goal_id: str
    spend_usd_ceiling: float = 0.0
    max_model_calls: int = 100
    max_tool_calls: int = 400
    allow_paid: bool = False
    holds: dict[str, ResourceHold] = field(default_factory=dict)
    on_change: Callable[[ResourceHold], None] | None = field(
        default=None, repr=False, compare=False
    )

    def _commit(self, hold: ResourceHold, prior: ResourceHold | None) -> ResourceHold:
        """Persist first (when durable); on failure restore the prior in-memory state."""
        if self.on_change is not None:
            try:
                self.on_change(hold)
            except Exception:
                if prior is None:
                    self.holds.pop(hold.hold_id, None)
                else:
                    self.holds[hold.hold_id] = prior
                raise
        self.holds[hold.hold_id] = hold
        return hold

    @classmethod
    def from_envelope(cls, goal_id: str, envelope: dict[str, Any] | None) -> GoalResourceLedger:
        env = dict(envelope or {})
        ceiling = float(env.get("spend_usd_ceiling", env.get("max_spend_usd", 0.0)) or 0.0)
        if ceiling < 0:
            ceiling = 0.0
        return cls(
            goal_id=goal_id,
            spend_usd_ceiling=ceiling,
            max_model_calls=int(env.get("max_model_calls", env.get("model_calls", 100)) or 100),
            max_tool_calls=int(env.get("max_tool_calls", env.get("tool_calls", 400)) or 400),
            allow_paid=bool(env.get("allow_paid", False)),
        )

    def _held_totals(self) -> UsageAmounts:
        """Budget still committed: open holds plus unknown-outcome holds.

        An ``unknown`` hold keeps the larger of its reservation and its reported
        usage committed until reconciled; unknown usage is never treated as zero.
        """
        spend = 0.0
        models = 0
        tools = 0
        for hold in self.holds.values():
            if hold.state == "held":
                spend += hold.reserved.spend_usd
                models += hold.reserved.model_calls
                tools += hold.reserved.tool_calls
            elif hold.state == "unknown":
                reported = hold.settled or UsageAmounts()
                spend += max(hold.reserved.spend_usd, reported.spend_usd)
                models += max(hold.reserved.model_calls, reported.model_calls)
                tools += max(hold.reserved.tool_calls, reported.tool_calls)
        return UsageAmounts(spend_usd=spend, model_calls=models, tool_calls=tools)

    def _settled_totals(self) -> UsageAmounts:
        spend = 0.0
        models = 0
        tools = 0
        unknown = False
        for hold in self.holds.values():
            if hold.state == "unknown":
                unknown = True
                continue
            if hold.state != "settled" or hold.settled is None:
                continue
            if hold.settled.usage_unknown:
                unknown = True
                continue
            spend += hold.settled.spend_usd
            models += hold.settled.model_calls
            tools += hold.settled.tool_calls
        return UsageAmounts(
            spend_usd=spend, model_calls=models, tool_calls=tools, usage_unknown=unknown
        )

    def remaining(self) -> UsageAmounts:
        held = self._held_totals()
        settled = self._settled_totals()
        return UsageAmounts(
            spend_usd=max(0.0, self.spend_usd_ceiling - held.spend_usd - settled.spend_usd),
            model_calls=max(0, self.max_model_calls - held.model_calls - settled.model_calls),
            tool_calls=max(0, self.max_tool_calls - held.tool_calls - settled.tool_calls),
            usage_unknown=settled.usage_unknown,
        )

    def reserve(
        self,
        *,
        mission_id: str,
        spend_usd: float = 0.0,
        model_calls: int = 0,
        tool_calls: int = 0,
        route_id: str | None = None,
        runtime: str | None = None,
    ) -> ResourceHold:
        spend = max(0.0, float(spend_usd))
        models = max(0, int(model_calls))
        tools = max(0, int(tool_calls))
        if spend > 0 and not self.allow_paid and self.spend_usd_ceiling <= 0:
            raise AccountingError("paid_cost_denied_under_zero_spend_budget")
        rem = self.remaining()
        if spend > rem.spend_usd + 1e-9:
            raise AccountingError("insufficient_spend_budget")
        if models > rem.model_calls:
            raise AccountingError("insufficient_model_call_budget")
        if tools > rem.tool_calls:
            raise AccountingError("insufficient_tool_call_budget")
        hold = ResourceHold(
            hold_id=new_id("hold_"),
            goal_id=self.goal_id,
            mission_id=mission_id,
            reserved=UsageAmounts(
                spend_usd=spend,
                model_calls=models,
                tool_calls=tools,
                route_id=route_id,
                runtime=runtime,
            ),
        )
        return self._commit(hold, None)

    def settle(
        self,
        hold_id: str,
        *,
        spend_usd: float = 0.0,
        model_calls: int = 0,
        tool_calls: int = 0,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        route_id: str | None = None,
        runtime: str | None = None,
        usage_unknown: bool = False,
    ) -> ResourceHold:
        hold = self.holds.get(hold_id)
        if hold is None:
            raise AccountingError(f"unknown_hold:{hold_id}")
        if hold.state == "settled":
            raise AccountingError(f"double_settle:{hold_id}")
        if hold.state == "released":
            raise AccountingError(f"settle_after_release:{hold_id}")
        if hold.state == "unknown":
            # Preserve unknown — do not invent a refund or clearance.
            raise AccountingError(f"unknown_hold_requires_reconciliation:{hold_id}")

        prior = copy.deepcopy(hold)
        spend = max(0.0, float(spend_usd))
        # Unknown usage is recorded without authorizing payment or inventing a refund.
        if usage_unknown:
            hold.state = "unknown"
            hold.settled = UsageAmounts(
                spend_usd=spend,
                model_calls=max(0, int(model_calls)),
                tool_calls=max(0, int(tool_calls)),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                route_id=route_id or hold.reserved.route_id,
                runtime=runtime or hold.reserved.runtime,
                usage_unknown=True,
            )
            hold.updated_at = utc_now().isoformat()
            return self._commit(hold, prior)

        if spend > 0 and not self.allow_paid and self.spend_usd_ceiling <= 0:
            raise AccountingError("paid_cost_denied_under_zero_spend_budget")
        # Cannot settle more spend than reserved + remaining (no silent expansion).
        rem = self.remaining()
        # Current hold is still "held", so rem already excludes it; allow up to reserved+rem.
        max_spend = hold.reserved.spend_usd + rem.spend_usd
        if spend > max_spend + 1e-9:
            raise AccountingError("settle_exceeds_envelope")

        hold.state = "settled"
        hold.settled = UsageAmounts(
            spend_usd=spend,
            model_calls=max(0, int(model_calls)),
            tool_calls=max(0, int(tool_calls)),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            route_id=route_id or hold.reserved.route_id,
            runtime=runtime or hold.reserved.runtime,
            usage_unknown=False,
        )
        hold.updated_at = utc_now().isoformat()
        return self._commit(hold, prior)

    def release(self, hold_id: str) -> ResourceHold:
        hold = self.holds.get(hold_id)
        if hold is None:
            raise AccountingError(f"unknown_hold:{hold_id}")
        if hold.state == "settled":
            raise AccountingError(f"release_after_settle:{hold_id}")
        if hold.state == "unknown":
            raise AccountingError(f"unknown_hold_requires_reconciliation:{hold_id}")
        if hold.state == "released":
            return hold
        prior = copy.deepcopy(hold)
        hold.state = "released"
        hold.updated_at = utc_now().isoformat()
        return self._commit(hold, prior)

    def reconcile_unknown(
        self,
        hold_id: str,
        *,
        spend_usd: float,
        model_calls: int,
        tool_calls: int,
        evidence_ref: str,
    ) -> ResourceHold:
        """Operator/provider reconciliation of an unknown hold to known usage."""
        hold = self.holds.get(hold_id)
        if hold is None:
            raise AccountingError(f"unknown_hold:{hold_id}")
        if hold.state != "unknown":
            raise AccountingError(f"reconcile_requires_unknown:{hold_id}")
        if not evidence_ref:
            raise AccountingError("reconcile_requires_evidence_ref")
        before = copy.deepcopy(hold)
        prior = hold.settled or UsageAmounts()
        hold.state = "settled"
        hold.settled = UsageAmounts(
            spend_usd=max(0.0, float(spend_usd)),
            model_calls=max(0, int(model_calls)),
            tool_calls=max(0, int(tool_calls)),
            prompt_tokens=prior.prompt_tokens,
            completion_tokens=prior.completion_tokens,
            route_id=prior.route_id or hold.reserved.route_id,
            runtime=prior.runtime or hold.reserved.runtime,
            usage_unknown=False,
        )
        hold.updated_at = utc_now().isoformat()
        return self._commit(hold, before)

    def snapshot(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "spend_usd_ceiling": self.spend_usd_ceiling,
            "max_model_calls": self.max_model_calls,
            "max_tool_calls": self.max_tool_calls,
            "allow_paid": self.allow_paid,
            "remaining": self.remaining().to_dict(),
            "held": self._held_totals().to_dict(),
            "settled": self._settled_totals().to_dict(),
            "holds": [h.to_dict() for h in self.holds.values()],
        }
