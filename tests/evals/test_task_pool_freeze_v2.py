"""ART-V13-TASK-POOL — deterministic verification of ``g13-pool-freeze-v2``.

Two halves:

* the committed v2 freeze must verify clean, regenerate byte-identically, leak
  no answer, cover every required cell at depth >= 15, and refuse to resolve a
  hidden reference;
* the verifier must actually *catch* every failure it claims to catch. The
  negative cases build a complete synthetic freeze under ``tmp_path`` and break
  it one way at a time. Those fixtures are test-only scaffolding and are never
  qualification evidence.

No model call, no network, no counted observation.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from swarm.evals.g13_independence import (
    CHECKER_ID,
    IndependenceRecord,
    check_independence,
    checker_identity,
    normalise_template,
)
from swarm.evals.g13_prompt_v2 import (
    PROMPT_ID,
    PromptV2Error,
    find_denylisted_keys,
    prompt_identity,
    render_prompt,
    rendered_prompt_digest,
    sha256_hex,
    visible_input,
    visible_payload_digest,
)
from swarm.evals.g13_sealed_reference import (
    BUNDLE_ID,
    COMMITMENT_FILENAME,
    INTERFACE_ID,
    HiddenReferenceHandle,
    SealedReferenceIdentityError,
    SealedReferenceUnavailable,
    handle_for,
    interface_identity,
    render_commitment,
    resolve,
)
from swarm.evals.g13_size_classifier_v2 import (
    CLASSIFIER_ID,
    classifier_identity,
    classify,
    derive_features,
)
from swarm.evals.task_pool_freeze_v2 import (
    CHECKSUMS_NAME,
    FREEZE_DIR,
    FREEZE_ID,
    HOLDOUT_DIRNAME,
    MANIFEST_NAME,
    SHARD_TABLE_NAME,
    canonical_corpus_records,
    file_digest,
    load_manifest,
    manifest_path,
    render_checksums,
    render_commitment_file,
    render_shard_table,
    verify_checksums_v2,
    verify_pool_freeze_v2,
)

REPO = Path(__file__).resolve().parents[2]
FREEZE = REPO / FREEZE_DIR

REQUIRED_FAMILIES: dict[str, str] = {
    "coding": "code_generation",
    "extraction": "extraction",
    "planning": "dependency_planning",
    "reasoning": "evidence_qa",
}
SIZES = ("S", "M", "L", "XL")


# ---------------------------------------------------------------------------
# the committed freeze
# ---------------------------------------------------------------------------


def test_committed_freeze_verifies_clean() -> None:
    result = verify_pool_freeze_v2(REPO)
    assert result.ok, result.report()


def test_committed_checksums_cover_every_frozen_file_recursively() -> None:
    result = verify_checksums_v2(REPO)
    assert result.ok, result.report()


def test_shard_table_regenerates_byte_identically() -> None:
    expected = (FREEZE / SHARD_TABLE_NAME).read_bytes().decode("utf-8")
    assert render_shard_table(REPO) == expected


def test_commitment_regenerates_byte_identically() -> None:
    expected = (FREEZE / COMMITMENT_FILENAME).read_bytes().decode("utf-8")
    assert render_commitment_file(canonical_corpus_records(REPO)) == expected


def test_checksums_regenerate_byte_identically() -> None:
    expected = (FREEZE / CHECKSUMS_NAME).read_bytes().decode("utf-8")
    assert render_checksums(REPO) == expected


@pytest.mark.parametrize(
    ("filename", "identity"),
    [
        ("identity_size_classifier_v2.json", classifier_identity),
        ("identity_prompt_v2.json", prompt_identity),
        ("identity_independence_checker_v2.json", checker_identity),
        ("identity_sealed_reference_v2.json", interface_identity),
    ],
)
def test_identity_spec_mirrors_its_module(filename: str, identity: Any) -> None:
    spec = json.loads((FREEZE / filename).read_bytes().decode("utf-8"))
    assert spec["identity"] == identity()


def test_required_coverage_is_at_least_fifteen_per_cell() -> None:
    stats = verify_pool_freeze_v2(REPO).stats
    per_cell = stats["independent_per_required_cell"]
    for product_family in REQUIRED_FAMILIES:
        for size in SIZES:
            cell = f"{product_family}/{size}"
            assert per_cell[cell] >= 15, f"{cell}: {per_cell.get(cell)}"
    assert stats["held_out_record_count"] >= 240
    assert stats["distinct_record_digests"] == stats["held_out_record_count"]


def test_committed_corpus_leaks_no_answer() -> None:
    stats = verify_pool_freeze_v2(REPO).stats
    assert stats["answer_leak_count"] == 0


def test_no_frozen_file_names_an_answer_key() -> None:
    for path in sorted(FREEZE.rglob("*.json")):
        payload = json.loads(path.read_bytes().decode("utf-8"))
        assert find_denylisted_keys(payload) == [], path.name


def test_every_committed_record_is_input_only_and_renderable() -> None:
    for entry in canonical_corpus_records(REPO):
        visible = visible_input(entry.record)
        assert set(entry.record) & {"expected_output", "grader", "reference_solution"} == set()
        assert classify(visible) == entry.row.size
        assert render_prompt(visible).endswith("\n")


def test_committed_independence_is_clean_and_fully_distinct() -> None:
    stats = verify_pool_freeze_v2(REPO).stats["independence"]
    assert stats["held_out_count"] == stats["distinct_held_out_templates"]
    assert stats["held_out_count"] == stats["distinct_held_out_payload_digests"]
    assert stats["held_out_count"] == stats["distinct_held_out_prompt_digests"]
    assert stats["held_out_template_collisions"] == 0
    assert stats["cross_partition_case_id_overlaps"] == 0
    assert stats["cross_partition_payload_overlaps"] == 0
    assert stats["cross_partition_prompt_overlaps"] == 0
    assert stats["cross_partition_template_isomorphs"] == 0
    assert stats["foreign_count"] > 0, "no foreign corpus was compared against"


def test_readiness_is_computed_and_not_claimed() -> None:
    stats = verify_pool_freeze_v2(REPO).stats
    manifest = load_manifest(manifest_path(REPO))
    declared = manifest["qualification_readiness"]["counted_qualification_ready"]
    assert declared is stats["counted_qualification_ready_computed"]
    assert stats["sealed_bundle_content_digest_bound"] is False
    assert declared is False


# ---------------------------------------------------------------------------
# sealed grader-reference interface
# ---------------------------------------------------------------------------


class _FakeSealedSource:
    """Stands in for the qualification harness' bundle. Test-only."""

    def __init__(self, bundle_id: str, commitment_sha256: str) -> None:
        self.bundle_id = bundle_id
        self.commitment_sha256 = commitment_sha256

    def fetch(self, hidden_reference_id: str) -> Mapping[str, Any]:
        return {"hidden_reference_id": hidden_reference_id, "payload": "sealed"}


