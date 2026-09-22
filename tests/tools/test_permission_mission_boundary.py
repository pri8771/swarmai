"""Permission proof requires durable storage before touching its local workspace."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from swarm.tools.permission_mission import run_permission_mission


@pytest.mark.asyncio
@pytest.mark.parametrize("database_url", [None, "sqlite:///:memory:"])
async def test_permission_proof_without_durable_postgres_has_no_local_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, database_url: str | None
) -> None:
    if database_url is None:
        monkeypatch.delenv("SWARM_DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("SWARM_DATABASE_URL", database_url)
    result = await run_permission_mission(tmp_path)
    assert result == {"ok": False, "reason": "durable_store_required", "cost_usd": 0.0}
    assert list(tmp_path.iterdir()) == []


def test_permission_proof_cli_reports_missing_durable_store(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2] / "src"
    env = {**os.environ, "PYTHONPATH": str(source)}
    env.pop("SWARM_DATABASE_URL", None)
    result = subprocess.run(
        [sys.executable, "-m", "swarm.cli", "tools", "permission-proof"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["reason"] == "durable_store_required"
    assert list(tmp_path.iterdir()) == []
