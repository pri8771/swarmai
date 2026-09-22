"""OPS-CI-01: heartbeat commits must not trigger GitHub Actions."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HEARTBEAT = REPO / "scripts" / "coordination" / "heartbeat.py"
WORKFLOW = REPO / ".github" / "workflows" / "ci.yml"


def _load_heartbeat_module():
    spec = importlib.util.spec_from_file_location("coord_heartbeat", HEARTBEAT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ci_skip_suffix_is_appended_once() -> None:
    hb = _load_heartbeat_module()
    once = hb.ci_skip("heartbeat(CURSOR-V17-SINGLE): 2026-09-22T00:00:00Z")
    assert once.endswith(" [skip ci]")
    assert hb.ci_skip(once) == once
    assert once.count("[skip ci]") == 1


def test_all_put_file_messages_use_ci_skip() -> None:
    tree = ast.parse(HEARTBEAT.read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "put_file"
    ]
    assert calls, "expected put_file call sites"
    for call in calls:
        message = next((kw.value for kw in call.keywords if kw.arg == "message"), None)
        assert message is not None, "put_file without message="
        assert isinstance(message, ast.Call)
        assert isinstance(message.func, ast.Name) and message.func.id == "ci_skip"


def test_ci_workflow_ignores_docs_paths() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    on_block = text.split("\njobs:", 1)[0]
    push = on_block.split("push:", 1)[1].split("pull_request:", 1)[0]
    pull = on_block.split("pull_request:", 1)[1]
    for trigger in (push, pull):
        assert "paths-ignore" in trigger
        assert '"docs/**"' in trigger
        assert '"**/*.md"' in trigger
    assert "concurrency:" in on_block
    assert "cancel-in-progress: true" in on_block