def _committed_commitment_digest() -> str:
    return file_digest(FREEZE / COMMITMENT_FILENAME)


def test_resolve_fails_closed_without_a_sealed_source() -> None:
    for entry in canonical_corpus_records(REPO)[:5]:
        handle = handle_for(entry.record)
        with pytest.raises(SealedReferenceUnavailable):
            resolve(handle)


def test_resolve_refuses_an_unbound_bundle() -> None:
    handle = handle_for(canonical_corpus_records(REPO)[0].record)
    source = _FakeSealedSource(BUNDLE_ID, _committed_commitment_digest())
    with pytest.raises(SealedReferenceIdentityError):
        resolve(handle, source)


def test_resolve_refuses_a_mismatched_commitment_digest() -> None:
    handle = handle_for(canonical_corpus_records(REPO)[0].record)
    source = _FakeSealedSource(BUNDLE_ID, "0" * 64)
    with pytest.raises(SealedReferenceIdentityError):
        resolve(handle, source, expected_commitment_sha256=_committed_commitment_digest())


def test_resolve_refuses_a_foreign_bundle_id() -> None:
    handle = handle_for(canonical_corpus_records(REPO)[0].record)
    digest = _committed_commitment_digest()
    source = _FakeSealedSource("some-other-bundle", digest)
    with pytest.raises(SealedReferenceIdentityError):
        resolve(handle, source, expected_commitment_sha256=digest)


def test_resolve_succeeds_only_with_a_matching_bundle() -> None:
    handle = handle_for(canonical_corpus_records(REPO)[0].record)
    digest = _committed_commitment_digest()
    source = _FakeSealedSource(BUNDLE_ID, digest)
    got = resolve(handle, source, expected_commitment_sha256=digest)
    assert got["hidden_reference_id"] == handle.hidden_reference_id


def test_handle_refuses_extra_keys_in_the_hidden_reference_block() -> None:
    record = dict(canonical_corpus_records(REPO)[0].record)
    record["hidden_reference"] = {
        "interface_id": INTERFACE_ID,
        "hidden_reference_id": "g13hr2-0001",
        "expected_output": {"rows": []},
    }
    with pytest.raises(SealedReferenceIdentityError):
        handle_for(record)


def test_no_local_reference_bundle_exists_on_this_branch() -> None:
    names = {p.name for p in FREEZE.rglob("*") if p.is_file()}
    assert "REFERENCES.jsonl" not in names
    assert "hidden_references.json" not in names


