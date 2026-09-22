"""R28d-1 local sandbox operations and confinement regressions."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

import pytest

from swarm.tools.adapters.base import AdapterDeniedError
from swarm.tools.adapters.local_sandbox import LocalSandboxAdapter
from swarm.tools.manifests import MANIFEST_DIR, load_manifest


def _adapter(root: Path, *, allowlist: list[list[str]] | None = None) -> LocalSandboxAdapter:
    return LocalSandboxAdapter(
        load_manifest(MANIFEST_DIR / "local.sandbox@1.json"),
        root=root,
        command_allowlist=allowlist,
    )


def test_manifest_declares_only_released_operations_with_effective_classification(
    tmp_path: Path,
) -> None:
    adapter = _adapter(tmp_path)

    assert set(adapter.manifest.operations) == {"fs.write_text", "proc.run"}
    assert adapter.command_allowlist == (
        ("uv", "run", "pytest"),
        ("python", "-m", "pytest"),
        ("git", "diff"),
        ("git", "status"),
        ("git", "rev-parse"),
    )
    assert {
        name: (declaration.side_effect_class, declaration.risk_class)
        for name, declaration in adapter.manifest.operations.items()
    } == {
        "fs.write_text": ("idempotent", "low"),
        "proc.run": ("idempotent", "low"),
    }

    for operation in adapter.manifest.operations:
        request: dict[str, Any] = {"project_id": "r28d1", "operation": operation}
        if operation == "proc.run":
            request["argv"] = ["git", "status"]
        envelope = adapter.normalize(request)
        declaration = adapter.manifest.operations[operation]
        assert envelope.side_effect_class == declaration.side_effect_class
        assert envelope.risk_class == declaration.risk_class
        assert envelope.requested_scopes == declaration.scopes


def test_write_text_reports_hashes_and_bytes(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    target = tmp_path / "nested" / "result.txt"
    envelope = adapter.normalize(
        {
            "project_id": "r28d1",
            "operation": "fs.write_text",
            "path": "nested/result.txt",
            "text": "first",
        }
    )

    adapter.validate(envelope)
    assert adapter.observe_pre_state(envelope) == {"sha256": None}
    result = adapter.execute(envelope)
    assert result["outcome"] == "succeeded"
    assert target.read_text(encoding="utf-8") == "first"
    assert adapter.observe_post_state(envelope, result) == {
        "sha256": hashlib.sha256(b"first").hexdigest(),
        "bytes": 5,
    }

    target.write_bytes(b"prior")
    assert adapter.observe_pre_state(envelope) == {"sha256": hashlib.sha256(b"prior").hexdigest()}


@pytest.mark.parametrize("path", ["../outside.txt", "/tmp/outside.txt"])
def test_write_text_rejects_lexical_escape_before_mutation(tmp_path: Path, path: str) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("preserve", encoding="utf-8")
    adapter = _adapter(root)
    envelope = adapter.normalize(
        {
            "project_id": "r28d1",
            "operation": "fs.write_text",
            "path": path,
            "text": "changed",
        }
    )

    with pytest.raises(AdapterDeniedError, match="^path_outside_root$"):
        adapter.validate(envelope)
    assert outside.read_text(encoding="utf-8") == "preserve"


def test_write_text_rejects_symlink_escape_without_outside_mutation(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)
    target = outside / "created.txt"
    adapter = _adapter(root)
    envelope = adapter.normalize(
        {
            "project_id": "r28d1",
            "operation": "fs.write_text",
            "path": "escape/created.txt",
            "text": "must not escape",
        }
    )

    with pytest.raises(AdapterDeniedError, match="^path_outside_root$"):
        adapter.validate(envelope)
    assert not target.exists()


def test_command_denial_occurs_before_subprocess(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_run(*args: Any, **kwargs: Any) -> None:
        pytest.fail(f"denied command reached subprocess: {args!r} {kwargs!r}")

    monkeypatch.setattr(subprocess, "run", unexpected_run)
    adapter = _adapter(tmp_path, allowlist=[["python", "-m", "pytest"]])
    envelope = adapter.normalize(
        {
            "project_id": "r28d1",
            "operation": "proc.run",
            "argv": ["python", "-c", "print('not allowed')"],
            "timeout_s": 2,
        }
    )

    with pytest.raises(AdapterDeniedError, match="^command_not_allowlisted$"):
        adapter.validate(envelope)


def test_proc_run_uses_fixed_cwd_no_shell_and_reports_nonzero_with_bounded_tails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stdout = b"prefix-out-" + b"o" * 5000
    stderr = b"prefix-err-" + b"e" * 5000
    observed: dict[str, Any] = {}

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        observed.update({"argv": argv, **kwargs})
        return subprocess.CompletedProcess(argv, 7, stdout=stdout, stderr=stderr)

    monkeypatch.setattr(subprocess, "run", fake_run)
    adapter = _adapter(tmp_path, allowlist=[["python", "-m", "pytest"]])
    envelope = adapter.normalize(
        {
            "project_id": "r28d1",
            "operation": "proc.run",
            "argv": ["python", "-m", "pytest", "tests/unit"],
            "timeout_s": 3,
        }
    )

    adapter.validate(envelope)
    result = adapter.execute(envelope)

    assert observed == {
        "argv": ["python", "-m", "pytest", "tests/unit"],
        "cwd": tmp_path.resolve(),
        "shell": False,
        "capture_output": True,
        "check": False,
        "timeout": 3.0,
    }
    assert result["outcome"] == "succeeded"
    assert result["exit_code"] == 7
    assert result["stdout_sha256"] == hashlib.sha256(stdout).hexdigest()
    assert result["stderr_sha256"] == hashlib.sha256(stderr).hexdigest()
    assert result["stdout_tail"].encode() == stdout[-4096:]
    assert result["stderr_tail"].encode() == stderr[-4096:]
    assert len(result["stdout_tail"].encode()) == 4096
    assert len(result["stderr_tail"].encode()) == 4096
    assert adapter.observe_post_state(envelope, result) == {"result": result}
