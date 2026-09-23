"""SiteAuthority / SiteEpoch fencing (ART-V18)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from swarm.contracts.common import new_id, payload_hash, utc_now


class AuthorityState(StrEnum):
    ACTIVE = "active"
    RECOVERING = "recovering"
    FENCED = "fenced"
    RETIRED = "retired"


class StaleEpochError(PermissionError):
    """Raised when dispatch/result/effect carries a stale site epoch."""


@dataclass
class SiteAuthority:
    site_id: str
    epoch: int
    state: AuthorityState = AuthorityState.ACTIVE
    authority_id: str = field(default_factory=lambda: new_id("auth_"))
    policy_version: str = "v18"
    content_digest: str = ""
    source_site_id: str | None = None
    recovery_id: str | None = None
    activated_at: str = field(default_factory=lambda: utc_now().isoformat())
    fenced_at: str | None = None

    def digest(self) -> str:
        return payload_hash(
            {
                "site_id": self.site_id,
                "epoch": self.epoch,
                "state": self.state.value,
                "policy_version": self.policy_version,
            }
        )


@dataclass
class AuthorityBinding:
    site_id: str
    site_epoch: int
    authority_digest: str


class SiteAuthorityService:
    """In-process authoritative epoch store (durable rows optional via session)."""

    def __init__(self) -> None:
        self._by_site: dict[str, SiteAuthority] = {}
        self._transitions: list[dict[str, Any]] = []

    def bootstrap(self, site_id: str, *, epoch: int = 1) -> SiteAuthority:
        auth = SiteAuthority(site_id=site_id, epoch=epoch)
        auth.content_digest = auth.digest()
        self._by_site[site_id] = auth
        return auth

    def current(self, site_id: str) -> SiteAuthority:
        if site_id not in self._by_site:
            return self.bootstrap(site_id)
        return self._by_site[site_id]

    def require_epoch(self, site_id: str, epoch: int, *, action: str = "dispatch") -> SiteAuthority:
        auth = self.current(site_id)
        if auth.state != AuthorityState.ACTIVE:
            raise StaleEpochError(f"site_not_active:{auth.state.value}:{action}")
        if epoch != auth.epoch:
            raise StaleEpochError(
                f"stale_epoch:action={action}:got={epoch}:want={auth.epoch}"
            )
        return auth

    def binding(self, site_id: str) -> AuthorityBinding:
        auth = self.current(site_id)
        return AuthorityBinding(
            site_id=auth.site_id,
            site_epoch=auth.epoch,
            authority_digest=auth.content_digest or auth.digest(),
        )

    def fence(self, site_id: str, *, reason: str = "split_brain") -> SiteAuthority:
        auth = self.current(site_id)
        auth.state = AuthorityState.FENCED
        auth.fenced_at = utc_now().isoformat()
        self._transitions.append(
            {
                "site_id": site_id,
                "from_epoch": auth.epoch,
                "to_epoch": auth.epoch,
                "reason": reason,
                "state": auth.state.value,
            }
        )
        return auth

    def advance_epoch(
        self,
        site_id: str,
        *,
        reason: str,
        recovery_id: str | None = None,
        source_site_id: str | None = None,
    ) -> SiteAuthority:
        prev = self.current(site_id)
        if prev.state == AuthorityState.ACTIVE:
            prev.state = AuthorityState.RETIRED
            prev.fenced_at = utc_now().isoformat()
        nxt = SiteAuthority(
            site_id=site_id,
            epoch=prev.epoch + 1,
            state=AuthorityState.ACTIVE,
            recovery_id=recovery_id,
            source_site_id=source_site_id or site_id,
        )
        nxt.content_digest = nxt.digest()
        self._by_site[site_id] = nxt
        self._transitions.append(
            {
                "site_id": site_id,
                "from_epoch": prev.epoch,
                "to_epoch": nxt.epoch,
                "reason": reason,
                "recovery_id": recovery_id,
            }
        )
        return nxt

    def transitions(self) -> list[dict[str, Any]]:
        return list(self._transitions)
