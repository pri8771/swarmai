"""Frozen G13 structured size classifier, version 3 (EVAL-131 size bands)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

CLASSIFIER_ID: Final[str] = "g13-size-classifier-v3"
SIZE_BANDS: Final[tuple[str, ...]] = ("S", "M", "L", "XL")
FEATURE_SCHEMA: Final[tuple[str, ...]] = (
    "entity_count",
    "constraint_count",
    "dependency_depth",
    "output_field_count",
    "distractor_count",
)
FEATURE_WEIGHTS: Final[dict[str, int]] = {
    "entity_count": 1,
    "constraint_count": 1,
    "dependency_depth": 2,
    "output_field_count": 1,
    "distractor_count": 1,
}
LOAD_BANDS: Final[tuple[int, int, int]] = (8, 14, 21)
DECISION_FEATURE: Final[str] = "structural_load"


class SizeClassifierV3Error(ValueError):
    """Raised when a visible payload cannot be measured by this classifier."""


@dataclass(frozen=True)
class StructuredFeatures:
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
            raise SizeClassifierV3Error(f"{where}: required collection is absent")
        return []
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise SizeClassifierV3Error(f"{where}: expected an array, got {type(value).__name__}")
    return list(value)


def _edge_pair(raw: Any, where: str) -> tuple[str, str]:
    pair = _as_sequence(raw, where, required=True)
    if len(pair) != 2:
        raise SizeClassifierV3Error(f"{where}: dependency edge must have exactly 2 endpoints")
    first, second = pair
    if not isinstance(first, str) or not isinstance(second, str):
        raise SizeClassifierV3Error(f"{where}: dependency endpoints must be strings")
    if first == second:
        raise SizeClassifierV3Error(f"{where}: self-dependency {first!r}")
    return first, second


def dependency_edges(visible_input: Mapping[str, Any]) -> list[tuple[str, str]]:
    raw = _as_sequence(visible_input.get("dependencies"), "input.dependencies", required=False)
    return [_edge_pair(edge, f"input.dependencies[{i}]") for i, edge in enumerate(raw)]


def longest_dependency_path(edges: Sequence[tuple[str, str]]) -> int:
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
            raise SizeClassifierV3Error(f"input.dependencies: cycle through {node!r}")
        visiting.add(node)
        best = 0
        for nxt in successors.get(node, ()):
            best = max(best, 1 + walk(nxt))
        visiting.discard(node)
        depth[node] = best
        return best

    return max(walk(node) for node in sorted(nodes))


def derive_features(visible_input: Mapping[str, Any]) -> StructuredFeatures:
    contract = visible_input.get("output_contract")
    if not isinstance(contract, Mapping):
        raise SizeClassifierV3Error("input.output_contract: expected an object")
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
    small, medium, large = LOAD_BANDS
    if structural_load <= small:
        return "S"
    if structural_load <= medium:
        return "M"
    if structural_load <= large:
        return "L"
    return "XL"


def classify(visible_input: Mapping[str, Any]) -> str:
    return classify_load(derive_features(visible_input).structural_load())


def classifier_identity() -> dict[str, Any]:
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
