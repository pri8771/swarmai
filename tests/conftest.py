"""Shared pytest configuration: evidence levels and the live fixture process."""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """`integration` needs SWARM_DATABASE_URL; `live_local` needs SWARM_LIVE_LOCAL=1.

    A skipped test is reported as skipped — never as a pass.
    """
    no_db = not (os.environ.get("SWARM_DATABASE_URL") or "").strip()
    no_live = os.environ.get("SWARM_LIVE_LOCAL", "").strip() != "1"
    for item in items:
        if no_db and item.get_closest_marker("integration") is not None:
            item.add_marker(pytest.mark.skip(reason="integration: SWARM_DATABASE_URL not set"))
        if no_live and item.get_closest_marker("live_local") is not None:
            item.add_marker(pytest.mark.skip(reason="live_local: SWARM_LIVE_LOCAL != 1"))


@pytest.fixture()
def live_fixture_credentials() -> dict[str, str]:
    return {"user": "fixture-user", "password": secrets.token_urlsafe(18)}


@pytest.fixture()
def live_fixture_url(live_fixture_credentials: dict[str, str]) -> Iterator[str]:
    """Start the live fixture service as a real subprocess; yield its base URL."""
    env = {
        **os.environ,
        "FIXTURE_USER": live_fixture_credentials["user"],
        "FIXTURE_PASSWORD": live_fixture_credentials["password"],
        "FIXTURE_SESSION_TTL_S": os.environ.get("FIXTURE_SESSION_TTL_S", "2"),
        "FIXTURE_DROP_HOLD_S": os.environ.get("FIXTURE_DROP_HOLD_S", "3"),
        "PYTHONPATH": str(REPO),
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "sandbox.live_fixture", "--port", "0"],
        cwd=str(REPO),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert proc.stdout is not None
        deadline = time.monotonic() + 10
        line = ""
        while time.monotonic() < deadline:
            line = proc.stdout.readline()
            if line.startswith("{"):
                break
            if proc.poll() is not None:
                break
        if not line.startswith("{"):
            err = proc.stderr.read() if proc.stderr else ""
            raise RuntimeError(f"live fixture did not start: {err[-800:]}")
        url = json.loads(line)["url"]
        # Wait for readiness.
        import httpx

        for _ in range(50):
            try:
                if httpx.get(f"{url}/healthz", timeout=0.5).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.1)
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
