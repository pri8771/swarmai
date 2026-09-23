"""Restore + reconciliation — preserve unknown effects, no blind retry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.common import new_id, payload_hash, utc_now
from swarm.recovery.authority import SiteAuthorityService
from swarm.recovery.backup import BackupManifest


@dataclass
class RecoveryReceipt:
    recovery_id: str
    backup_id: str
    old_site_id: str
    old_epoch: int
    new_site_id: str
    new_epoch: int
    final_state: str
    lease_actions: list[dict[str, Any]] = field(default_factory=list)
    unknown_effects: list[dict[str, Any]] = field(default_factory=list)
    fenced_stale_epochs: list[int] = field(default_factory=list)
    evidence_digest: str = ""
    started_at: str = ""
    finished_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_id": self.recovery_id,
            "backup_id": self.backup_id,
            "old_site_id": self.old_site_id,
            "old_epoch": self.old_epoch,
            "new_site_id": self.new_site_id,
            "new_epoch": self.new_epoch,
            "final_state": self.final_state,
            "lease_actions": list(self.lease_actions),
            "unknown_effects": list(self.unknown_effects),
            "fenced_stale_epochs": list(self.fenced_stale_epochs),
            "evidence_digest": self.evidence_digest,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class RestoreService:
    def __init__(self, authority: SiteAuthorityService) -> None:
        self.authority = authority

    def restore(
        self,
        manifest: BackupManifest,
        *,
        in_flight_leases: list[dict[str, Any]] | None = None,
        unknown_effects: list[dict[str, Any]] | None = None,
        new_site_id: str | None = None,
    ) -> RecoveryReceipt:
        started = utc_now().isoformat()
        recovery_id = new_id("rcv_")
        old_site = manifest.source_site_id
        old_epoch = manifest.source_epoch
        target_site = new_site_id or old_site

        # Fence old authority / advance epoch before writes.
        try:
            self.authority.fence(old_site, reason="restore")
        except Exception:
            pass
        new_auth = self.authority.advance_epoch(
            target_site,
            reason="restore",
            recovery_id=recovery_id,
            source_site_id=old_site,
        )

        lease_actions: list[dict[str, Any]] = []
        for lease in in_flight_leases or []:
            lease_actions.append(
                {
                    "lease_id": lease.get("lease_id") or lease.get("id"),
                    "action": "expire_uncertain",
                    "prior_epoch": lease.get("site_epoch", old_epoch),
                }
            )

        # Unknown effects are preserved — never blindly retried.
        preserved = []
        for effect in unknown_effects or []:
            preserved.append(
                {
                    "effect_key": effect.get("effect_key"),
                    "state": "unknown_preserved",
                    "retry": False,
                }
            )

        receipt = RecoveryReceipt(
            recovery_id=recovery_id,
            backup_id=manifest.backup_id,
            old_site_id=old_site,
            old_epoch=old_epoch,
            new_site_id=new_auth.site_id,
            new_epoch=new_auth.epoch,
            final_state="recovered",
            lease_actions=lease_actions,
            unknown_effects=preserved,
            fenced_stale_epochs=[old_epoch],
            started_at=started,
            finished_at=utc_now().isoformat(),
        )
        receipt.evidence_digest = payload_hash(receipt.to_dict())
        return receipt
