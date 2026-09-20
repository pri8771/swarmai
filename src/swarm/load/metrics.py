"""Load-test metrics helpers (offline / mock)."""

from __future__ import annotations

from collections.abc import Sequence


def percentile(samples: Sequence[float], pct: float) -> float | None:
    if not samples:
        return None
    ordered = sorted(samples)
    if len(ordered) == 1:
        return ordered[0]
    idx = min(len(ordered) - 1, max(0, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return ordered[idx]
