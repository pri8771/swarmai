"""Local outage/split-brain drill harness (ART-V18-03)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from swarm.contracts.common import payload_hash, utc_now
from swarm.recovery.authority import SiteAuthorityService, StaleEpochError
from swarm.recovery.backup import BackupService
from swarm.recovery.restore import RestoreService


@dataclass
class DrillReport:
    status: str
    rpo_seconds: float
    rto_seconds: float
    checks: dict[str, bool]
    detail: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "rpo_seconds": self.rpo_seconds,
            "rto_seconds": self.rto_seconds,
            "checks": dict(self.checks),
            "detail": dict(self.detail),
            "generated_at": utc_now().isoformat(),
            "digest": payload_hash(
                {"status": self.status, "checks": self.checks, "detail": self.detail}
            ),
        }


class OutageDrillHarness:
    def run_local(
        self,
        *,
        site_id: str = "site_local",
        commit_sha: str = "deadbeef",
    ) -> DrillReport:
        auth = SiteAuthorityService()
        current = auth.bootstrap(site_id, epoch=1)
        backup = BackupService().create(
            site_id=site_id,
            epoch=current.epoch,
            commit_sha=commit_sha,
            schema_revision="a18site001",
            secret_ref_names=["SWARM_DATABASE_URL"],
            migration_heads=["a18site001"],
            state_snapshot={"missions": 1},
        )
        # Simulate split-brain: stale epoch dispatch must fail.
        stale_rejected = False
        try:
            auth.require_epoch(site_id, epoch=0, action="dispatch")
        except StaleEpochError:
            stale_rejected = True

        restore = RestoreService(auth)
        receipt = restore.restore(
            backup,
            in_flight_leases=[{"lease_id": "ls_1", "site_epoch": 1}],
            unknown_effects=[{"effect_key": "eff_unknown"}],
        )
        # Old epoch still rejected after restore.
        post_stale = False
        try:
            auth.require_epoch(site_id, epoch=1, action="effect")
        except StaleEpochError:
            post_stale = True
        auth.require_epoch(site_id, epoch=receipt.new_epoch, action="dispatch")

        checks = {
            "backup_created": bool(backup.integrity_digest),
            "secrets_names_only": backup.secret_refs == ["SWARM_DATABASE_URL"],
            "stale_dispatch_rejected": stale_rejected,
            "unknown_effect_preserved": any(
                e.get("retry") is False for e in receipt.unknown_effects
            ),
            "epoch_advanced": receipt.new_epoch == 2,
            "post_restore_stale_rejected": post_stale,
        }
        status = "pass" if all(checks.values()) else "fail"
        return DrillReport(
            status=status,
            rpo_seconds=0.0,
            rto_seconds=0.0,
            checks=checks,
            detail={"backup_id": backup.backup_id, "recovery": receipt.to_dict()},
        )
