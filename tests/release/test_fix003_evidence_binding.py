"""FIX-003: release evidence must bind candidate SHA, exit/result, mode, freshness."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from swarm.release.verify import (
    EVIDENCE_MAX_AGE,
    _validate_evidence_file,
    verify_release,
)

ROOT = Path(__file__).resolve().parents[2]


def _tip_sha() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    return proc.stdout.strip()


def _write_evidence(path: Path, **fields: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fields, indent=2) + "\n", encoding="utf-8")


def _valid_offline_fields(tip: str) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "status": "pass",
        "command": "uv run pytest (offline suite)",
        "exit_code": 0,
        "mode": "offline_ci",
        "candidate_sha": tip,
        "generated_at": datetime.now(UTC).isoformat(),
        "config_version": "1.0",
    }


def test_missing_candidate_sha_fails(tmp_path: Path) -> None:
    tip = _tip_sha()
    path = tmp_path / "offline_ci_pass.json"
    fields = _valid_offline_fields(tip)
    del fields["candidate_sha"]
    _write_evidence(path, **fields)
    item = _validate_evidence_file(path, expected_kind="offline_ci", candidate_sha=tip)
    assert item.ok is False
    assert "missing_candidate_sha" in item.detail


def test_wrong_candidate_sha_fails(tmp_path: Path) -> None:
    tip = _tip_sha()
    path = tmp_path / "offline_ci_pass.json"
    fields = _valid_offline_fields(tip)
    fields["candidate_sha"] = "deadbeef" * 5
    _write_evidence(path, **fields)
    item = _validate_evidence_file(path, expected_kind="offline_ci", candidate_sha=tip)
    assert item.ok is False
    assert "sha_mismatch" in item.detail


def test_stale_timestamp_fails(tmp_path: Path) -> None:
    tip = _tip_sha()
    path = tmp_path / "offline_ci_pass.json"
    fields = _valid_offline_fields(tip)
    fields["generated_at"] = (datetime.now(UTC) - EVIDENCE_MAX_AGE - timedelta(days=1)).isoformat()
    _write_evidence(path, **fields)
    item = _validate_evidence_file(path, expected_kind="offline_ci", candidate_sha=tip)
    assert item.ok is False
    assert "stale_evidence" in item.detail


def test_failed_exit_fails(tmp_path: Path) -> None:
    tip = _tip_sha()
    path = tmp_path / "offline_ci_pass.json"
    fields = _valid_offline_fields(tip)
    fields["exit_code"] = 1
    _write_evidence(path, **fields)
    item = _validate_evidence_file(path, expected_kind="offline_ci", candidate_sha=tip)
    assert item.ok is False
    assert "exit_code_nonzero" in item.detail


def test_wrong_mode_fails(tmp_path: Path) -> None:
    tip = _tip_sha()
    path = tmp_path / "offline_ci_pass.json"
    fields = _valid_offline_fields(tip)
    fields["mode"] = "live_local"
    _write_evidence(path, **fields)
    item = _validate_evidence_file(path, expected_kind="offline_ci", candidate_sha=tip)
    assert item.ok is False
    assert "mode_mismatch" in item.detail or "mode_not_offline" in item.detail


def test_status_pass_alone_cannot_bypass_missing_exit(tmp_path: Path) -> None:
    tip = _tip_sha()
    path = tmp_path / "offline_ci_pass.json"
    fields = _valid_offline_fields(tip)
    del fields["exit_code"]
    _write_evidence(path, **fields)
    item = _validate_evidence_file(path, expected_kind="offline_ci", candidate_sha=tip)
    assert item.ok is False
    assert "missing_exit_or_result" in item.detail


def test_valid_bound_evidence_passes(tmp_path: Path) -> None:
    tip = _tip_sha()
    path = tmp_path / "offline_ci_pass.json"
    _write_evidence(path, **_valid_offline_fields(tip))
    item = _validate_evidence_file(path, expected_kind="offline_ci", candidate_sha=tip)
    assert item.ok is True


def test_release_verify_rejects_no_sha_evidence() -> None:
    """Regression: prior test expected no-SHA evidence to pass — FIX-003 forbids that."""
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
                "note": "intentionally missing sha/exit/timestamp — must fail",
            }
        )
        + "\n"
    )
    try:
        report = verify_release(ROOT)
        assert report.passed is False
        offline_item = next(i for i in report.items if i.item_id == "offline_ci_evidence")
        assert offline_item.ok is False
        assert "missing_candidate_sha" in offline_item.detail
    finally:
        if previous is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(previous)


def test_release_verify_passes_with_bound_evidence() -> None:
    tip = _tip_sha()
    evidence_dir = ROOT / "var" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / "offline_ci_pass.json"
    previous = path.read_text() if path.is_file() else None
    _write_evidence(path, **_valid_offline_fields(tip))
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
