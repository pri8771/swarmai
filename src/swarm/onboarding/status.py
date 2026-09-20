"""Onboarding status vocabularies — keep account / adapter / route separate."""

from __future__ import annotations

from enum import StrEnum


class AccountOnboardingStatus(StrEnum):
    UNKNOWN = "unknown"
    EXISTING_UNVERIFIED = "existing_unverified"
    SIGNUP_NEEDED = "signup_needed"
    VERIFICATION_NEEDED = "verification_needed"
    CONFIGURED = "configured"
    AUTH_VERIFIED = "auth_verified"
    BLOCKED = "blocked"
    RETIRED = "retired"
    GATED_PAYMENT = "gated_payment_method"


class AdapterOnboardingStatus(StrEnum):
    NOT_IMPLEMENTED = "not_implemented"
    IMPLEMENTED = "implemented"
    OFFLINE_TESTED = "offline_tested"
    LIVE_TESTED = "live_tested"
    RETIRED = "retired"


class RouteOnboardingStatus(StrEnum):
    DISCOVERED = "discovered"
    DISABLED = "disabled"
    CANARIED = "canaried"
    PROVISIONAL = "provisional"
    QUALIFIED = "qualified"
    EXPIRED = "expired"
    QUARANTINED = "quarantined"
    UNKNOWN_COST_DENIED = "unknown_cost_denied"
    PAID_DENIED = "paid_denied"


class CatalogLayer(StrEnum):
    """Catalog vs implemented vs configured — never collapse these."""

    CATALOGED = "cataloged"
    IMPLEMENTED = "implemented"
    CONFIGURED = "configured"  # secret ref present locally
    AUTHENTICATED = "authenticated"  # live auth proven — never inferred from key presence
