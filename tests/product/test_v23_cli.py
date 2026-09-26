"""SW-W3-S3: ``swarm v23 …`` commands are offline, deterministic and fail closed."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from swarm.capabilities import CapabilityPackManifest
from swarm.cli import main


def _run(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], *argv: str):
    monkeypatch.setattr(sys, "argv", ["swarm", "v23", *argv])
    code = 0
    try:
        main()
    except SystemExit as exc:
        code = int(exc.code or 0)
    return code, json.loads(capsys.readouterr().out)


def test_policy_loads(monkeypatch, capsys) -> None:
    code, out = _run(monkeypatch, capsys, "scheduler-policy")
    assert code == 0 and out["policy"]["policy_version"] == "v23-wdrr-1"


def test_simulate_matches_weights(monkeypatch, capsys) -> None:
    code, out = _run(
        monkeypatch, capsys, "scheduler-simulate", "--projects", "a:1,b:3", "--decisions", "400"
    )
    assert code == 0
    assert out["admitted"] == {"a": 100, "b": 300}
    assert out["share"] == out["target_share"]


@pytest.mark.parametrize(
    "argv",
    [
        ("--projects", "a:0"),
        ("--projects", "a"),
        ("--projects", "a:1", "--decisions", "0"),
        ("--projects", "a:1", "--decisions", "100001"),
    ],
)
def test_simulate_rejects_bad_input(monkeypatch, capsys, argv) -> None:
    code, out = _run(monkeypatch, capsys, "scheduler-simulate", *argv)
    assert code == 2 and out["ok"] is False


def test_pack_sign_then_verify(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("SWARM_PACK_TRUSTED_PUBLISHERS", "acme")
    monkeypatch.setenv("SWARM_PACK_KEY_ACME", "test-only-key")
    src = tmp_path / "m.json"
    src.write_text(
        CapabilityPackManifest(
            pack_id="p", version="1", content_digest="sha256:x", publisher="acme"
        ).model_dump_json(),
        encoding="utf-8",
    )
    signed = tmp_path / "signed.json"
    code, out = _run(monkeypatch, capsys, "pack-sign", "--manifest", str(src), "--out", str(signed))
    assert code == 0 and out["ok"]
    code, out = _run(monkeypatch, capsys, "pack-verify", "--manifest", str(signed))
    assert code == 0 and out == {"ok": True, "pack_id": "p", "publisher": "acme"}
    code, out = _run(monkeypatch, capsys, "pack-verify", "--manifest", str(src))
    assert code == 2 and out["error"] == "pack_signature_unkeyed"
    monkeypatch.setenv("SWARM_PACK_KEY_ACME", "rotated-key")
    code, out = _run(monkeypatch, capsys, "pack-verify", "--manifest", str(signed))
    assert code == 2 and out["error"] == "pack_signature_invalid"


def test_pack_sign_without_key_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("SWARM_PACK_TRUSTED_PUBLISHERS", raising=False)
    src = tmp_path / "m.json"
    src.write_text(
        CapabilityPackManifest(
            pack_id="p", version="1", content_digest="sha256:x", publisher="acme"
        ).model_dump_json(),
        encoding="utf-8",
    )
    code, out = _run(
        monkeypatch, capsys, "pack-sign", "--manifest", str(src), "--out", str(tmp_path / "o")
    )
    assert code == 2 and out["error"] == "no_trusted_key_for_publisher:acme"


def test_export_import_roundtrip_and_tamper(tmp_path: Path, monkeypatch, capsys) -> None:
    code, out = _run(
        monkeypatch, capsys, "export", "--project-id", "proj_x", "--out-dir", str(tmp_path)
    )
    assert code == 0
    path = Path(out["path"])
    code, out = _run(
        monkeypatch, capsys, "import", "--bundle", str(path), "--target-project-id", "proj_y"
    )
    assert code == 0 and out["project_id"] == "proj_y"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["project_config"]["project_id"] = "tampered"
    path.write_text(json.dumps(data), encoding="utf-8")
    code, out = _run(monkeypatch, capsys, "import", "--bundle", str(path))
    assert code == 2 and out["error"] == "bundle_integrity_mismatch"