# ---------------------------------------------------------------------------
# synthetic freeze fixture (test-only; never qualification evidence)
# ---------------------------------------------------------------------------

_WORDS = (
    "alfa",
    "bravo",
    "charlie",
    "delta",
    "echo",
    "foxtrot",
    "golf",
    "hotel",
    "india",
    "juliett",
    "kilo",
    "lima",
    "mike",
    "november",
    "oscar",
)

#: ``size -> (items, constraints, distractors, output fields)``. The resulting
#: structural loads are 6 / 11 / 17 / 24, which land in S / M / L / XL under
#: ``g13-size-classifier-v2``.
_SHAPE: dict[str, tuple[int, int, int, int]] = {
    "S": (2, 1, 0, 3),
    "M": (5, 2, 1, 3),
    "L": (9, 3, 2, 3),
    "XL": (14, 4, 3, 3),
}


def _synthetic_record(
    product_family: str, family: str, size: str, index: int, reference_index: int
) -> dict[str, Any]:
    items_n, constraints_n, distractors_n, fields_n = _SHAPE[size]
    word = _WORDS[index - 1]
    payload: dict[str, Any] = {
        "task": family,
        "instruction": f"synthetic {product_family} {word} exercise",
        "items": [
            {"ref": f"SX-{i}", "requirement": f"{word} clause {i}"}
            for i in range(1, items_n + 1)
        ],
        "constraints": [f"{word} rule {i}" for i in range(1, constraints_n + 1)],
        "output_contract": {
            "format": "json",
            "fields": [f"field_{i}" for i in range(1, fields_n + 1)],
            "sort_by": "ref",
        },
    }
    if distractors_n:
        payload["distractors"] = [
            f"{word} aside {i}" for i in range(1, distractors_n + 1)
        ]
    return {
        "schema_version": "2.0",
        "pool": FREEZE_ID,
        "id": f"g13v2_{product_family}_{size}_{index:02d}",
        "split": "holdout",
        "product_family": product_family,
        "family": family,
        "size": size,
        "variant": "synthetic",
        "scenario": word,
        "input": payload,
        "hidden_reference": {
            "interface_id": INTERFACE_ID,
            "hidden_reference_id": f"g13hr2-{reference_index:04d}",
        },
        "generation": {
            "synthetic": True,
            "third_party_source": False,
            "corpus_revision": "test-fixture",
            "authoring": "generated_by_test",
        },
        "output_limit_tokens_proposed": 1024,
    }


