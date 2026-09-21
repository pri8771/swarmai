"""ART-V13-TASK-POOL — frozen G13 calibration / held-out pool verification.

This module is the executable half of the G13 task-pool freeze. The declarative
half lives under ``benchmarks/g13/pool_freeze_v1/``:

``task_pool_freeze_v1.manifest.json``
    The frozen manifest: split membership, coverage, source/licence metadata,
    and the identity bindings (size classifier, scorer, prompt, tool protocol,
    exact model-configuration schema) that later EVAL-131 observations must
    quote.
``POOL_RECORD_DIGESTS.txt``
    One ``<case_id> <sha256> *-`` line per frozen record, in dataset file
    order. The digest input is the exact JSONL record line **including** its
    terminating ``LF``.

Why derived digests are not stored
----------------------------------
The manifest pins the whole-file digest of the pool *and* a per-record digest
for every record. Any digest derived from a record (visible prompt, hidden
answer, normalised template) is a pure function of those frozen bytes, so it is
already pinned transitively. Storing it again would only create a second place
to drift. The verifier therefore recomputes derived digests at verification time
and checks the contamination boundary directly.

Nothing here runs a model, and nothing here counts towards qualification.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.evals.dataset import build_model_input
from swarm.evals.size_classifier import (
    CLASSIFIER_ID,
    classify,
    feature_vector,
)

FREEZE_ID = "g13-pool-freeze-v1"
FREEZE_DIR = Path("benchmarks") / "g13" / "pool_freeze_v1"
MANIFEST_NAME = "task_pool_freeze_v1.manifest.json"
RECORD_DIGESTS_NAME = "POOL_RECORD_DIGESTS.txt"
CHECKSUMS_NAME = "SHA256SUMS"

CALIBRATION_SPLIT = "calibration"
HELD_OUT_SPLIT = "holdout"

#: Header of the record digest sidecar, reproduced byte-for-byte on regeneration.
DIGEST_HEADER: tuple[str, ...] = (
    "# g13-pool-freeze-v1 record digests",
    "# format: <case_id> <sha256-hex> *-",
    "# digest input: exact bytes of the JSONL record line in benchmarks/starter.jsonl"
    " INCLUDING its terminating LF",
    "# order: dataset file order (line 1..224); line N of the dataset -> Nth"
    " non-comment line here",
)

#: Fields of a frozen record that must never reach the worker or the model.
HIDDEN_FIELDS: tuple[str, ...] = (
    "expected_output",
    "grader",
    "reference_solution",
    "broken_code",
)

#: Values that mark an unfinished ("floating") manifest.
FLOATING_VALUES: frozenset[str] = frozenset(
    {"", "tbd", "todo", "unknown", "null", "none", "n/a", "fixme", "<fill>", "changeme"}
)

_DIGIT_RUN = re.compile(r"\d+")


class PoolFreezeError(ValueError):
    """Raised when the frozen pool artefacts cannot be parsed at all."""


@dataclass(frozen=True)
class Violation:
    """A single freeze-integrity failure."""

    code: str
    detail: str

    def __str__(self) -> str:  # pragma: no cover - formatting helper
        return f"{self.code}: {self.detail}"


@dataclass
class FreezeVerification:
    """Result of verifying the frozen pool against the repository."""

    violations: list[Violation] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.violations

    def add(self, code: str, detail: str) -> None:
        self.violations.append(Violation(code=code, detail=detail))

    def report(self) -> str:
        if self.ok:
            return "pool freeze OK"
        return "pool freeze violations:\n" + "\n".join(f"  - {v}" for v in self.violations)


# --------------------------------------------------------------------------
# primitives
# --------------------------------------------------------------------------


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def record_digest(line: str) -> str:
    """Digest of one JSONL record line, including its terminating ``LF``."""
    return sha256_hex((line + "\n").encode("utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def visible_prompt_digest(record: Mapping[str, Any]) -> str:
    """Digest of exactly the model-visible payload of a frozen record."""
    visible = build_model_input(dict(record))
    return sha256_hex(canonical_json(visible).encode("utf-8"))


def template_digest(record: Mapping[str, Any]) -> str:
    """Digest of the model-visible payload with every digit run normalised.

    Two records with the same template digest are seed-isomorphic: identical
    structure, different synthetic identifiers. This is *reported*, never
    enforced — the seeded generator produces isomorphic variants by design.
    """
    visible = build_model_input(dict(record))
    flattened = _DIGIT_RUN.sub("#", canonical_json(visible))
    return sha256_hex(flattened.encode("utf-8"))


# --------------------------------------------------------------------------
# typed JSON access (mypy-strict friendly)
# --------------------------------------------------------------------------


def _as_dict(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PoolFreezeError(f"{where}: expected object, got {type(value).__name__}")
    return {str(k): v for k, v in value.items()}


def _as_list(value: Any, where: str) -> list[Any]:
    if not isinstance(value, list):
        raise PoolFreezeError(f"{where}: expected array, got {type(value).__name__}")
    return list(value)


def _as_str(value: Any, where: str) -> str:
    if not isinstance(value, str):
        raise PoolFreezeError(f"{where}: expected string, got {type(value).__name__}")
    return value


def _as_int(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PoolFreezeError(f"{where}: expected integer, got {type(value).__name__}")
    return value


def _get(mapping: Mapping[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise PoolFreezeError(f"{where}: missing required key {key!r}")
    return mapping[key]


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------


def manifest_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / FREEZE_DIR / MANIFEST_NAME


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise PoolFreezeError(f"manifest not found: {path}")
    return _as_dict(json.loads(path.read_text(encoding="utf-8")), str(path))


def load_record_digests(path: Path) -> list[tuple[str, str]]:
    """Parse ``<case_id> <sha256> *-`` lines, skipping ``#`` comments."""
    if not path.exists():
        raise PoolFreezeError(f"record digest file not found: {path}")
    rows: list[tuple[str, str]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            raise PoolFreezeError(f"{path}:{line_no}: malformed digest line {raw!r}")
        case_id, digest = parts[0], parts[1]
        if len(digest) != 64 or not all(c in "0123456789abcdef" for c in digest):
            raise PoolFreezeError(f"{path}:{line_no}: not a sha256 hex digest: {digest!r}")
        rows.append((case_id, digest))
    return rows


def load_pool_lines(path: Path) -> list[str]:
    """Raw JSONL record lines (no terminating newline) in file order.

    Read as bytes on purpose: ``read_text`` applies universal-newline
    translation, which would silently hide a CRLF pool from a byte-exact freeze.
    """
    if not path.exists():
        raise PoolFreezeError(f"pool source not found: {path}")
    text = path.read_bytes().decode("utf-8")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    else:
        raise PoolFreezeError(f"{path}: pool source must end with a single LF")
    return lines


# --------------------------------------------------------------------------
# floating / placeholder detection
# --------------------------------------------------------------------------


def find_floating_values(value: Any, path: str = "$") -> list[str]:
    """Return JSON paths whose value is a placeholder or an empty container."""
    found: list[str] = []
    if value is None:
        found.append(path)
    elif isinstance(value, str):
        if value.strip().lower() in FLOATING_VALUES:
            found.append(path)
    elif isinstance(value, dict):
        if not value:
            found.append(path)
        for key in sorted(str(k) for k in value):
            found.extend(find_floating_values(value[key], f"{path}.{key}"))
    elif isinstance(value, list):
        if not value:
            found.append(path)
        for index, item in enumerate(value):
            found.extend(find_floating_values(item, f"{path}[{index}]"))
    return found


def find_hidden_field_names(value: Any, path: str = "$") -> list[str]:
    """Return JSON paths where a hidden-answer field name is used as a key."""
    found: list[str] = []
    if isinstance(value, dict):
        for key in sorted(str(k) for k in value):
            child = f"{path}.{key}"
            if key in HIDDEN_FIELDS:
                found.append(child)
            found.extend(find_hidden_field_names(value[key], child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(find_hidden_field_names(item, f"{path}[{index}]"))
    return found


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------


def _index_manifest_cases(
    result: FreezeVerification, manifest: Mapping[str, Any]
) -> dict[str, dict[str, str]]:
    """Flatten ``splits.<split>.cells[].case_ids`` into a per-case index."""
    splits = _as_dict(_get(manifest, "splits", "$"), "$.splits")
    indexed: dict[str, dict[str, str]] = {}
    for split_name in sorted(splits):
        where_split = f"$.splits.{split_name}"
        block = _as_dict(splits[split_name], where_split)
        declared_total = _as_int(
            _get(block, "case_count", where_split), f"{where_split}.case_count"
        )
        cells = _as_list(_get(block, "cells", where_split), f"{where_split}.cells")
        seen_in_split = 0
        for position, raw_cell in enumerate(cells):
            where = f"{where_split}.cells[{position}]"
            cell = _as_dict(raw_cell, where)
            family = _as_str(_get(cell, "family", where), f"{where}.family")
            size = _as_str(_get(cell, "size", where), f"{where}.size")
            product_family = _as_str(
                _get(cell, "product_family", where), f"{where}.product_family"
            )
            case_ids = _as_list(_get(cell, "case_ids", where), f"{where}.case_ids")
            for case_id_raw in case_ids:
                case_id = _as_str(case_id_raw, f"{where}.case_ids[]")
                if case_id in indexed:
                    result.add("manifest_duplicate_case", f"{where}: {case_id} listed twice")
                    continue
                indexed[case_id] = {
                    "id": case_id,
                    "split": split_name,
                    "family": family,
                    "size": size,
                    "product_family": product_family,
                }
                seen_in_split += 1
        if seen_in_split != declared_total:
            result.add(
                "split_case_count_mismatch",
                f"{where_split}: declares {declared_total} cases, lists {seen_in_split}",
            )
    return indexed


def _check_pinned_files(
    result: FreezeVerification, root: Path, pinned: Mapping[str, Any], where: str
) -> None:
    for rel in sorted(pinned):
        expected = _as_str(pinned[rel], f"{where}.{rel}")
        target = root / rel
        if not target.exists():
            result.add("pinned_file_missing", f"{where}: {rel} does not exist")
            continue
        actual = file_digest(target)
        if actual != expected:
            result.add(
                "pinned_file_digest_mismatch",
                f"{where}: {rel} expected {expected} got {actual} "
                "(frozen identity changed — mint a new freeze version)",
            )


def _collect_identity_pins(manifest: Mapping[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    identities = _as_dict(_get(manifest, "identities", "$"), "$.identities")
    pins: list[tuple[str, dict[str, Any]]] = []
    for name in sorted(identities):
        block = _as_dict(identities[name], f"$.identities.{name}")
        raw = block.get("pinned_files")
        if raw is None:
            continue
        pins.append((f"$.identities.{name}.pinned_files", _as_dict(raw, name)))
    return pins


def _check_identity_specs(
    result: FreezeVerification, base: Path, manifest: Mapping[str, Any]
) -> None:
    """Every identity must point at a real, digest-pinned, non-floating spec file."""
    identities = _as_dict(_get(manifest, "identities", "$"), "$.identities")
    for name in sorted(identities):
        where = f"$.identities.{name}"
        block = _as_dict(identities[name], where)
        spec = _as_dict(_get(block, "spec", where), f"{where}.spec")
        rel = _as_str(_get(spec, "path", f"{where}.spec"), f"{where}.spec.path")
        expected = _as_str(_get(spec, "sha256", f"{where}.spec"), f"{where}.spec.sha256")
        target = base / rel
        if not target.exists():
            result.add("identity_spec_missing", f"{where}: {rel} does not exist")
            continue
        actual = file_digest(target)
        if actual != expected:
            result.add(
                "identity_spec_digest_mismatch",
                f"{where}: {rel} expected {expected} got {actual}",
            )
        payload = json.loads(target.read_text(encoding="utf-8"))
        for floating in find_floating_values(payload, f"{rel}$"):
            result.add("floating_identity_value", f"{floating} is empty/placeholder")
        for leaked in find_hidden_field_names(payload, f"{rel}$"):
            result.add("hidden_field_in_identity", f"{leaked} names a hidden-answer field")


def _required_cells(manifest: Mapping[str, Any]) -> list[tuple[str, str]]:
    coverage = _as_dict(_get(manifest, "coverage", "$"), "$.coverage")
    families = _as_list(
        _get(coverage, "required_product_families", "$.coverage"), "required_product_families"
    )
    sizes = _as_list(_get(coverage, "required_sizes", "$.coverage"), "required_sizes")
    return [
        (_as_str(f, "required_product_families[]"), _as_str(s, "required_sizes[]"))
        for f in families
        for s in sizes
    ]


def _counter_to_sorted(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def verify_pool_freeze(
    root: Path | None = None, *, manifest_file: Path | None = None
) -> FreezeVerification:
    """Deterministically verify the frozen pool. No model calls, no network."""
    base = root or repo_root()
    result = FreezeVerification()
    path = manifest_file or manifest_path(base)
    manifest = load_manifest(path)

    # --- manifest self-description -------------------------------------
    freeze_id = _as_str(_get(manifest, "freeze_id", "$"), "$.freeze_id")
    if freeze_id != FREEZE_ID:
        result.add("freeze_id_mismatch", f"expected {FREEZE_ID!r}, manifest says {freeze_id!r}")

    for floating in find_floating_values(manifest):
        result.add("floating_manifest_value", f"{floating} is empty/placeholder")

    for leaked in find_hidden_field_names(manifest):
        result.add("hidden_field_in_manifest", f"{leaked} names a hidden-answer field")

    # --- pool source ----------------------------------------------------
    pool = _as_dict(_get(manifest, "pool_source", "$"), "$.pool_source")
    pool_rel = _as_str(_get(pool, "path", "$.pool_source"), "$.pool_source.path")
    pool_path = base / pool_rel
    if not pool_path.exists():
        result.add("pool_source_missing", f"{pool_rel} does not exist")
        return result

    declared_pool_digest = _as_str(
        _get(pool, "sha256", "$.pool_source"), "$.pool_source.sha256"
    )
    actual_pool_digest = file_digest(pool_path)
    if actual_pool_digest != declared_pool_digest:
        result.add(
            "pool_source_digest_mismatch",
            f"{pool_rel} expected {declared_pool_digest} got {actual_pool_digest}",
        )

    lines = load_pool_lines(pool_path)
    declared_count = _as_int(
        _get(pool, "record_count", "$.pool_source"), "$.pool_source.record_count"
    )
    if len(lines) != declared_count:
        result.add(
            "pool_record_count_mismatch",
            f"{pool_rel} has {len(lines)} records, manifest declares {declared_count}",
        )

    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(lines, start=1):
        records.append(_as_dict(json.loads(line), f"{pool_rel}:{line_no}"))

    # --- record digest sidecar -----------------------------------------
    digest_block = _as_dict(
        _get(manifest, "record_digests", "$"), "$.record_digests"
    )
    digest_rel = _as_str(
        _get(digest_block, "path", "$.record_digests"), "$.record_digests.path"
    )
    digest_path = base / digest_rel
    declared_digest_file = _as_str(
        _get(digest_block, "sha256", "$.record_digests"), "$.record_digests.sha256"
    )
    if not digest_path.exists():
        result.add("record_digest_file_missing", f"{digest_rel} does not exist")
        return result
    if file_digest(digest_path) != declared_digest_file:
        result.add(
            "record_digest_file_mismatch",
            f"{digest_rel} expected {declared_digest_file} got {file_digest(digest_path)}",
        )

    digest_rows = load_record_digests(digest_path)
    if len(digest_rows) != len(lines):
        result.add(
            "record_digest_count_mismatch",
            f"{digest_rel} lists {len(digest_rows)} digests for {len(lines)} records",
        )

    digest_by_id: dict[str, str] = {}
    for index, (listed_id, listed_digest) in enumerate(digest_rows):
        if index >= len(lines):
            result.add("record_digest_extra", f"{digest_rel} line {index + 1}: {listed_id}")
            continue
        actual_id = _as_str(records[index].get("id"), f"{pool_rel}:{index + 1}.id")
        if listed_id != actual_id:
            result.add(
                "record_digest_order_mismatch",
                f"{digest_rel} position {index + 1} is {listed_id!r}, "
                f"{pool_rel} line {index + 1} is {actual_id!r}",
            )
            continue
        computed = record_digest(lines[index])
        if computed != listed_digest:
            result.add(
                "record_digest_mismatch",
                f"{actual_id}: expected {listed_digest} got {computed}",
            )
        digest_by_id[actual_id] = listed_digest

    # --- manifest case membership ---------------------------------------
    manifest_cases = _index_manifest_cases(result, manifest)
    dataset_ids = {
        _as_str(rec.get("id"), f"{pool_rel}:{i + 1}.id") for i, rec in enumerate(records)
    }
    for missing in sorted(dataset_ids - set(manifest_cases)):
        result.add("manifest_case_missing", f"{missing} is in the pool but not the manifest")
    for extra in sorted(set(manifest_cases) - dataset_ids):
        result.add("manifest_case_extra", f"{extra} is in the manifest but not the pool")

    product_family_of: dict[str, str] = {}
    for line_no, record in enumerate(records, start=1):
        case_id = _as_str(record.get("id"), f"{pool_rel}:{line_no}.id")
        entry = manifest_cases.get(case_id)
        if entry is None:
            continue
        product_family_of[case_id] = entry["product_family"]
        for key in ("family", "size", "split"):
            declared = entry[key]
            actual = _as_str(record.get(key), f"{pool_rel}:{line_no}.{key}")
            if declared != actual:
                result.add(
                    "manifest_case_field_mismatch",
                    f"{case_id}.{key}: manifest {declared!r} vs pool {actual!r}",
                )

    # --- contamination boundary -----------------------------------------
    by_split: dict[str, list[dict[str, Any]]] = {CALIBRATION_SPLIT: [], HELD_OUT_SPLIT: []}
    for line_no, record in enumerate(records, start=1):
        split = _as_str(record.get("split"), f"{pool_rel}:{line_no}.split")
        if split not in by_split:
            result.add("unknown_split", f"{pool_rel}:{line_no}: split {split!r}")
            continue
        by_split[split].append(record)

    calibration = by_split[CALIBRATION_SPLIT]
    held_out = by_split[HELD_OUT_SPLIT]

    calibration_ids = {str(r.get("id")) for r in calibration}
    held_out_ids = {str(r.get("id")) for r in held_out}
    for shared in sorted(calibration_ids & held_out_ids):
        result.add("split_id_overlap", f"{shared} appears in both splits")

    calibration_digests = {digest_by_id.get(str(r.get("id")), "") for r in calibration}
    held_out_digests = {digest_by_id.get(str(r.get("id")), "") for r in held_out}
    for shared_digest in sorted(d for d in calibration_digests & held_out_digests if d):
        result.add("split_record_digest_overlap", f"record digest {shared_digest} in both splits")

    calibration_prompts = {visible_prompt_digest(r): str(r.get("id")) for r in calibration}
    held_out_prompts = {visible_prompt_digest(r): str(r.get("id")) for r in held_out}
    for shared_prompt in sorted(set(calibration_prompts) & set(held_out_prompts)):
        result.add(
            "split_visible_prompt_overlap",
            f"{calibration_prompts[shared_prompt]} and {held_out_prompts[shared_prompt]} "
            "share an identical model-visible prompt",
        )

    duplicate_held_out = len(held_out) - len(set(held_out_prompts))
    if duplicate_held_out:
        result.add(
            "held_out_prompt_duplicate",
            f"{duplicate_held_out} held-out records share a model-visible prompt with "
            "another held-out record (distinct-case counting would be inflated)",
        )

    # --- size classifier identity ---------------------------------------
    identities = _as_dict(_get(manifest, "identities", "$"), "$.identities")
    classifier_block = _as_dict(
        _get(identities, "size_classifier", "$.identities"), "$.identities.size_classifier"
    )
    declared_classifier = _as_str(
        _get(classifier_block, "classifier_id", "$.identities.size_classifier"),
        "$.identities.size_classifier.classifier_id",
    )
    if declared_classifier != CLASSIFIER_ID:
        result.add(
            "size_classifier_id_mismatch",
            f"manifest {declared_classifier!r} vs code {CLASSIFIER_ID!r}",
        )
    for line_no, record in enumerate(records, start=1):
        case_id = _as_str(record.get("id"), f"{pool_rel}:{line_no}.id")
        family = _as_str(record.get("family"), f"{pool_rel}:{line_no}.family")
        declared_size = _as_str(record.get("size"), f"{pool_rel}:{line_no}.size")
        features = feature_vector(
            _as_dict(record.get("size_features"), f"{pool_rel}:{line_no}.size_features")
        )
        derived = classify(family, features)
        if derived != declared_size:
            result.add(
                "size_classifier_disagreement",
                f"{case_id}: declared {declared_size} but {CLASSIFIER_ID} derives "
                f"{derived} from decision feature value {features.decision_value()}",
            )

    # --- identity pins ----------------------------------------------------
    _check_identity_specs(result, base, manifest)
    for where, pinned in _collect_identity_pins(manifest):
        _check_pinned_files(result, base, pinned, where)

    # --- coverage and readiness -------------------------------------------
    held_out_cell_counts: Counter[str] = Counter()
    calibration_cell_counts: Counter[str] = Counter()
    for record in held_out:
        case_id = str(record.get("id"))
        pf = product_family_of.get(case_id)
        if pf:
            held_out_cell_counts[f"{pf}/{record.get('size')}"] += 1
    for record in calibration:
        case_id = str(record.get("id"))
        pf = product_family_of.get(case_id)
        if pf:
            calibration_cell_counts[f"{pf}/{record.get('size')}"] += 1

    readiness = _as_dict(
        _get(manifest, "qualification_readiness", "$"), "$.qualification_readiness"
    )
    min_per_cell = _as_int(
        _get(readiness, "protocol_min_distinct_per_cell", "$.qualification_readiness"),
        "protocol_min_distinct_per_cell",
    )
    max_per_cell = _as_int(
        _get(readiness, "protocol_max_distinct_per_cell", "$.qualification_readiness"),
        "protocol_max_distinct_per_cell",
    )
    frozen_per_cell = _as_int(
        _get(readiness, "frozen_held_out_per_required_cell", "$.qualification_readiness"),
        "frozen_held_out_per_required_cell",
    )

    gap_min = 0
    gap_max = 0
    for product_family, size in _required_cells(manifest):
        cell = f"{product_family}/{size}"
        count = held_out_cell_counts.get(cell, 0)
        if count == 0:
            result.add("required_cell_empty", f"{cell} has no held-out records")
        if count != frozen_per_cell:
            result.add(
                "required_cell_depth_mismatch",
                f"{cell} has {count} held-out records, manifest declares {frozen_per_cell}",
            )
        if calibration_cell_counts.get(cell, 0) == 0:
            result.add("required_cell_no_calibration", f"{cell} has no calibration records")
        gap_min += max(0, min_per_cell - count)
        gap_max += max(0, max_per_cell - count)

    declared_gap_min = _as_int(
        _get(readiness, "additional_held_out_cases_for_min_depth", "$.qualification_readiness"),
        "additional_held_out_cases_for_min_depth",
    )
    declared_gap_max = _as_int(
        _get(readiness, "additional_held_out_cases_for_max_depth", "$.qualification_readiness"),
        "additional_held_out_cases_for_max_depth",
    )
    if declared_gap_min != gap_min:
        result.add(
            "readiness_gap_mismatch",
            f"min-depth gap: manifest {declared_gap_min}, computed {gap_min}",
        )
    if declared_gap_max != gap_max:
        result.add(
            "readiness_gap_mismatch",
            f"max-depth gap: manifest {declared_gap_max}, computed {gap_max}",
        )

    # --- statistics (reported, never enforced) ----------------------------
    calibration_templates = {template_digest(r) for r in calibration}
    held_out_templates = {template_digest(r) for r in held_out}
    result.stats = {
        "freeze_id": freeze_id,
        "pool_sha256": actual_pool_digest,
        "record_count": len(records),
        "calibration_count": len(calibration),
        "held_out_count": len(held_out),
        "held_out_per_required_cell": _counter_to_sorted(held_out_cell_counts),
        "calibration_per_required_cell": _counter_to_sorted(calibration_cell_counts),
        "distinct_calibration_templates": len(calibration_templates),
        "distinct_held_out_templates": len(held_out_templates),
        "cross_split_template_isomorphs": len(calibration_templates & held_out_templates),
        "additional_held_out_cases_for_min_depth": gap_min,
        "additional_held_out_cases_for_max_depth": gap_max,
    }
    return result


def verify_checksums(root: Path | None = None) -> FreezeVerification:
    """Verify the ``SHA256SUMS`` sidecar covering every frozen artefact file."""
    base = root or repo_root()
    result = FreezeVerification()
    sums_path = base / FREEZE_DIR / CHECKSUMS_NAME
    if not sums_path.exists():
        result.add("checksums_missing", f"{sums_path} does not exist")
        return result
    listed: dict[str, str] = {}
    for line_no, raw in enumerate(sums_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise PoolFreezeError(f"{sums_path}:{line_no}: malformed line {raw!r}")
        listed[parts[1].lstrip("*").strip()] = parts[0]
    for name in sorted(listed):
        target = base / FREEZE_DIR / name
        if not target.exists():
            result.add("checksum_target_missing", name)
            continue
        actual = file_digest(target)
        if actual != listed[name]:
            result.add("checksum_mismatch", f"{name}: expected {listed[name]} got {actual}")
    on_disk = {
        p.name
        for p in (base / FREEZE_DIR).iterdir()
        if p.is_file() and p.name != CHECKSUMS_NAME
    }
    for uncovered in sorted(on_disk - set(listed)):
        result.add("checksum_uncovered_file", uncovered)
    result.stats = {"covered_files": len(listed)}
    return result


def iter_frozen_artifact_files(root: Path | None = None) -> Iterable[Path]:
    base = (root or repo_root()) / FREEZE_DIR
    return sorted(p for p in base.iterdir() if p.is_file())


# --------------------------------------------------------------------------
# regeneration (used by scripts/g13_freeze_task_pool.py and by the tests)
# --------------------------------------------------------------------------


def render_record_digests(pool_path: Path) -> str:
    """Render the record digest sidecar exactly as it is committed."""
    rendered = list(DIGEST_HEADER)
    for line_no, line in enumerate(load_pool_lines(pool_path), start=1):
        record = _as_dict(json.loads(line), f"{pool_path}:{line_no}")
        case_id = _as_str(record.get("id"), f"{pool_path}:{line_no}.id")
        rendered.append(f"{case_id} {record_digest(line)} *-")
    return "\n".join(rendered) + "\n"


def render_checksums(root: Path | None = None) -> str:
    """Render a ``sha256sum``-compatible cover file for the freeze directory."""
    freeze_dir = (root or repo_root()) / FREEZE_DIR
    names = sorted(
        p.name for p in freeze_dir.iterdir() if p.is_file() and p.name != CHECKSUMS_NAME
    )
    return "".join(f"{file_digest(freeze_dir / name)} *{name}\n" for name in names)
