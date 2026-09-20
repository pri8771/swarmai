"""Regression tests for the synthetic parser demo."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_parser():
    path = Path(__file__).with_name("parser.py")
    spec = importlib.util.spec_from_file_location("demo_parser", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_reproduces_trailing_field_bug() -> None:
    """Fails on buggy baseline; passes after correct patch."""
    mod = _load_parser()
    assert mod.parse_csv_line("a,b,c") == ["a", "b", "c"]


def test_empty_fields() -> None:
    mod = _load_parser()
    assert mod.parse_csv_line("a,,c") == ["a", "", "c"]