def _identity_block(
    root: Path, name: str, filename: str, identity: dict[str, Any], **extra: Any
) -> dict[str, Any]:
    target = root / FREEZE_DIR / filename
    target.write_text(
        json.dumps({"spec_of": name, "identity": identity}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="",
    )
    block: dict[str, Any] = {"spec": {"path": str(Path(FREEZE_DIR) / filename).replace("\\", "/")}}
    block.update(extra)
    return block


def _write_synthetic_freeze(root: Path) -> Path:
    """Build a complete, clean synthetic v2 freeze under ``root``."""
    freeze_dir = root / FREEZE_DIR
    (freeze_dir / HOLDOUT_DIRNAME).mkdir(parents=True, exist_ok=True)

    reference_index = 0
    for product_family, family in sorted(REQUIRED_FAMILIES.items()):
        for size in SIZES:
            lines: list[str] = []
            for index in range(1, 16):
                reference_index += 1
                record = _synthetic_record(
                    product_family, family, size, index, reference_index
                )
                lines.append(json.dumps(record, separators=(",", ":"), sort_keys=True))
            shard = freeze_dir / HOLDOUT_DIRNAME / f"{product_family}_{size}.jsonl"
            shard.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")

    # A burned foreign corpus: v1-shaped, answers once worker-visible.
    foreign_dir = root / "benchmarks"
    foreign_dir.mkdir(parents=True, exist_ok=True)
    foreign = foreign_dir / "legacy_pool.jsonl"
    foreign.write_text(
        "\n".join(
            json.dumps(
                {
                    "id": f"legacy_{i}",
                    "split": "calibration" if i % 2 else "holdout",
                    "input": {"prompt": f"legacy prompt number {i} about nothing"},
                },
                separators=(",", ":"),
                sort_keys=True,
            )
            for i in range(1, 5)
        )
        + "\n",
        encoding="utf-8",
        newline="",
    )

    records = canonical_corpus_records(root)
    (freeze_dir / SHARD_TABLE_NAME).write_text(
        render_shard_table(root), encoding="utf-8", newline=""
    )
    (freeze_dir / COMMITMENT_FILENAME).write_text(
        render_commitment_file(records), encoding="utf-8", newline=""
    )

    identities: dict[str, dict[str, Any]] = {
        "pool": _identity_block(
            root,
            "pool",
            "identity_pool_v2.json",
            {"pool_id": FREEZE_ID, "shard_count": 16, "record_count": 240},
        ),
        "records": _identity_block(
            root,
            "records",
            "identity_records_v2.json",
            {"records_id": "g13-records-v2", "pinned_by": "shard byte digests"},
        ),
        "split": _identity_block(
            root,
            "split",
            "identity_split_v2.json",
            {"split_id": "g13-split-v2", "splits": ["holdout"]},
        ),
        "size_classifier": _identity_block(
            root,
            "size_classifier",
            "identity_size_classifier_v2.json",
            classifier_identity(),
            classifier_id=CLASSIFIER_ID,
        ),
        "scorer": _identity_block(
            root,
            "scorer",
            "identity_scorer_v2.json",
            {"scorer_id": "g13-scorer-v2", "graders": ["json_exact"]},
        ),
        "prompt": _identity_block(
            root, "prompt", "identity_prompt_v2.json", prompt_identity(), prompt_id=PROMPT_ID
        ),
        "tool_protocol": _identity_block(
            root,
            "tool_protocol",
            "identity_tool_protocol_v2.json",
            {"tool_protocol_id": "g13-tool-protocol-v2", "model_visible_tools": 0},
        ),
        "model_config_schema": _identity_block(
            root,
            "model_config_schema",
            "identity_model_config_schema_v2.json",
            {"schema_id": "g13-exact-model-config-v2", "required": ["provider", "model"]},
        ),
        "independence_checker": _identity_block(
            root,
            "independence_checker",
            "identity_independence_checker_v2.json",
            checker_identity(),
            checker_id=CHECKER_ID,
        ),
        "sealed_reference_interface": _identity_block(
            root,
            "sealed_reference_interface",
            "identity_sealed_reference_v2.json",
            interface_identity(),
            interface_id=INTERFACE_ID,
        ),
    }
    for block in identities.values():
        spec = block["spec"]
        spec["sha256"] = file_digest(root / str(spec["path"]))

    manifest: dict[str, Any] = {
        "schema_version": "2.0",
        "artifact_id": "ART-V13-TASK-POOL",
        "freeze_id": FREEZE_ID,
        "freeze_version": 2,
        "corpus": {
            "root": f"{Path(FREEZE_DIR).as_posix()}/{HOLDOUT_DIRNAME}",
            "format": "jsonl",
            "record_count": 240,
            "shard_count": 16,
            "shard_table": {
                "path": f"{Path(FREEZE_DIR).as_posix()}/{SHARD_TABLE_NAME}",
                "sha256": file_digest(freeze_dir / SHARD_TABLE_NAME),
            },
        },
        "coverage": {
            "required_product_families": sorted(REQUIRED_FAMILIES),
            "required_sizes": list(SIZES),
            "min_independent_per_required_cell": 15,
            "min_total_independent_held_out": 240,
        },
        "identities": identities,
        "sealed_reference": {
            "interface_id": INTERFACE_ID,
            "id_commitment": {
                "path": f"{Path(FREEZE_DIR).as_posix()}/{COMMITMENT_FILENAME}",
                "sha256": file_digest(freeze_dir / COMMITMENT_FILENAME),
                "entry_count": 240,
            },
            "reference_bundle": {
                "bundle_id": BUNDLE_ID,
                "location": "outside_the_worker_visible_branch",
                "content_digest_binding": {
                    "declared_here": False,
                    "required_before_counted_qualification": True,
                    "reason": "the bundle is not authored by this fixture",
                },
            },
        },
        "foreign_corpora": [
            {
                "corpus_id": "legacy-pool-v1",
                "path": "benchmarks/legacy_pool.jsonl",
                "sha256": file_digest(foreign),
                "prompt_field": "prompt",
                "why_foreign": "answers were worker-visible, so the split is burned",
            }
        ],
        "qualification_readiness": {
            "counted_qualification_ready": False,
            "blocking_reason": "sealed_reference_bundle_content_digest_not_bound",
        },
    }
    (freeze_dir / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline=""
    )
    (freeze_dir / CHECKSUMS_NAME).write_text(
        render_checksums(root), encoding="utf-8", newline=""
    )
    return root


def _remint(root: Path) -> None:
    """Re-derive every digest sidecar after a corpus mutation."""
    freeze_dir = root / FREEZE_DIR
    (freeze_dir / SHARD_TABLE_NAME).write_text(
        render_shard_table(root), encoding="utf-8", newline=""
    )
    manifest = load_manifest(manifest_path(root))
    manifest["corpus"]["shard_table"]["sha256"] = file_digest(freeze_dir / SHARD_TABLE_NAME)
    (freeze_dir / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline=""
    )
    (freeze_dir / CHECKSUMS_NAME).write_text(
        render_checksums(root), encoding="utf-8", newline=""
    )


def _shard(root: Path, name: str) -> Path:
    return root / FREEZE_DIR / HOLDOUT_DIRNAME / name


def _read_shard(root: Path, name: str) -> list[dict[str, Any]]:
    text = _shard(root, name).read_bytes().decode("utf-8")
    return [json.loads(line) for line in text.splitlines() if line]


def _write_shard(root: Path, name: str, records: list[dict[str, Any]]) -> None:
    _shard(root, name).write_text(
        "\n".join(json.dumps(r, separators=(",", ":"), sort_keys=True) for r in records) + "\n",
        encoding="utf-8",
        newline="",
    )


def _patch_manifest(root: Path, mutate: Any) -> None:
    manifest = load_manifest(manifest_path(root))
    mutate(manifest)
    (root / FREEZE_DIR / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline=""
    )
    (root / FREEZE_DIR / CHECKSUMS_NAME).write_text(
        render_checksums(root), encoding="utf-8", newline=""
    )


@pytest.fixture
def freeze(tmp_path: Path) -> Path:
    return _write_synthetic_freeze(tmp_path)


def test_synthetic_fixture_is_itself_clean(freeze: Path) -> None:
    result = verify_pool_freeze_v2(freeze)
    assert result.ok, result.report()
    assert verify_checksums_v2(freeze).ok
    assert result.stats["freeze_conditions_pass"] is True
    assert result.stats["counted_qualification_ready_computed"] is False


# --- negative: visible answer leakage --------------------------------------


def test_rejects_visible_answer_leakage_in_a_record(freeze: Path) -> None:
    records = _read_shard(freeze, "coding_S.jsonl")
    records[3]["expected_output"] = {"module_source": "def f(): return 1"}
    _write_shard(freeze, "coding_S.jsonl", records)
    _remint(freeze)
    result = verify_pool_freeze_v2(freeze)
    codes = result.codes()
    assert "visible_answer_leak" in codes, result.report()
    assert "visible_payload_refused" in codes
    assert result.stats["answer_leak_count"] == 1


def test_rejects_a_grader_fixture_nested_inside_the_input(freeze: Path) -> None:
    records = _read_shard(freeze, "reasoning_M.jsonl")
    records[0]["input"]["grader"] = {"kind": "json_exact"}
    _write_shard(freeze, "reasoning_M.jsonl", records)
    _remint(freeze)
    result = verify_pool_freeze_v2(freeze)
    assert "visible_answer_leak" in result.codes(), result.report()


def test_visible_input_refuses_rather_than_sanitises() -> None:
    record = {"id": "x", "input": {"task": "t", "instruction": "i"}, "expected_output": 1}
    with pytest.raises(PromptV2Error):
        visible_input(record)


# --- negative: cell depth ---------------------------------------------------


def test_rejects_fewer_than_fifteen_inputs_in_a_required_cell(freeze: Path) -> None:
    records = _read_shard(freeze, "planning_L.jsonl")
    _write_shard(freeze, "planning_L.jsonl", records[:14])
    _remint(freeze)
    result = verify_pool_freeze_v2(freeze)
    codes = result.codes()
    assert "required_cell_below_minimum" in codes, result.report()
    assert "corpus_below_minimum_total" in codes


def test_rejects_a_missing_required_cell(freeze: Path) -> None:
    _shard(freeze, "extraction_XL.jsonl").unlink()
    _remint(freeze)
    result = verify_pool_freeze_v2(freeze)
    assert "required_cell_below_minimum" in result.codes(), result.report()


# --- negative: overlap axes -------------------------------------------------


def test_rejects_case_id_overlap_with_a_foreign_corpus(freeze: Path) -> None:
    records = _read_shard(freeze, "coding_S.jsonl")
    stolen = records[0]["id"]
    foreign = freeze / "benchmarks" / "legacy_pool.jsonl"
    lines = foreign.read_bytes().decode("utf-8").splitlines()
    clash = json.loads(lines[0])
    clash["id"] = stolen
    lines[0] = json.dumps(clash, separators=(",", ":"), sort_keys=True)
    foreign.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    _patch_manifest(
        freeze,
        lambda m: m["foreign_corpora"][0].__setitem__("sha256", file_digest(foreign)),
    )
    result = verify_pool_freeze_v2(freeze)
    assert "cross_partition_case_id_overlap" in result.codes(), result.report()


def _clash_foreign_record(freeze: Path, payload: dict[str, Any]) -> None:
    """Overwrite the first foreign record's ``input`` and re-pin its digest."""
    foreign = freeze / "benchmarks" / "legacy_pool.jsonl"
    lines = foreign.read_bytes().decode("utf-8").splitlines()
    clash = json.loads(lines[0])
    clash["input"] = payload
    lines[0] = json.dumps(clash, separators=(",", ":"), sort_keys=True)
    foreign.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    _patch_manifest(
        freeze,
        lambda m: m["foreign_corpora"][0].__setitem__("sha256", file_digest(foreign)),
    )


def test_rejects_input_digest_overlap_with_a_foreign_corpus(freeze: Path) -> None:
    records = _read_shard(freeze, "coding_S.jsonl")
    _clash_foreign_record(freeze, records[0]["input"])
    result = verify_pool_freeze_v2(freeze)
    assert "cross_partition_payload_digest_overlap" in result.codes(), result.report()


def test_rejects_rendered_prompt_overlap_with_a_foreign_corpus(freeze: Path) -> None:
    records = _read_shard(freeze, "extraction_L.jsonl")
    rendered = render_prompt(visible_input(records[0]))
    _clash_foreign_record(freeze, {"prompt": rendered})
    result = verify_pool_freeze_v2(freeze)
    codes = result.codes()
    assert "cross_partition_prompt_digest_overlap" in codes, result.report()
    assert "cross_partition_template_isomorph" in codes


def test_rejects_a_duplicate_normalised_template_inside_the_holdout(freeze: Path) -> None:
    records = _read_shard(freeze, "coding_S.jsonl")
    # Seed-isomorphic sibling: identical structure, different synthetic names.
    records[1]["input"] = json.loads(
        json.dumps(records[0]["input"]).replace("SX-", "QQ-")
    )
    _write_shard(freeze, "coding_S.jsonl", records)
    _remint(freeze)
    result = verify_pool_freeze_v2(freeze)
    codes = result.codes()
    assert "holdout_template_duplicate" in codes, result.report()


def test_rejects_an_exact_duplicate_prompt_inside_the_holdout(freeze: Path) -> None:
    records = _read_shard(freeze, "extraction_M.jsonl")
    records[2]["input"] = json.loads(json.dumps(records[1]["input"]))
    _write_shard(freeze, "extraction_M.jsonl", records)
    _remint(freeze)
    result = verify_pool_freeze_v2(freeze)
    codes = result.codes()
    assert "holdout_payload_digest_duplicate" in codes, result.report()
    assert "holdout_prompt_digest_duplicate" in codes


def test_rejects_a_seed_isomorphic_overlap_with_a_foreign_corpus(freeze: Path) -> None:
    records = _read_shard(freeze, "reasoning_S.jsonl")
    # Differs from the held-out record only in its synthetic identifiers and
    # numbering, so it is a distinct string but not an independent observation.
    isomorph = render_prompt(visible_input(records[0])).replace("SX-1", "SX-9987")
    _clash_foreign_record(freeze, {"prompt": isomorph})
    result = verify_pool_freeze_v2(freeze)
    codes = result.codes()
    assert "cross_partition_template_isomorph" in codes, result.report()
    assert "cross_partition_prompt_digest_overlap" not in codes


def test_normaliser_collapses_synthetic_identifiers_and_numbers() -> None:
    a = normalise_template("ITEMS:\n- ORD-310-001 amount 231\n")
    b = normalise_template("ITEMS:\n- ORD-998-777 amount 4242\n")
    assert a == b
    c = normalise_template("ITEMS:\n- ORD-310-001 volume 231\n")
    assert a != c


def test_independence_checker_flags_every_axis() -> None:
    def rec(case_id: str, split: str, seed: str) -> IndependenceRecord:
        return IndependenceRecord(
            corpus_id="pool",
            split=split,
            case_id=case_id,
            payload_digest=sha256_hex(f"p{seed}".encode()),
            prompt_digest=sha256_hex(f"r{seed}".encode()),
            template_digest=sha256_hex(f"t{seed}".encode()),
        )

    report = check_independence(
        [rec("a", "holdout", "1"), rec("b", "holdout", "1")],
        held_out_corpus_id="pool",
        held_out_split="holdout",
    )
    codes = {v.code for v in report.violations}
    assert codes == {
        "holdout_payload_digest_duplicate",
        "holdout_prompt_digest_duplicate",
        "holdout_template_duplicate",
    }, report.report()

    report = check_independence(
        [rec("a", "holdout", "1"), rec("a", "calibration", "1")],
        held_out_corpus_id="pool",
        held_out_split="holdout",
    )
    codes = {v.code for v in report.violations}
    assert codes == {
        "cross_partition_case_id_overlap",
        "cross_partition_payload_digest_overlap",
        "cross_partition_prompt_digest_overlap",
        "cross_partition_template_isomorph",
    }, report.report()


# --- negative: hidden-reference identity ------------------------------------


def test_rejects_a_missing_hidden_reference_block(freeze: Path) -> None:
    records = _read_shard(freeze, "coding_M.jsonl")
    del records[5]["hidden_reference"]
    _write_shard(freeze, "coding_M.jsonl", records)
    _remint(freeze)
    result = verify_pool_freeze_v2(freeze)
    codes = result.codes()
    assert "hidden_reference_identity_invalid" in codes, result.report()
    assert "commitment_case_not_in_corpus" in codes


def test_rejects_a_mismatched_hidden_reference_id(freeze: Path) -> None:
    records = _read_shard(freeze, "coding_M.jsonl")
    records[5]["hidden_reference"]["hidden_reference_id"] = "g13hr2-9999"
    _write_shard(freeze, "coding_M.jsonl", records)
    _remint(freeze)
    result = verify_pool_freeze_v2(freeze)
    assert "hidden_reference_id_mismatch" in result.codes(), result.report()


def test_rejects_a_duplicate_hidden_reference_id(freeze: Path) -> None:
    records = _read_shard(freeze, "planning_S.jsonl")
    records[1]["hidden_reference"]["hidden_reference_id"] = records[0]["hidden_reference"][
        "hidden_reference_id"
    ]
    _write_shard(freeze, "planning_S.jsonl", records)
    _remint(freeze)
    result = verify_pool_freeze_v2(freeze)
    assert "hidden_reference_id_duplicate" in result.codes(), result.report()


def test_rejects_a_tampered_commitment_digest(freeze: Path) -> None:
    _patch_manifest(
        freeze,
        lambda m: m["sealed_reference"]["id_commitment"].__setitem__("sha256", "0" * 64),
    )
    result = verify_pool_freeze_v2(freeze)
    assert "sealed_reference_commitment_digest_mismatch" in result.codes(), result.report()


def test_rejects_a_wrong_commitment_entry_count(freeze: Path) -> None:
    _patch_manifest(
        freeze,
        lambda m: m["sealed_reference"]["id_commitment"].__setitem__("entry_count", 239),
    )
    result = verify_pool_freeze_v2(freeze)
    assert "sealed_reference_entry_count_mismatch" in result.codes(), result.report()


def test_rejects_a_reference_bundle_declared_inside_the_branch(freeze: Path) -> None:
    _patch_manifest(
        freeze,
        lambda m: m["sealed_reference"]["reference_bundle"].__setitem__(
            "location", "benchmarks/g13/pool_freeze_v2/references.jsonl"
        ),
    )
    result = verify_pool_freeze_v2(freeze)
    assert "sealed_reference_bundle_inside_branch" in result.codes(), result.report()


def test_rejects_a_bundle_claiming_a_digest_it_does_not_declare(freeze: Path) -> None:
    _patch_manifest(
        freeze,
        lambda m: m["sealed_reference"]["reference_bundle"][
            "content_digest_binding"
        ].__setitem__("declared_here", True),
    )
    result = verify_pool_freeze_v2(freeze)
    assert "sealed_reference_bundle_digest_absent" in result.codes(), result.report()


def test_commitment_renders_opaque_ids_only() -> None:
    rendered = render_commitment(
        [HiddenReferenceHandle("case_1", "g13hr2-0001", INTERFACE_ID)]
    )
    assert "g13hr2-0001" in rendered
    assert "expected" not in rendered
    assert "grader" not in rendered


# --- negative: mutated bytes ------------------------------------------------


def test_rejects_mutated_pool_bytes(freeze: Path) -> None:
    shard = _shard(freeze, "reasoning_XL.jsonl")
    text = shard.read_bytes().decode("utf-8")
    shard.write_text(text.replace("alfa", "alpha", 1), encoding="utf-8", newline="")
    result = verify_pool_freeze_v2(freeze)
    assert "shard_digest_mismatch" in result.codes(), result.report()


def test_rejects_a_mutated_shard_table(freeze: Path) -> None:
    table = freeze / FREEZE_DIR / SHARD_TABLE_NAME
    text = table.read_bytes().decode("utf-8")
    table.write_text(text.replace(" 15 ", " 14 ", 1), encoding="utf-8", newline="")
    result = verify_pool_freeze_v2(freeze)
    codes = result.codes()
    assert "shard_table_digest_mismatch" in codes, result.report()
    assert "shard_record_count_mismatch" in codes


def test_rejects_an_undeclared_shard_on_disk(freeze: Path) -> None:
    extra = _shard(freeze, "coding_S.jsonl").read_bytes()
    (freeze / FREEZE_DIR / HOLDOUT_DIRNAME / "coding_S_copy.jsonl").write_bytes(extra)
    result = verify_pool_freeze_v2(freeze)
    assert "shard_not_in_table" in result.codes(), result.report()


def test_rejects_a_file_not_covered_by_the_checksums(freeze: Path) -> None:
    (freeze / FREEZE_DIR / "stray_note.txt").write_text("stray\n", encoding="utf-8", newline="")
    result = verify_checksums_v2(freeze)
    assert "checksum_uncovered_file" in result.codes(), result.report()


# --- negative: incomplete / floating identities -----------------------------


def test_rejects_a_missing_identity_block(freeze: Path) -> None:
    def drop(manifest: dict[str, Any]) -> None:
        del manifest["identities"]["independence_checker"]

    _patch_manifest(freeze, drop)
    result = verify_pool_freeze_v2(freeze)
    assert "identity_missing" in result.codes(), result.report()


def test_rejects_a_floating_manifest_value(freeze: Path) -> None:
    _patch_manifest(
        freeze, lambda m: m["coverage"].__setitem__("required_product_families_note", "TBD")
    )
    result = verify_pool_freeze_v2(freeze)
    assert "floating_manifest_value" in result.codes(), result.report()


def test_rejects_an_empty_container_in_the_manifest(freeze: Path) -> None:
    _patch_manifest(freeze, lambda m: m["corpus"].__setitem__("notes", []))
    result = verify_pool_freeze_v2(freeze)
    assert "floating_manifest_value" in result.codes(), result.report()


def test_rejects_a_floating_identity_spec_value(freeze: Path) -> None:
    spec_path = freeze / FREEZE_DIR / "identity_scorer_v2.json"
    spec = json.loads(spec_path.read_bytes().decode("utf-8"))
    spec["identity"]["grader_matrix"] = "tbd"
    spec_path.write_text(
        json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline=""
    )
    _patch_manifest(
        freeze,
        lambda m: m["identities"]["scorer"]["spec"].__setitem__(
            "sha256", file_digest(spec_path)
        ),
    )
    result = verify_pool_freeze_v2(freeze)
    assert "floating_identity_value" in result.codes(), result.report()


def test_rejects_a_drifted_identity_spec_digest(freeze: Path) -> None:
    _patch_manifest(
        freeze,
        lambda m: m["identities"]["prompt"]["spec"].__setitem__("sha256", "0" * 64),
    )
    result = verify_pool_freeze_v2(freeze)
    assert "identity_spec_digest_mismatch" in result.codes(), result.report()


def test_rejects_an_identity_id_that_disagrees_with_its_module(freeze: Path) -> None:
    _patch_manifest(
        freeze,
        lambda m: m["identities"]["size_classifier"].__setitem__(
            "classifier_id", "g13-size-classifier-v1"
        ),
    )
    result = verify_pool_freeze_v2(freeze)
    assert "identity_id_code_mismatch" in result.codes(), result.report()


# --- negative: readiness over-claim -----------------------------------------


def test_rejects_an_unearned_counted_qualification_ready_claim(freeze: Path) -> None:
    _patch_manifest(
        freeze,
        lambda m: m["qualification_readiness"].__setitem__(
            "counted_qualification_ready", True
        ),
    )
    result = verify_pool_freeze_v2(freeze)
    assert "readiness_declaration_mismatch" in result.codes(), result.report()


def test_rejects_a_size_band_the_classifier_does_not_derive(freeze: Path) -> None:
    records = _read_shard(freeze, "coding_S.jsonl")
    records[0]["input"]["items"].extend(
        {"ref": f"SX-{i}", "requirement": f"extra clause {i}"} for i in range(90, 100)
    )
    _write_shard(freeze, "coding_S.jsonl", records)
    _remint(freeze)
    result = verify_pool_freeze_v2(freeze)
    assert "size_classifier_disagreement" in result.codes(), result.report()


def test_classifier_derives_bands_from_the_payload_not_a_declaration() -> None:
    visible = {
        "task": "extraction",
        "instruction": "x",
        "items": [{"ref": f"SX-{i}"} for i in range(1, 3)],
        "constraints": ["a"],
        "output_contract": {"format": "json", "fields": ["a", "b", "c"], "sort_by": "ref"},
    }
    features = derive_features(visible)
    assert features.structural_load() == 6
    assert classify(visible) == "S"
    visible["items"] = [{"ref": f"SX-{i}"} for i in range(1, 30)]
    assert classify(visible) == "XL"


def test_digests_are_stable_across_key_order() -> None:
    a = {"task": "t", "instruction": "i", "items": [], "constraints": [], "output_contract": {}}
    b = {"output_contract": {}, "constraints": [], "items": [], "instruction": "i", "task": "t"}
    assert visible_payload_digest(a) == visible_payload_digest(b)
    assert rendered_prompt_digest(a) == rendered_prompt_digest(b)
