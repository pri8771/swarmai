"""Regression for synthetic parser helper (selfdev sample)."""

from __future__ import annotations

from parser_helper import inclusive_range_count


def test_inclusive_range_count() -> None:
    assert inclusive_range_count(1, 3) == 3
    assert inclusive_range_count(0, 0) == 1


if __name__ == "__main__":
    test_inclusive_range_count()
    print("ok")
