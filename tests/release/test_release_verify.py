"""P21 release verify tests."""

from __future__ import annotations

from pathlib import Path

from swarm.release.verify import verify_release

ROOT = Path(__file__).resolve().parents[2]


def test_release_verify_passes_offline() -> None:
    report = verify_release(ROOT)
    assert report.passed is True
    assert report.label == "offline-verified-release-candidate"
    assert report.matrix["live_tested"] == "no"
    assert report.matrix["deployed"].startswith("no")
    assert report.mock_vs_live == "offline_release_candidate"
    assert all(i.ok for i in report.items if i.item_id.startswith("secret_absent"))
