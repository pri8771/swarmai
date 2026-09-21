"""ART-V13-TASK-POOL — deterministic verification of the frozen G13 pool.

Two halves:

* the committed freeze must verify clean, regenerate byte-identically, and leak
  no hidden answer;
* the verifier must actually *catch* the failures it claims to catch. The
  negative cases below build a tiny synthetic freeze under ``tmp_path`` and
  break it one way at a time. Those fixtures are test-only scaffolding and are
  never qualification evidence.

No model call, no network, no counted observation.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from swarm.evals.size_classifier import CLASSIFIER_ID, classifier_identity
from swarm.evals.task_pool_freeze import (
    CHECKSUMS_NAME,
    FREEZE_DIR,
    MANIFEST_NAME,
    RECORD_DIGESTS_NAME,
    canonical_json,
    file_digest,
    find_hidden_field_names,
    load_pool_lines,
    manifest_path,
    record_digest,
    render_checksums,
    render_record_digests,
    verify_checksums,
    verify_pool_freeze,
)

REPO = Path(__file__).resolve().parents[2]
FREEZE = REPO / FREEZE_DIR


# ---------------------------------------------------------------------------
# the committed freeze
# ---------------------------------------------------------------------------


def test_committed_freeze_verifies_clean() -> None:
    result = verify_pool_freeze(REPO)
    assert result.ok, result.report()


def test_committed_checksums_cover_every_frozen_file() -> None:
    result = verify_checksums(REPO)
    assert result.ok, result.report()


def test_record_digest_sidecar_regenerates_byte_identically() -> None:
    manifest = json.loads(manifest_path(REPO).read_text(encoding="utf-8"))
    pool = REPO / str(manifest["pool_source"]["path"])
    # Bytes, not read_text: a CRLF checkout must fail here, not be normalised away.
    expected = (FREEZE / RECORD_DIGESTS_NAME).read_bytes().decode("utf-8")
    assert render_record_digests(pool) == expected


def test_checksums_regenerate_byte_identically() -> None:
    expected = (FREEZE / CHECKSUMS_NAME).read_bytes().decode("utf-8")
    assert render_checksums(REPO) == expected


def test_size_classifier_spec_mirrors_the_module() -> None:
    spec = json.loads(
        (FREEZE / "identity_size_classifier_v1.json").read_text(encoding="utf-8")
    )
    assert spec["identity"] == classifier_identity()
    assert spec["identity"]["classifier_id"] == CLASSIFIER_ID


def test_required_coverage_is_complete() -> None:
    stats = verify_pool_freeze(REPO).stats
    per_cell = stats["held_out_per_required_cell"]
    for family in ("coding", "planning", "reasoning", "extraction"):
        for size in ("S", "M", "L", "XL"):
            assert per_cell[f"{family}/{size}"] == 5, f"{family}/{size}"


def test_frozen_files_never_name_a_hidden_answer_field() -> None:
    for path in sorted(FREEZE.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert find_hidden_field_names(payload) == [], path.name


def test_frozen_files_never_contain_a_hidden_reference_value() -> None:
    manifest = json.loads(manifest_path(REPO).read_text(encoding="utf-8"))
    pool = REPO / str(manifest["pool_source"]["path"])
    frozen_text = "\n".join(
        p.read_text(encoding="utf-8") for p in sorted(FREEZE.iterdir()) if p.is_file()
    )
    for line in load_pool_lines(pool):
        record = json.loads(line)
        for field in ("expected_output", "reference_solution", "broken_code"):
            value = record.get(field)
            if value is None:
                continue
            serialised = value if isinstance(value, str) else canonical_json(value)
            if len(serialised) > 20:
                assert serialised not in frozen_text, f"{record['id']}.{field} leaked"


# ---------------------------------------------------------------------------
# synthetic freeze fixtures (test-only; never qualification evidence)
# ---------------------------------------------------------------------------


def _record(case_id: str, split: str, seed: int) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "id": case_id,
        "family": "extraction",
        "size": "S",
        "split": split,
        "input": {"prompt": f"Extract record ORD-{seed:03d} and return JSON."},
        "expected_output": {"records": [{"id": f"ORD-{seed:03d}"}]},
        "size_features": {
            "input_characters": 532,
            "input_tokens_estimate": 133,
            "entity_count": 3,
            "dependency_depth": 0,
            "file_count": 1,
            "tool_steps": 0,
        },
    }


def _identity_stub(name: str, key: str, value: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "name": name,
        key: value,
        "note": "test-only synthetic identity stub",
    }


def _write_freeze(root: Path, records: list[dict[str, Any]]) -> Path:
    """Materialise a minimal, self-consistent freeze and return its manifest."""
    pool = root / "pool.jsonl"
    lines = [canonical_json(r) for r in records]
    pool.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8", newline="")

    digests = root / "digests.txt"
    digests.write_text(
        "# test-only synthetic freeze\n"
        + "".join(
            f"{r['id']} {record_digest(line)} *-\n"
            for r, line in zip(records, lines, strict=True)
        ),
        encoding="utf-8",
        newline="",
    )

    identity_specs = {
        "size_classifier": ("identity_size_classifier.json", "classifier_id", CLASSIFIER_ID),
        "scorer": ("identity_scorer.json", "scorer_id", "g13-scorer-v1"),
        "prompt": ("identity_prompt.json", "prompt_id", "g13-prompt-v1"),
        "tool_protocol": ("identity_tool_protocol.json", "tool_protocol_id", "g13-tp-v1"),
        "model_config_schema": ("identity_model_config.json", "schema_id", "g13-emc-v1"),
    }
    identities: dict[str, Any] = {}
    for name, (filename, key, value) in identity_specs.items():
        spec_path = root / filename
        spec_path.write_text(
            json.dumps(_identity_stub(name, key, value), indent=2) + "\n",
            encoding="utf-8",
            newline="",
        )
        identities[name] = {
            key: value,
            "spec": {"path": filename, "sha256": file_digest(spec_path)},
        }

    calibration = [r["id"] for r in records if r["split"] == "calibration"]
    holdout = [r["id"] for r in records if r["split"] == "holdout"]
    manifest = {
        "schema_version": "1.0",
        "freeze_id": "g13-pool-freeze-v1",
        "pool_source": {
            "path": "pool.jsonl",
            "sha256": file_digest(pool),
            "record_count": len(records),
        },
        "record_digests": {"path": "digests.txt", "sha256": file_digest(digests)},
        "identities": identities,
        "coverage": {
            "required_product_families": ["extraction"],
            "required_sizes": ["S"],
        },
        "qualification_readiness": {
            "counted_qualification_ready": False,
            "protocol_min_distinct_per_cell": 15,
            "protocol_max_distinct_per_cell": 60,
            "frozen_held_out_per_required_cell": len(holdout),
            "additional_held_out_cases_for_min_depth": 15 - len(holdout),
            "additional_held_out_cases_for_max_depth": 60 - len(holdout),
        },
        "splits": {
            "calibration": {
                "purpose": "test-only calibration",
                "case_count": len(calibration),
                "cells": [
                    {
                        "product_family": "extraction",
                        "family": "extraction",
                        "size": "S",
                        "case_ids": calibration,
                    }
                ],
            },
            "holdout": {
                "purpose": "test-only holdout",
                "case_count": len(holdout),
                "cells": [
                    {
                        "product_family": "extraction",
                        "family": "extraction",
                        "size": "S",
                        "case_ids": holdout,
                    }
                ],
            },
        },
    }
    target = root / MANIFEST_NAME
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="")
    return target


def _default_records() -> list[dict[str, Any]]:
    return [
        _record("extraction_S_01", "calibration", 1),
        _record("extraction_S_02", "calibration", 2),
        _record("extraction_S_03", "holdout", 3),
        _record("extraction_S_04", "holdout", 4),
    ]


def _codes(root: Path, manifest: Path) -> set[str]:
    return {v.code for v in verify_pool_freeze(root, manifest_file=manifest).violations}


@pytest.fixture
def freeze(tmp_path: Path) -> tuple[Path, Path]:
    manifest = _write_freeze(tmp_path, _default_records())
    return tmp_path, manifest


def _rewrite_manifest(manifest: Path, mutate: Any) -> None:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    mutate(payload)
    manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="")


# ---------------------------------------------------------------------------
# the verifier must catch these
# ---------------------------------------------------------------------------


def test_synthetic_baseline_is_clean(freeze: tuple[Path, Path]) -> None:
    root, manifest = freeze
    result = verify_pool_freeze(root, manifest_file=manifest)
    assert result.ok, result.report()


def test_catches_calibration_holdout_id_overlap(tmp_path: Path) -> None:
    records = _default_records()
    # The same case id lands in both splits.
    records[2]["id"] = "extraction_S_01"
    manifest = _write_freeze(tmp_path, records)
    _rewrite_manifest(
        manifest,
        lambda m: m["splits"]["holdout"]["cells"][0]["case_ids"].__setitem__(
            0, "extraction_S_01"
        ),
    )
    codes = _codes(tmp_path, manifest)
    assert "split_id_overlap" in codes or "manifest_duplicate_case" in codes


def test_catches_identical_prompt_across_splits(tmp_path: Path) -> None:
    records = _default_records()
    # A held-out record reuses a calibration prompt verbatim.
    records[2]["input"] = dict(records[0]["input"])
    manifest = _write_freeze(tmp_path, records)
    assert "split_visible_prompt_overlap" in _codes(tmp_path, manifest)


def test_catches_duplicate_prompt_inside_holdout(tmp_path: Path) -> None:
    records = _default_records()
    records[3]["input"] = dict(records[2]["input"])
    manifest = _write_freeze(tmp_path, records)
    assert "held_out_prompt_duplicate" in _codes(tmp_path, manifest)


def test_catches_incomplete_manifest(freeze: tuple[Path, Path]) -> None:
    root, manifest = freeze
    _rewrite_manifest(manifest, lambda m: m["splits"]["holdout"]["cells"][0]["case_ids"].pop())
    codes = _codes(root, manifest)
    assert "manifest_case_missing" in codes
    assert "split_case_count_mismatch" in codes


def test_catches_extra_case_in_manifest(freeze: tuple[Path, Path]) -> None:
    root, manifest = freeze
    _rewrite_manifest(
        manifest,
        lambda m: m["splits"]["holdout"]["cells"][0]["case_ids"].append("extraction_S_99"),
    )
    assert "manifest_case_extra" in _codes(root, manifest)


def test_catches_floating_manifest_value(freeze: tuple[Path, Path]) -> None:
    root, manifest = freeze
    _rewrite_manifest(manifest, lambda m: m["splits"]["holdout"].__setitem__("purpose", "TBD"))
    assert "floating_manifest_value" in _codes(root, manifest)


def test_catches_null_manifest_value(freeze: tuple[Path, Path]) -> None:
    root, manifest = freeze
    _rewrite_manifest(manifest, lambda m: m["pool_source"].__setitem__("format", None))
    assert "floating_manifest_value" in _codes(root, manifest)


def test_catches_mutated_pool_record(freeze: tuple[Path, Path]) -> None:
    root, manifest = freeze
    pool = root / "pool.jsonl"
    lines = pool.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[3])
    record["input"]["prompt"] += " (silently edited)"
    lines[3] = canonical_json(record)
    pool.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8", newline="")
    codes = _codes(root, manifest)
    assert "pool_source_digest_mismatch" in codes
    assert "record_digest_mismatch" in codes


def test_catches_dropped_pool_record(freeze: tuple[Path, Path]) -> None:
    root, manifest = freeze
    pool = root / "pool.jsonl"
    lines = pool.read_text(encoding="utf-8").splitlines()[:-1]
    pool.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8", newline="")
    codes = _codes(root, manifest)
    assert "pool_record_count_mismatch" in codes
    assert "manifest_case_extra" in codes


def test_catches_floating_identity_pointer(freeze: tuple[Path, Path]) -> None:
    root, manifest = freeze
    (root / "identity_scorer.json").unlink()
    assert "identity_spec_missing" in _codes(root, manifest)


def test_catches_identity_spec_drift(freeze: tuple[Path, Path]) -> None:
    root, manifest = freeze
    spec = root / "identity_prompt.json"
    payload = json.loads(spec.read_text(encoding="utf-8"))
    payload["note"] = "quietly changed after freezing"
    spec.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="")
    assert "identity_spec_digest_mismatch" in _codes(root, manifest)


def test_catches_pinned_source_drift(freeze: tuple[Path, Path]) -> None:
    root, manifest = freeze
    decoy = root / "pinned_module.py"
    decoy.write_text("# original\n", encoding="utf-8", newline="")
    _rewrite_manifest(
        manifest,
        lambda m: m["identities"]["scorer"].__setitem__(
            "pinned_files", {"pinned_module.py": file_digest(decoy)}
        ),
    )
    assert verify_pool_freeze(root, manifest_file=manifest).ok
    decoy.write_text("# drifted\n", encoding="utf-8", newline="")
    assert "pinned_file_digest_mismatch" in _codes(root, manifest)


def test_catches_readiness_gap_drift(freeze: tuple[Path, Path]) -> None:
    root, manifest = freeze
    _rewrite_manifest(
        manifest,
        lambda m: m["qualification_readiness"].__setitem__(
            "additional_held_out_cases_for_min_depth", 0
        ),
    )
    assert "readiness_gap_mismatch" in _codes(root, manifest)


def test_catches_size_classifier_disagreement(tmp_path: Path) -> None:
    records = _default_records()
    # Declared S, but the structured features put it squarely in XL.
    records[3]["size_features"]["input_tokens_estimate"] = 5000
    manifest = _write_freeze(tmp_path, records)
    assert "size_classifier_disagreement" in _codes(tmp_path, manifest)


def test_catches_hidden_answer_field_in_manifest(freeze: tuple[Path, Path]) -> None:
    root, manifest = freeze
    _rewrite_manifest(
        manifest,
        lambda m: m["splits"]["holdout"].__setitem__(
            "expected_output", {"records": ["leaked"]}
        ),
    )
    assert "hidden_field_in_manifest" in _codes(root, manifest)


def test_catches_uncovered_or_drifted_checksums(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / FREEZE_DIR).mkdir(parents=True)
    shutil.copy(FREEZE / CHECKSUMS_NAME, root / FREEZE_DIR / CHECKSUMS_NAME)
    assert "checksum_target_missing" in {v.code for v in verify_checksums(root).violations}
    stray = root / FREEZE_DIR / "stray.json"
    stray.write_text("{}\n", encoding="utf-8", newline="")
    assert "checksum_uncovered_file" in {v.code for v in verify_checksums(root).violations}
