#!/usr/bin/env python3
"""Dump V1.7 collab + continuous-connector campaign evidence (no spend)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from swarm.mission.collab_connector_campaign import run_collab_connector_campaign  # noqa: E402


def main() -> int:
    evidence = ROOT / "docs" / "evidence" / "v17" / "collab"
    fixtures = ROOT / "var" / "mac-connector" / "fixtures"
    report = asyncio.run(
        run_collab_connector_campaign(evidence_dir=evidence, fixture_dir=fixtures)
    )
    print(json.dumps({"ok": report.ok, "mission_id": report.mission_id}, indent=2))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
