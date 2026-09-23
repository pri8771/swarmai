"""V1.8 recovery / site-epoch deterministic tests."""

from __future__ import annotations

import pytest

from swarm.recovery import (
    BackupService,
    OutageDrillHarness,
    RestoreService,
    SiteAuthorityService,
    StaleEpochError,
)


def test_stale_epoch_dispatch_rejected() -> None:
    auth = SiteAuthorityService()
    auth.bootstrap("site_a", epoch=3)
    with pytest.raises(StaleEpochError, match="stale_epoch"):
        auth.require_epoch("site_a", 2, action="dispatch")
    auth.require_epoch("site_a", 3, action="dispatch")


def test_backup_rejects_secret_values(tmp_path) -> None:
    svc = BackupService(root=tmp_path)
    with pytest.raises(ValueError, match="secret_value_forbidden"):
        svc.create(
            site_id="site_a",
            epoch=1,
            commit_sha="abc",
            schema_revision="a18",
            state_snapshot={"db_password": "hunter2"},
        )


def test_restore_preserves_unknown_effects_without_retry(tmp_path) -> None:
    auth = SiteAuthorityService()
    auth.bootstrap("site_a", epoch=1)
    backup = BackupService(root=tmp_path).create(
        site_id="site_a",
        epoch=1,
        commit_sha="abc123",
        schema_revision="a18",
        secret_ref_names=["SWARM_DATABASE_URL"],
    )
    receipt = RestoreService(auth).restore(
        backup,
        in_flight_leases=[{"lease_id": "L1", "site_epoch": 1}],
        unknown_effects=[{"effect_key": "E1"}],
    )
    assert receipt.new_epoch == 2
    assert receipt.unknown_effects[0]["retry"] is False
    with pytest.raises(StaleEpochError):
        auth.require_epoch("site_a", 1, action="effect")


def test_outage_drill_harness_passes() -> None:
    report = OutageDrillHarness().run_local(commit_sha="testdrill")
    assert report.status == "pass"
    assert report.checks["unknown_effect_preserved"] is True
