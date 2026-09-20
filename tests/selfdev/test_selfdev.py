"""P19 controlled self-development tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.selfdev.policy import scan_diff_for_privilege_expansion, validate_worker_patch
from swarm.selfdev.runner import (
    run_self_development,
    worker_cannot_access_production_secrets,
)


def test_privilege_expansion_markers() -> None:
    hits = scan_diff_for_privilege_expansion("enable auto_merge and self_approve")
    assert "auto_merge" in hits
    assert "self_approve" in hits


def test_self_approval_forbidden() -> None:
    verdict = validate_worker_patch(
        changed_paths=["parser_helper.py"],
        diff_text="return end - start + 1",
        allowlisted_paths=["sandbox/selfdev_issue/parser_helper.py"],
        author_role="worker",
        reviewer_role="reviewer",
        author_id="same",
        reviewer_id="same",
    )
    assert verdict.allowed is False
    assert any("self_approval" in r for r in verdict.reasons)


def test_worker_no_host_secrets() -> None:
    assert worker_cannot_access_production_secrets() is True


@pytest.mark.asyncio
async def test_good_patch_produces_artifact(tmp_path: Path) -> None:
    report = run_self_development(mode="mock", variant="good", report_dir=tmp_path)
    assert report.tests_passed is True
    assert report.policy_allowed is True
    assert report.merged is False
    assert report.patch_path
    assert report.mock_vs_live == "simulated_selfdev_not_live"
    assert Path(report.patch_path).exists()
    assert (tmp_path / f"{report.run_id}.json").exists()


@pytest.mark.asyncio
async def test_failing_patch_rejected(tmp_path: Path) -> None:
    report = run_self_development(mode="mock", variant="failing", report_dir=tmp_path)
    assert report.tests_passed is False
    assert report.patch_path is None
    assert report.checks["review_accepted"] is False


@pytest.mark.asyncio
async def test_malicious_privilege_diff_flagged(tmp_path: Path) -> None:
    report = run_self_development(mode="mock", variant="malicious", report_dir=tmp_path)
    assert report.policy_allowed is False
    assert any("privilege_expansion" in r or "forbidden_path" in r for r in report.policy_reasons)
    assert report.patch_path is None
    assert report.merged is False


def test_live_mode_blocked(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="live_selfdev_blocked"):
        run_self_development(mode="live", report_dir=tmp_path)
