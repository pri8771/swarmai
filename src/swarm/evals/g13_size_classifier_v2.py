"""Frozen G13 **structured** size classifier, version 2 (EVAL-131 size bands).

Why a v2 classifier
-------------------
``g13-size-classifier-v1`` bucketed on ``size_features.input_tokens_estimate``,
a number *declared* on each record by the pool generator. That is a second
source of truth: nothing stopped a record from declaring a token estimate that
did not describe its own payload, and the classifier could not tell.

``g13-size-classifier-v2`` removes the declaration entirely. It **derives** its
feature vector from the model-visible structured payload, so a record cannot
misdescribe its own size. Records in ``g13-pool-freeze-v2`` therefore carry no
``size_features`` block at all; they carry only the band label ``size``, and the
verifier asserts that this classifier reproduces it.

Feature vector
--------------
Every model-visible payload in the v2 corpus is a structured object, not a prose
blob, so these counts are exact rather than estimated:

``entity_count``
    number of entries in ``input.items`` — the primary collection the task
    operates over.
``constraint_count``
    number of entries in ``input.constraints``.
``dependency_depth``
    number of edges on the longest path through ``input.dependencies``
    (``0`` when the family declares no dependency graph).
``output_field_count``
    number of entries in ``input.output_contract.fields``.
``distractor_count``
    number of entries in ``input.distractors``.

Decision
--------
The bands cut on a single scalar, ``structural_load``, a fixed weighted sum of
the feature vector. ``dependency_depth`` carries weight 2 because one extra
level of a dependency chain costs more reasoning than one extra flat entity;
every other feature carries weight 1. Boundaries are **global**, not per family:
v1 needed per-family bounds because it cut on a generator-declared token
estimate whose scale differed wildly between families, whereas
``structural_load`` is measured in comparable units (countable payload elements)
across all families.

Boundaries are inclusive upper bounds; anything above the ``L`` bound is ``XL``.

Changing ``CLASSIFIER_ID``, ``FEATURE_SCHEMA``, ``FEATURE_WEIGHTS`` or
``LOAD_BANDS`` is a breaking change: mint a new classifier id *and* a new pool
freeze version.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

CLASSIFIER_ID: Final[str] = "g13-size-classifier-v2"

SIZE_BANDS: Final[tuple[str, ...]] = ("S", "M", "L", "XL")

#: Ordered structured feature schema, all derived from the visible payload.
FEATURE_SCHEMA: Final[tuple[str, ...]] = (
    "entity_count",
    "constraint_count",
    "dependency_depth",
    "output_field_count",
    "distractor_count",
)

#: Fixed weights applied to the feature vector to obtain ``structural_load``.
FEATURE_WEIGHTS: Final[dict[str, int]] = {
    "entity_count": 1,
    "constraint_count": 1,
    "dependency_depth": 2,
    "output_field_count": 1,
    "distractor_count": 1,
}

#: Inclusive upper bounds on ``structural_load`` for (S, M, L). Above L is XL.
LOAD_BANDS: Final[tuple[int, int, int]] = (8, 14, 21)

DECISION_FEATURE: Final[str] = "structural_load"


class SizeClassifierV2Error(ValueError):
    """Raised when a visible payload cannot be measured by this classifier."""


@dataclass(frozen=True)
class StructuredFeatures:
    """Exact structural counts derived from one model-visible payload."""

    entity_count: int
    constraint_count: int
    dependency_depth: int
    output_field_count: int
    distractor_count: int

    def as_dict(self) -> dict[str, int]:
        return {
            "entity_count": self.entity_count,
            "constraint_count": self.constraint_count,
            "dependency_depth": self.dependency_depth,
            "output_field_count": self.output_field_count,
            "distractor_count": self.distractor_count,
        }

    def structural_load(self) -> int:
        counts = self.as_dict()
        return sum(FEATURE_WEIGHTS[name] * counts[name] for name in FEATURE_SCHEMA)


def _as_sequence(value: Any, where: str, *, required: bool) -> list[Any]:
    if value is None:
        if required:
            raise SizeClassifierV2Error(f"{where}: required collection is absent")
        return []
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise SizeClassifierV2Error(f"{where}: expected an array, got {type(value).__name__}")
    return list(value)


def _edge_pair(raw: Any, where: str) -> tuple[str, str]:
    pair = _as_sequence(raw, where, required=True)
    if len(pair) != 2:
        raise SizeClassifierV2Error(f"{where}: dependency edge must have exactly 2 endpoints")
    first, second = pair
    if not isinstance(first, str) or not isinstance(second, str):
        raise SizeClassifierV2Error(f"{where}: dependency endpoints must be strings")
    if first == second:
        raise SizeClassifierV2Error(f"{where}: self-dependency {first!r}")
    return first, second


def dependency_edges(visible_input: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Normalised ``[[before, after], ...]`` edge list of the visible payload."""
    raw = _as_sequence(visible_input.get("dependencies"), "input.dependencies", required=False)
    return [_edge_pair(edge, f"input.dependencies[{i}]") for i, edge in enumerate(raw)]


