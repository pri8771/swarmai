"""Tests for V2.0 acceptance campaign freeze integrity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from swarm.acceptance.freeze import (
    FREEZE_PATH,
    HOSTNAME_VALIDATION_POLICY,
    REQUIRED_SCENARIO_IDS,
    VERSION_ACCEPTANCE_MANIFEST_PATH,
    FreezeIntegrityError,
    content_hash_for,
    is_valid_public_hostname,
    load_freeze,
    load_version_acceptance_manifest,
    resolve_deployment_public_hostname,
    verify_freeze_integrity,
    verify_version_acceptance_manifest,
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


def test_freeze_does_not_hardcode_splitsignal_hostname() -> None:
    """Protected regression: integrity must not require literal swarm.splitsignal.ai."""
    import inspect

    from swarm.acceptance import freeze as freeze_mod
    from swarm.product.portable_config import PublicEndpointConfig

    source = inspect.getsource(freeze_mod.verify_freeze_integrity)
    assert '!= "swarm.splitsignal.ai"' not in source
    assert '== "swarm.splitsignal.ai"' not in source
    assert HOSTNAME_VALIDATION_POLICY == "match_deployment_config"
    assert resolve_deployment_public_hostname(env={}) is None
    assert resolve_deployment_public_hostname(env={"SWARM_PUBLIC_HOSTNAME": ""}) is None
    # P4 contract is the deployment config surface.
    cfg = PublicEndpointConfig(
        public_hostname="accept.example.test",
        api_base_url="https://accept.example.test",
    )
    assert cfg.matches_configured_hostname("accept.example.test")


def test_freeze_hostname_matches_deployment_config(tmp_path: Path) -> None:
    """Protected regression: alternate hostname OK when PublicEndpointConfig matches."""
    from swarm.product.portable_config import PublicEndpointConfig

    raw = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    raw["public_hostname"] = "accept.example.test"
    path = tmp_path / "portable.freeze.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    endpoint = PublicEndpointConfig(
        public_hostname="accept.example.test",
        api_base_url="https://accept.example.test",
    )
    freeze = load_freeze(
        path,
        endpoint=endpoint,
        verify_manifest=False,
    )
    assert freeze.public_hostname == "accept.example.test"
    assert is_valid_public_hostname(freeze.public_hostname)


def test_freeze_hostname_mismatch_deployment_config(tmp_path: Path) -> None:
    from swarm.product.portable_config import PublicEndpointConfig

    raw = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    raw["public_hostname"] = "accept.example.test"
    path = tmp_path / "mismatch.freeze.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    endpoint = PublicEndpointConfig(
        public_hostname="other.example.test",
        api_base_url="https://other.example.test",
    )
    with pytest.raises(FreezeIntegrityError, match="hostname_mismatch"):
        load_freeze(
            path,
            endpoint=endpoint,
            verify_manifest=False,
        )


def test_version_acceptance_manifest_tracks_scope() -> None:
    freeze = load_freeze()
    assert VERSION_ACCEPTANCE_MANIFEST_PATH.is_file()
    manifest = load_version_acceptance_manifest()
    assert manifest["literal_hostname_forbidden"] is True
    assert manifest["any_version_accepted"] is False
    verify_version_acceptance_manifest(freeze, manifest=manifest)
    # Historical freeze content_hash preserved (freeze file unchanged by policy).
    raw = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert content_hash_for(raw) == freeze.content_hash
