"""SW-W1-S6: portability bundle v2 (ART acceptance item 7) and value secret scan (F-03)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from swarm.product.portability import PortabilityService


def _export(svc: PortabilityService, out: Path, **kw: object):
    base: dict[str, object] = {
        "project_id": "proj_src",
        "project_config": {"name": "demo", "db_url": "env:SWARM_DATABASE_URL"},
        "out_dir": out,
    }
    base.update(kw)
    return svc.export_project(**base)  # type: ignore[arg-type]


def test_value_based_secret_scan(tmp_path: Path) -> None:
    svc = PortabilityService()
    for config in (
        {"notes": "use sk-abcdefghijklmnop to call"},
        {"endpoint": "https://x.test/?token=abcd1234"},
        {"header": "Bearer abcdefghijklmnopqrstuvwxyz"},
        {"api_key": "env:not a valid ref"},
        {"password": 12345},
        {"secret": {"value": "nested-credential-material"}},
        {"notes": "ss_live_0123456789abcdef0123456789abcdef_abcdefghijklmnopqrstuvwxyzABCDEFG"},
        {"notes": "postgresql://user:password@db.internal/private"},
    ):
        with pytest.raises(ValueError, match="secret"):
            _export(svc, tmp_path, project_config=config)
    with pytest.raises(ValueError, match="secret"):
        _export(svc, tmp_path, history=[{"event": "call", "detail": "sk-live-abcdefghijk"}])


def test_roundtrip_with_history_into_clean_root(tmp_path: Path) -> None:
    svc = PortabilityService()
    bundle = _export(
        svc,
        tmp_path / "a",
        history=[{"event": "mission.created", "project_id": "proj_src", "mission_id": "msn_1"}],
        receipts=[{"receipt_id": "sdr_1", "project_id": "proj_src", "digest": "d1"}],
        approvals=[{"approval_id": "apr_1", "state": "approved", "project_id": "proj_src"}],
        leases=[{"lease_id": "ls_1", "state": "active"}],
        artifact_digests={"art_1": "sha256:aa"},
    )
    clean = tmp_path / "clean"
    clean.mkdir()
    src = tmp_path / "a" / f"{bundle.bundle_id}.json"
    (clean / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    loaded = svc.import_bundle(clean / src.name)
    assert loaded.integrity_digest == bundle.integrity_digest
    assert loaded.schema_version == "2"
    assert loaded.sections["artifact_digests"] == {"art_1": "sha256:aa"}
    for name in ("approvals", "leases"):
        for item in loaded.sections[name]:
            assert item["executable"] is False
            assert item["state"] == "tombstoned"
    assert loaded.sections["approvals"][0]["original_state"] == "approved"


def test_tampered_section_rejected(tmp_path: Path) -> None:
    svc = PortabilityService()
    bundle = _export(svc, tmp_path, receipts=[{"receipt_id": "sdr_1", "digest": "d1"}])
    path = tmp_path / f"{bundle.bundle_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["sections"]["receipts"][0]["digest"] = "forged"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="bundle_section_mismatch:receipts"):
        svc.import_bundle(path)


def test_executable_approval_injection_rejected(tmp_path: Path) -> None:
    svc = PortabilityService()
    bundle = _export(svc, tmp_path, approvals=[{"approval_id": "apr_1", "state": "approved"}])
    path = tmp_path / f"{bundle.bundle_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["sections"]["approvals"][0]["executable"] = True
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="bundle_(section_mismatch|live_authority)"):
        svc.import_bundle(path)


def test_incompatible_reader_rejected(tmp_path: Path) -> None:
    svc = PortabilityService()
    bundle = _export(svc, tmp_path)
    path = tmp_path / f"{bundle.bundle_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["compatibility"]["min_reader"] = 99
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="bundle_incompatible"):
        svc.import_bundle(path)


def test_namespace_remap(tmp_path: Path) -> None:
    svc = PortabilityService()
    bundle = _export(
        svc, tmp_path, history=[{"event": "mission.created", "project_id": "proj_src"}]
    )
    loaded = svc.import_bundle(
        tmp_path / f"{bundle.bundle_id}.json", target_project_id="proj_dst"
    )
    assert loaded.project_id == "proj_dst"
    assert loaded.remapped_from == "proj_src"
    assert loaded.sections["history"][0]["project_id"] == "proj_dst"


def test_schema1_bundle_still_imports(tmp_path: Path) -> None:
    from swarm.contracts.common import payload_hash

    body = {
        "project_id": "p",
        "project_config": {"name": "old"},
        "knowledge_refs": [],
        "capability_pack_config": {},
        "policy_refs": [],
        "artifact_refs": [],
        "version_manifest": {},
    }
    data = {"bundle_id": "port_old", "created_at": "2026-01-01T00:00:00+00:00", **body}
    data["integrity_digest"] = payload_hash(body)
    path = tmp_path / "port_old.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    loaded = PortabilityService().import_bundle(path)
    assert loaded.schema_version == "1"
    assert loaded.project_config == {"name": "old"}
