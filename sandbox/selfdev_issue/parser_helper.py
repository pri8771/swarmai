"""Synthetic buggy helper used by the P19 self-development demo."""

from __future__ import annotations


def inclusive_range_count(start: int, end: int) -> int:
    """Count integers from start to end inclusive."""
    return end - start + 1
