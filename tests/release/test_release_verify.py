"""P21 / V0.9 release verify tests — packaging vs behavioral evidence."""

from __future__ import annotations

import json
from pathlib import Path

from swarm.release.harden import redact_mapping, run_security_harden
from swarm.release.install import run_install_check
from swarm.release.verify import verify_release

ROOT = Path(__file__).resolve().parents[2]


def test_release_verify_packaging_without_ci_evidence_is_not_behavioral_pass(
    tmp_path: Path,
) -> None:
    """File presence alone must not claim offline_tested=yes / passed."""
    # Copy minimal packaging surface into an empty tree is heavy; assert on
    # the real repo without offline evidence file.
    evidence = ROOT / "var" / "evidence" / "offline_ci_pass.json"
    existed = evidence.is_file()
    backup = evidence.read_text() if existed else None
    if existed:
        evidence.unlink()
    try:
        report = verify_release(ROOT)
        assert report.matrix["cloud_live_tested"] == "no"
        assert report.matrix["public_launch"] == "no"
        assert report.matrix["offline_tested"].startswith("unknown")
        assert report.passed is False
        assert "evidence-missing" in report.label or "packaging-presence" in report.label
        assert report.mock_vs_live == "packaging_check_not_behavioral_proof"
        offline_item = next(i for i in report.items if i.item_id == "offline_ci_evidence")
        assert offline_item.ok is False
    finally:
        if backup is not None:
            evidence.parent.mkdir(parents=True, exist_ok=True)
            evidence.write_text(backup)


def test_release_verify_passes_when_offline_evidence_present(tmp_path: Path) -> None:
    evidence_dir = ROOT / "var" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / "offline_ci_pass.json"
    previous = path.read_text() if path.is_file() else None
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "status": "pass",
                "command": "uv run pytest (offline suite)",
                "note": "test fixture evidence — not a live campaign",
            }
        )
        + "\n"
    )
    try:
        report = verify_release(ROOT)
        assert report.passed is True
        assert report.matrix["offline_tested"].startswith("yes")
        assert "offline-evidence-present" in report.label
    finally:
        if previous is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(previous)


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
