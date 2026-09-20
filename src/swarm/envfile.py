"""Load repo `.env` into process env without logging values."""

from __future__ import annotations

import os
from pathlib import Path


def load_repo_dotenv(repo_root: Path | None = None) -> int:
    """Apply KEY=VALUE pairs from `.env` when the key is unset.

    Never prints or returns secret values. Returns count of keys applied.
    """
    root = repo_root or Path(__file__).resolve().parents[2]
    path = root / ".env"
    if not path.is_file():
        return 0
    applied = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value
        applied += 1
    return applied
