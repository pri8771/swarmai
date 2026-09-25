"""Tests for V2.0 acceptance campaign freeze integrity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from swarm.acceptance.freeze import (
    FREEZE_PATH,
    REQUIRED_SCENARIO_IDS,
    FreezeIntegrityError,
    content_hash_for,
    load_freeze,
    verify_freeze_integrity,
)

ROOT = Path(__file__).resolve().parents[2]


def test_freeze_file_exists_and_loads() -> None:
    assert FREEZE_PATH.is_file()
    freeze = load_freeze()
    assert freeze.freeze_id == "v20-acceptance-campaign-20260925"
    assert freeze.public_hostname == "swarm.splitsignal.ai"
    assert len(freeze.scenarios) == 12
    assert tuple(s.id for s in freeze.scenarios) == REQUIRED_SCENARIO_IDS


def test_freeze_separates_gates() -> None:
    freeze = load_freeze()
    assert set(freeze.gates) == {"deterministic", "live", "host", "elapsed"}
    assert freeze.gates["live"]["requires_live_grant"] is True
    assert freeze.gates["host"]["requires_host"] is True
    assert freeze.gates["elapsed"]["requires_elapsed_window"] is True
    assert freeze.observation_windows["elapsed_reliability"]["simulate_elapsed_time"] is False


def test_all_scenarios_have_pass_criteria() -> None:
    freeze = load_freeze()
    for spec in freeze.scenarios:
        assert spec.pass_criteria, spec.id
        assert spec.fail_criteria, spec.id
        assert spec.deterministic_probe, spec.id


def test_version_matrices_not_preaccepted() -> None:
    freeze = load_freeze()
    for ver, meta in freeze.version_matrices.items():
        assert meta.get("accepted") is False, ver
        for sid in meta["required_scenarios"]:
            freeze.scenario(sid)


def test_section10_coverage() -> None:
    freeze = load_freeze()
    titles = " ".join(s.title.lower() for s in freeze.scenarios)
    for needle in (
        "multi-mission",
        "strategy",
        "ongoing",
        "blocked",
        "delegation",
        "succession",
        "restart",
        "duplicate",
        "pause",
        "lesson",
        "sdk",
        "authorized",
    ):
        assert needle in titles, needle


def test_content_hash_stable() -> None:
    freeze = load_freeze()
    raw = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert content_hash_for(raw) == freeze.content_hash
    assert len(freeze.content_hash) == 64


def test_verify_rejects_accepted_preclaim(tmp_path: Path) -> None:
    raw = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    raw["version_matrices"]["V2.0"]["accepted"] = True
    path = tmp_path / "bad.freeze.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(FreezeIntegrityError, match="preclaim_accepted"):
        load_freeze(path)


def test_verify_rejects_elapsed_simulation(tmp_path: Path) -> None:
    raw = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    raw["observation_windows"]["elapsed_reliability"]["simulate_elapsed_time"] = True
    path = tmp_path / "bad2.freeze.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(FreezeIntegrityError, match="elapsed_simulation"):
        load_freeze(path)


def test_verify_freeze_integrity_direct() -> None:
    freeze = load_freeze()
    verify_freeze_integrity(freeze)
