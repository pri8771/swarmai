"""Purpose, privacy, cost, and credential-scope filtering."""

from __future__ import annotations

from dataclasses import dataclass, field

from swarm.broker.errors import PolicyDeniedError, UnknownChargeDeniedError
from swarm.contracts.enums import AvailabilityStatus, BillingMode, PurposeEligibility
from swarm.contracts.provider import InferenceRequest, ProviderAccount, RouteSnapshot


@dataclass
class RoutePolicyContext:
    """Extra metadata attached to a discoverable route for admission."""

    route: RouteSnapshot
    account: ProviderAccount | None = None
    qualified: bool = False
    qualification_rationale: str = "unassessed"
    privacy_ok: bool = True
    deprecated: bool = False
    billing_mode: BillingMode = BillingMode.UNKNOWN
    purpose_eligibility: PurposeEligibility = PurposeEligibility.UNKNOWN
    charge_verified_free: bool = False
    shared_upstream_group: str | None = None
    tags: set[str] = field(default_factory=set)


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    blocked_dimension: str | None = None


class AdmissionPolicy:
    """Admission order step 1: purpose / privacy / cost / availability."""

    def __init__(
        self,
        *,
        allow_paid: bool = False,
        allow_unknown_billing: bool = False,
        require_privacy_ref_for_production: bool = True,
    ) -> None:
        self.allow_paid = allow_paid
        self.allow_unknown_billing = allow_unknown_billing
        self.require_privacy_ref_for_production = require_privacy_ref_for_production

    def evaluate(self, request: InferenceRequest, ctx: RoutePolicyContext) -> PolicyDecision:
        route = ctx.route
        if ctx.deprecated or route.availability_status == AvailabilityStatus.RETIRED:
            return PolicyDecision(False, "model_deprecated", "availability")
        if route.availability_status in {
            AvailabilityStatus.DISABLED,
            AvailabilityStatus.UNAVAILABLE,
        }:
            return PolicyDecision(False, "route_unavailable", "availability")

        purpose = request.purpose
        eligibility = ctx.purpose_eligibility
        if purpose in {"production", "mission"} and eligibility not in {
            PurposeEligibility.PRODUCTION,
            PurposeEligibility.INTERNAL,
            PurposeEligibility.PROTOTYPE,
        }:
            # Unknown purpose eligibility is not production-qualified.
            if eligibility == PurposeEligibility.UNKNOWN:
                return PolicyDecision(False, "purpose_unknown", "purpose")

        if (
            purpose == "production"
            and self.require_privacy_ref_for_production
            and not route.privacy_policy_ref
            and not ctx.privacy_ok
        ):
            return PolicyDecision(False, "privacy_policy_missing", "privacy")

        billing = ctx.billing_mode
        if billing == BillingMode.PAID and not self.allow_paid:
            return PolicyDecision(False, "spending_denied_before_network", "cost")
        if billing == BillingMode.UNKNOWN and not self.allow_unknown_billing:
            if not (ctx.charge_verified_free and purpose in {"probe", "benchmark", "catalog"}):
                return PolicyDecision(False, "unknown_charge_exposure", "cost")

        if not ctx.qualified and purpose not in {"probe", "benchmark", "catalog", "planning"}:
            return PolicyDecision(False, "not_qualified", "qualification")

        return PolicyDecision(True, "eligible")

    def assert_allowed(self, request: InferenceRequest, ctx: RoutePolicyContext) -> None:
        decision = self.evaluate(request, ctx)
        if decision.allowed:
            return
        if decision.reason in {"unknown_charge_exposure", "spending_denied_before_network"}:
            raise UnknownChargeDeniedError(decision.reason)
        raise PolicyDeniedError(decision.reason)
