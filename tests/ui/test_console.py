"""P09 console build/smoke checks from the Python test runner."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONSOLE = ROOT / "apps" / "console"


@pytest.mark.skipif(not (CONSOLE / "package.json").exists(), reason="console app missing")
def test_console_package_scripts() -> None:
    pkg = json.loads((CONSOLE / "package.json").read_text())
    assert "test" in pkg["scripts"]
    assert "build" in pkg["scripts"]


@pytest.mark.skipif(not (CONSOLE / "node_modules").exists(), reason="npm install not run")
def test_console_vitest() -> None:
    result = subprocess.run(
        ["npm", "test"],
        cwd=CONSOLE,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(not (CONSOLE / "node_modules").exists(), reason="npm install not run")
def test_console_build_has_no_secret_literals() -> None:
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=CONSOLE,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    dist = CONSOLE / "dist"
    blob = ""
    for path in dist.rglob("*"):
        if path.is_file() and path.suffix in {".js", ".html", ".css", ".map"}:
            blob += path.read_text(errors="ignore")
    import re

    # Provider-key shape only (avoid SVG attrs like mask-type containing "sk-").
    assert re.search(r"sk-[a-zA-Z0-9]{8,}", blob) is None
    assert "OPENROUTER_API_KEY=" not in blob
    assert re.search(r"api_key\s*=\s*\S+", blob, re.I) is None
