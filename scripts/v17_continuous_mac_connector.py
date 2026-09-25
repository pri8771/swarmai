#!/usr/bin/env python3
"""V1.7 continuous Mac connector entrypoint (not one-shot TH-03).

Enrolls, heartbeats, claims/renews/submits leased work, honors cancel/reconnect.
Never self-accepts results. Free/local only.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("SWARM_REPO_ROOT", str(ROOT))

from swarm.workers.continuous_connector import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
