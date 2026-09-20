"""P21 / V0.9 release verify tests."""

from __future__ import annotations

from pathlib import Path

from swarm.release.harden import redact_mapping, run_security_harden
from swarm.release.install import run_install_check
from swarm.release.verify import verify_release

ROOT = Path(__file__).resolve().parents[2]


def test_release_verify_passes_offline() -> None:
    report = verify_release(ROOT)
    assert report.passed is True
    assert report.label == "offline-verified-release-candidate"
    assert report.matrix["cloud_live_tested"] == "no"
    assert report.matrix["deployed"].startswith("no")
    assert report.matrix["public_launch"] == "no"
    assert report.mock_vs_live == "offline_release_candidate"
    assert all(i.ok for i in report.items if i.item_id.startswith("secret_untracked"))


def test_security_harden_ok() -> None:
    report = run_security_harden(ROOT)
    assert report.ok is True
    assert not report.tracked_secret_files


def test_redact_mapping() -> None:
    cleaned = redact_mapping({"api_key": "sk-live-should-hide", "mission_id": "m1"})
    assert cleaned["api_key"] == "[redacted]"
    assert cleaned["mission_id"] == "m1"


def test_install_check_ok() -> None:
    report = run_install_check(ROOT)
    assert report.ok is True
