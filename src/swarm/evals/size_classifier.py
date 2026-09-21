"""Frozen G13 size classifier (EVAL-131 structured-feature size bands).

The EVAL-131 protocol binds every observation to an explicit size band. This
module freezes *how* a band is derived from the structured features carried by
each frozen pool record, so later observations can be bound to a stable
classifier identity instead of an undocumented convention.

Design notes
------------
* The classifier is **declarative**: it reads the structured features already
  persisted on each frozen case (``size_features``) and buckets them. It does
  not re-derive character/token counts from prompt text, because the pool
  generator (``seed-v1``) owns that derivation and re-deriving it here would
  silently fork two definitions of the same number.
* Boundaries are **per product/dataset family**. A single global threshold table
  cannot separate the bands: e.g. ``dependency_planning`` XL (471-535 estimated
  tokens) sits below ``classification`` L (538), so a global cut would mislabel
  both families.
* Boundaries are inclusive upper bounds on the decision feature. Anything above
  the ``L`` bound is ``XL``.

Changing ``CLASSIFIER_ID``, ``FEATURE_SCHEMA``, ``DECISION_FEATURE`` or
``FAMILY_BANDS`` is a breaking change: mint a new classifier id *and* a new pool
freeze version, and re-run
``scripts/g13_freeze_task_pool.py`` so the frozen manifest is regenerated.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

CLASSIFIER_ID: Final[str] = "g13-size-classifier-v1"

SIZE_BANDS: Final[tuple[str, ...]] = ("S", "M", "L", "XL")

#: Ordered structured feature schema persisted with every frozen case.
FEATURE_SCHEMA: Final[tuple[str, ...]] = (
    "input_characters",
    "input_tokens_estimate",
    "entity_count",
    "dependency_depth",
    "file_count",
    "tool_steps",
)

#: The single feature the frozen v1 classifier cuts on. The remaining schema
#: fields are carried (and frozen) for later classifier versions and for
#: ``max_supported_features`` reasoning, but do not affect the v1 decision.
DECISION_FEATURE: Final[str] = "input_tokens_estimate"

#: Inclusive upper bounds on ``DECISION_FEATURE`` for (S, M, L). Above the L
#: bound is XL. Derived as the floor of the midpoint between the highest
#: observed value of a band and the lowest observed value of the next band in
#: the frozen pool, per family.
FAMILY_BANDS: Final[dict[str, tuple[int, int, int]]] = {
    "classification": (205, 404, 779),
    "code_generation": (232, 404, 866),
    "code_repair": (216, 355, 621),
    "context_compaction": (252, 458, 843),
    "dependency_planning": (113, 205, 381),
    "evidence_qa": (347, 716, 1415),
    "extraction": (184, 341, 634),
    "tool_selection": (257, 418, 731),
}


class SizeClassifierError(ValueError):
    """Raised when structured features are missing, malformed, or unmapped."""


@dataclass(frozen=True)
class SizeFeatureVector:
    """Structured features required by EVAL-131 for a single frozen case."""

    input_characters: int
    input_tokens_estimate: int
    entity_count: int
    dependency_depth: int
    file_count: int
    tool_steps: int

    def as_dict(self) -> dict[str, int]:
        return {
            "input_characters": self.input_characters,
            "input_tokens_estimate": self.input_tokens_estimate,
            "entity_count": self.entity_count,
            "dependency_depth": self.dependency_depth,
            "file_count": self.file_count,
            "tool_steps": self.tool_steps,
        }

    def decision_value(self) -> int:
        return self.as_dict()[DECISION_FEATURE]


def _require_int(raw: Mapping[str, Any], key: str) -> int:
    if key not in raw:
        raise SizeClassifierError(f"missing structured feature {key!r}")
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise SizeClassifierError(f"structured feature {key!r} must be an int, got {value!r}")
    return value


def feature_vector(raw: Mapping[str, Any]) -> SizeFeatureVector:
    """Build a feature vector from a frozen case's ``size_features`` mapping."""
    return SizeFeatureVector(
        input_characters=_require_int(raw, "input_characters"),
        input_tokens_estimate=_require_int(raw, "input_tokens_estimate"),
        entity_count=_require_int(raw, "entity_count"),
        dependency_depth=_require_int(raw, "dependency_depth"),
        file_count=_require_int(raw, "file_count"),
        tool_steps=_require_int(raw, "tool_steps"),
    )


def classify(family: str, features: SizeFeatureVector) -> str:
    """Return the frozen size band for ``family`` given structured features."""
    bands = FAMILY_BANDS.get(family)
    if bands is None:
        raise SizeClassifierError(
            f"family {family!r} has no frozen size bands; add it to FAMILY_BANDS and "
            "mint a new classifier id"
        )
    value = features.decision_value()
    small, medium, large = bands
    if value <= small:
        return "S"
    if value <= medium:
        return "M"
    if value <= large:
        return "L"
    return "XL"


def classifier_identity() -> dict[str, Any]:
    """Serialisable identity of the frozen classifier, for manifests/receipts."""
    return {
        "classifier_id": CLASSIFIER_ID,
        "feature_schema": list(FEATURE_SCHEMA),
        "decision_feature": DECISION_FEATURE,
        "size_bands": list(SIZE_BANDS),
        "boundary_kind": "inclusive_upper_bound_per_family",
        "family_bands": {
            family: {
                "S_max": bands[0],
                "M_max": bands[1],
                "L_max": bands[2],
                "XL": f"> {bands[2]}",
            }
            for family, bands in sorted(FAMILY_BANDS.items())
        },
    }
