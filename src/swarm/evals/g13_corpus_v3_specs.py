"""Unique G13 v3 held-out/calibration task specifications."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

PRODUCT_FAMILIES: Final[tuple[str, ...]] = ("coding", "planning", "reasoning", "extraction")
SIZE_BANDS: Final[tuple[str, ...]] = ("S", "M", "L", "XL")
DATASET_FAMILY: Final[dict[str, str]] = {
    "coding": "code_generation",
    "planning": "dependency_planning",
    "reasoning": "evidence_qa",
    "extraction": "extraction",
}

_OBJECTIVES_PATH = Path(__file__).with_name("g13_corpus_v3_objectives.json")


def _load_objectives() -> dict[str, dict[str, tuple[tuple[str, str], ...]]]:
    raw = json.loads(_OBJECTIVES_PATH.read_text(encoding="utf-8"))
    loaded: dict[str, dict[str, tuple[tuple[str, str], ...]]] = {}
    for family, sizes in raw.items():
        loaded[family] = {}
        for size, pairs in sizes.items():
            loaded[family][size] = tuple((str(slug), str(desc)) for slug, desc in pairs)
    return loaded


CELL_OBJECTIVES: Final[dict[str, dict[str, tuple[tuple[str, str], ...]]]] = _load_objectives()


def _assert_unique() -> None:
    for family, sizes in CELL_OBJECTIVES.items():
        seen: set[str] = set()
        for size, pairs in sizes.items():
            if len(pairs) != 15:
                raise RuntimeError(f"{family}/{size} has {len(pairs)} objectives, need 15")
            for slug, _desc in pairs:
                key = f"{family}/{slug}"
                if key in seen:
                    raise RuntimeError(f"duplicate objective {key}")
                seen.add(key)
    total = sum(len(pairs) for sizes in CELL_OBJECTIVES.values() for pairs in sizes.values())
    if total != 240:
        raise RuntimeError(f"expected 240 unique holdout objectives, got {total}")


_assert_unique()
