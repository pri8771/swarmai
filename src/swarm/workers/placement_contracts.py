"""Placement contracts — schedule by locality/capability contracts, not hostnames.

Personal machine names (``host_alias``, operator labels) are identity metadata.
Eligibility uses authorized capability grants and locality contracts only.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

# Scope tokens on tasks → required locality contract classes.
SCOPE_TO_LOCALITY: dict[str, str] = {
    "local_only": "local",
    "local": "local",
    "mac_local": "mac_local",
    "host_local": "host_local",
    "region_bound": "region_bound",
    "site_bound": "site_bound",
}


@dataclass(frozen=True)
class CapabilityContract:
    """Task requires these authorized capabilities (subset match)."""

    required: frozenset[str]

    @classmethod
    def from_task(
        cls,
        *,
        required_capabilities: Iterable[str] | None = None,
    ) -> CapabilityContract:
        return cls(required=frozenset(str(c) for c in (required_capabilities or []) if str(c)))

    def satisfied_by(self, granted: Iterable[str]) -> bool:
        have = frozenset(str(c) for c in granted)
        if not self.required:
            return True
        return self.required.issubset(have)


@dataclass(frozen=True)
class LocalityContract:
    """Task requires these authorized locality classes."""

    required: frozenset[str]

    @classmethod
    def from_scopes(cls, scopes: Iterable[str] | None = None) -> LocalityContract:
        required: set[str] = set()
        for scope in scopes or []:
            mapped = SCOPE_TO_LOCALITY.get(str(scope))
            if mapped:
                required.add(mapped)
        return cls(required=frozenset(required))

    def satisfied_by(self, authorized_classes: Iterable[str]) -> bool:
        have = frozenset(str(c) for c in authorized_classes)
        if not self.required:
            return True
        return self.required.issubset(have)


@dataclass(frozen=True)
class PlacementContract:
    """Combined capability + locality eligibility (no personal hostname keys)."""

    capabilities: CapabilityContract
    locality: LocalityContract

    @classmethod
    def for_task(
        cls,
        *,
        required_capabilities: Iterable[str] | None = None,
        scopes: Iterable[str] | None = None,
    ) -> PlacementContract:
        return cls(
            capabilities=CapabilityContract.from_task(
                required_capabilities=required_capabilities
            ),
            locality=LocalityContract.from_scopes(scopes),
        )

    def worker_eligible(
        self,
        *,
        granted_capabilities: Iterable[str],
        authorized_locality: Iterable[str],
        labels: Iterable[str] | None = None,
        host_alias: str | None = None,
    ) -> bool:
        # Labels and personal aliases are ignored for eligibility.
        _ = labels
        _ = host_alias
        if not self.capabilities.satisfied_by(granted_capabilities):
            return False
        if not self.locality.satisfied_by(authorized_locality):
            return False
        return True
