"""Capability authority — labels alone never grant access.

Self-reported capability lists and labels are *claims*. Only capabilities that
survive authorization become ``verified_capabilities`` on
:class:`~swarm.product.portable_config.WorkerIdentitySpec`. Scheduling uses
``WorkerIdentitySpec.effective_capabilities()`` (declared ∩ verified).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from swarm.product.portable_config import WorkerIdentitySpec

# Baseline capabilities the control plane may grant without a per-project policy.
# Not a support claim for every OS; just the portable default allowlist.
DEFAULT_AUTHORIZED_CAPABILITIES: frozenset[str] = frozenset(
    {
        "chat",
        "tools",
        "extract",
        "code.read",
        "code.write",
        "review",
        "summarize",
        "planning",
        "reasoning",
        "mac.local.extract",  # optional adapter; still requires locality grant
    }
)


@dataclass(frozen=True)
class AuthorizationResult:
    claimed: tuple[str, ...]
    granted: tuple[str, ...]
    verified: bool
    rejected: tuple[str, ...] = ()

    def as_lists(self) -> tuple[list[str], list[str]]:
        return list(self.claimed), list(self.granted)


@dataclass
class CapabilityAuthority:
    """Authorize requested capabilities against project (or default) grants.

    Labels are accepted for diagnostics but never unioned into the grant set.
    """

    default_grants: frozenset[str] = DEFAULT_AUTHORIZED_CAPABILITIES
    project_grants: dict[str, frozenset[str]] = field(default_factory=dict)
    # When True and no project grant exists, grant nothing (strict). Default False
    # keeps tests/dev usable via default_grants.
    strict_without_project_grant: bool = False

    def set_project_grants(self, project_id: str, capabilities: Iterable[str]) -> None:
        self.project_grants[project_id] = frozenset(str(c) for c in capabilities)

    def authorize(
        self,
        *,
        project_id: str,
        requested: Iterable[str],
        labels: Iterable[str] | None = None,
    ) -> AuthorizationResult:
        _ = labels  # Explicitly unused — labels never authorize.
        claimed = tuple(sorted({str(c) for c in requested if str(c).strip()}))
        if project_id in self.project_grants:
            allow = self.project_grants[project_id]
            verified = True
        elif self.strict_without_project_grant:
            allow = frozenset()
            verified = True
        else:
            allow = self.default_grants
            verified = False  # default allowlist — not project-verified
        granted = tuple(sorted(set(claimed) & set(allow)))
        rejected = tuple(sorted(set(claimed) - set(granted)))
        return AuthorizationResult(
            claimed=claimed,
            granted=granted,
            verified=verified,
            rejected=rejected,
        )

    def apply_to_identity(self, identity: WorkerIdentitySpec) -> WorkerIdentitySpec:
        """Return identity with scheduling-eligible caps = effective_capabilities()."""
        effective = sorted(identity.effective_capabilities())
        return identity.model_copy(update={"verified_capabilities": effective})
