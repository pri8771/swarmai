"""Wilson score interval lower bound for binomial proportions."""

from __future__ import annotations

import math


def wilson_lower_bound(successes: int, n: int, z: float = 1.96) -> float | None:
    """Wilson 95% lower bound (default z=1.96). Returns None when n==0."""
    if n <= 0:
        return None
    if successes < 0 or successes > n:
        raise ValueError("successes must be in [0, n]")
    p = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = p + z2 / (2.0 * n)
    margin = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n)
    return (centre - margin) / denom