def longest_dependency_path(edges: Sequence[tuple[str, str]]) -> int:
    """Edge count of the longest path through ``edges``; 0 for an empty graph.

    Raises when the graph contains a cycle: a dependency cycle makes the size
    band undefined and must fail the freeze rather than be silently measured.
    """
    if not edges:
        return 0
    successors: dict[str, list[str]] = {}
    nodes: set[str] = set()
    for before, after in edges:
        successors.setdefault(before, []).append(after)
        nodes.add(before)
        nodes.add(after)

    depth: dict[str, int] = {}
    visiting: set[str] = set()

    def walk(node: str) -> int:
        cached = depth.get(node)
        if cached is not None:
            return cached
        if node in visiting:
            raise SizeClassifierV2Error(f"input.dependencies: cycle through {node!r}")
        visiting.add(node)
        best = 0
        for nxt in successors.get(node, ()):
            best = max(best, 1 + walk(nxt))
        visiting.discard(node)
        depth[node] = best
        return best

    return max(walk(node) for node in sorted(nodes))


def derive_features(visible_input: Mapping[str, Any]) -> StructuredFeatures:
    """Derive the exact structured feature vector from a visible payload."""
    contract = visible_input.get("output_contract")
    if not isinstance(contract, Mapping):
        raise SizeClassifierV2Error("input.output_contract: expected an object")
    return StructuredFeatures(
        entity_count=len(_as_sequence(visible_input.get("items"), "input.items", required=True)),
        constraint_count=len(
            _as_sequence(visible_input.get("constraints"), "input.constraints", required=True)
        ),
        dependency_depth=longest_dependency_path(dependency_edges(visible_input)),
        output_field_count=len(
            _as_sequence(contract.get("fields"), "input.output_contract.fields", required=True)
        ),
        distractor_count=len(
            _as_sequence(visible_input.get("distractors"), "input.distractors", required=False)
        ),
    )


def classify_load(structural_load: int) -> str:
    """Return the frozen size band for a ``structural_load`` value."""
    small, medium, large = LOAD_BANDS
    if structural_load <= small:
        return "S"
    if structural_load <= medium:
        return "M"
    if structural_load <= large:
        return "L"
    return "XL"


def classify(visible_input: Mapping[str, Any]) -> str:
    """Return the frozen size band of a model-visible payload."""
    return classify_load(derive_features(visible_input).structural_load())


def classifier_identity() -> dict[str, Any]:
    """Serialisable identity of the frozen v2 classifier, for manifests."""
    small, medium, large = LOAD_BANDS
    return {
        "classifier_id": CLASSIFIER_ID,
        "feature_source": "derived_from_model_visible_payload",
        "feature_schema": list(FEATURE_SCHEMA),
        "feature_weights": {name: FEATURE_WEIGHTS[name] for name in FEATURE_SCHEMA},
        "decision_feature": DECISION_FEATURE,
        "decision_formula": "sum(FEATURE_WEIGHTS[f] * features[f] for f in FEATURE_SCHEMA)",
        "size_bands": list(SIZE_BANDS),
        "boundary_kind": "inclusive_upper_bound_global",
        "load_bands": {
            "S_max": small,
            "M_max": medium,
            "L_max": large,
            "XL": f"> {large}",
        },
        "records_declare_features": False,
    }
