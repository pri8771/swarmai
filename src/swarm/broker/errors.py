"""Broker-specific errors."""

from __future__ import annotations


class BrokerError(RuntimeError):
    """Base broker error."""


class BrokerBypassError(BrokerError):
    """Raised when a model call is attempted without admission."""


class PolicyDeniedError(BrokerError):
    """Purpose, privacy, or cost policy blocked the route."""


class QuotaExhaustedError(BrokerError):
    """One or more quota buckets cannot cover the reservation."""


class UnknownChargeDeniedError(BrokerError):
    """Unknown paid exposure; execution denied before network."""


class CircuitOpenError(BrokerError):
    """Circuit breaker is open for this route/provider."""


class DuplicateSettlementError(BrokerError):
    """Settlement key already applied."""


class AmbiguousSendError(BrokerError):
    """Post-send outcome unknown; must retain and reconcile."""
