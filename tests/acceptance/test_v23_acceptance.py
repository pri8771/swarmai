"""SW-W3-S4: deterministic V2.3 probes A01-A10 bound to the frozen scenario manifest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from swarm.acceptance.v23_probes import (
    DEFAULT_FREEZE,
    PROBES,
    VERSION_CLAIM,
    V23FreezeError,
    load_v23_freeze,
    run_v23_probes,
)


@pytest.fixture(scope="module")
def report(tmp_path_factory: pytest.TempPathFactory) -> dict:
    return run_v23_probes(tmp_path_factory.mktemp("v23"))


def test_every_deterministic_scenario_has_a_probe() -> None:
    data = load_v23_freeze()
    probes = {s["deterministic_probe"] for s in data["scenarios"] if s["deterministic_probe"]}
    assert probes == set(PROBES)


@pytest.mark.parametrize("scenario_id", [f"V23-A{n:02d}" for n in range(1, 11)])
def test_probe_passes(report: dict, scenario_id: str) -> None:
    row = next(r for r in report["results"] if r["id"] == scenario_id)
    assert row["ok"], row


def test_harness_never_claims_acceptance(report: dict) -> None:
    assert report["version_claim"] == VERSION_CLAIM
    assert report["deterministic_passed"] == report["deterministic_total"] == 10
    assert report["pending"] == [{"id": "V23-A11", "status": "pending_owner_approval"}]
    assert "accepted" not in json.dumps(report["pending"])


def test_unknown_probe_fails_closed(tmp_path: Path) -> None:
    data = json.loads(DEFAULT_FREEZE.read_text(encoding="utf-8"))
    data["scenarios"][0]["deterministic_probe"] = "made_up"
    bad = tmp_path / "freeze.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(V23FreezeError, match="freeze_unknown_probe"):
        load_v23_freeze(bad)


def test_policy_drift_fails_closed(tmp_path: Path) -> None:
    data = json.loads(DEFAULT_FREEZE.read_text(encoding="utf-8"))
    data["policy_version"] = "v23-wdrr-999"
    bad = tmp_path / "freeze.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(V23FreezeError, match="freeze_policy_version_mismatch"):
        load_v23_freeze(bad)


def test_crashing_probe_is_a_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(work: Path, scenario: dict) -> None:
        raise RuntimeError("boom")

    monkeypatch.setitem(PROBES, "zero_spend", boom)
    row = next(r for r in run_v23_probes(tmp_path)["results"] if r["id"] == "V23-A10")
    assert row["ok"] is False and row["status"] == "error:RuntimeError"
