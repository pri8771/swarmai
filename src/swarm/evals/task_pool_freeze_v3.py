"""ART-V13-TASK-POOL — g13-pool-freeze-v3 generate + verify (fail-closed)."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.evals.g13_corpus_v3_specs import (
    CELL_OBJECTIVES,
    DATASET_FAMILY,
    PRODUCT_FAMILIES,
    SIZE_BANDS,
)
from swarm.evals.g13_independence_v3 import (
    IndependenceRecord,
    check_independence,
    checker_identity,
    clause_texts,
    normalise_template,
    scenario_stripped_stem,
)
from swarm.evals.g13_prompt_v3 import (
    PROMPT_ID,
    PromptV3Error,
    canonical_json,
    find_denylisted_keys,
    prompt_identity,
    render_prompt,
    rendered_prompt_digest,
    sha256_hex,
    visible_input,
    visible_payload_digest,
)
from swarm.evals.g13_sealed_reference_v3 import (
    BUNDLE_ID,
    COMMITMENT_FILENAME,
    INTERFACE_ID,
    SealedReferenceIdentityError,
    commitment_violations,
    handle_for,
    interface_identity,
    load_commitment,
    render_commitment,
)
from swarm.evals.g13_size_classifier_v3 import (
    SizeClassifierV3Error,
    classifier_identity,
    classify,
    derive_features,
)

FREEZE_ID = "g13-pool-freeze-v3"
FREEZE_VERSION = 3
FREEZE_DIR = Path("benchmarks") / "g13" / "pool_freeze_v3"
MANIFEST_NAME = "task_pool_freeze_v3.manifest.json"
SHARD_TABLE_NAME = "CORPUS_SHARD_DIGESTS.txt"
CHECKSUMS_NAME = "SHA256SUMS"
HOLDOUT_DIRNAME = "holdout"
CALIBRATION_DIRNAME = "calibration"
HELD_OUT_SPLIT = "holdout"
CALIBRATION_SPLIT = "calibration"
SCHEMA_VERSION = "3.0"
MIN_PER_CELL = 15
MIN_TOTAL = 240
WILSON_COUNTED_Z = 1.2815515655446004
FLOATING_VALUES = frozenset(
    {"", "tbd", "todo", "unknown", "null", "none", "n/a", "fixme", "<fill>", "changeme", "?"}
)
REQUIRED_IDENTITIES = (
    "pool",
    "records",
    "split",
    "size_classifier",
    "scorer",
    "prompt",
    "tool_protocol",
    "model_config_schema",
    "independence_checker",
    "sealed_reference_interface",
)
SIZE_LAYOUT = {
    "S": {"n_items": 2, "n_constraints": 1, "n_fields": 3, "n_distractors": 0, "dep_depth": 0},
    "M": {"n_items": 5, "n_constraints": 2, "n_fields": 3, "n_distractors": 1, "dep_depth": 0},
    "L": {"n_items": 7, "n_constraints": 3, "n_fields": 4, "n_distractors": 1, "dep_depth": 2},
    "XL": {"n_items": 12, "n_constraints": 4, "n_fields": 4, "n_distractors": 3, "dep_depth": 2},
}


class PoolFreezeV3Error(ValueError):
    """Raised when frozen v3 artefacts cannot be parsed."""


@dataclass(frozen=True)
class Violation:
    code: str
    detail: str

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


@dataclass
class FreezeVerification:
    violations: list[Violation] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.violations

    def add(self, code: str, detail: str) -> None:
        self.violations.append(Violation(code=code, detail=detail))

    def report(self) -> str:
        if self.ok:
            return f"{FREEZE_ID} OK"
        lines = "\n".join(f"  - {v}" for v in self.violations)
        return f"{FREEZE_ID} violations:\n{lines}"


@dataclass(frozen=True)
class LoadedRecord:
    line: str
    record: dict[str, Any]
    case_id: str
    product_family: str
    size: str
    split: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def file_digest(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def record_digest(line: str) -> str:
    return sha256_hex((line + "\n").encode("utf-8"))


def find_floating_values(value: Any, path: str = "$") -> list[str]:
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


def _as_dict(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PoolFreezeV3Error(f"{where}: expected object, got {type(value).__name__}")
    return {str(k): v for k, v in value.items()}


def _as_str(value: Any, where: str) -> str:
    if not isinstance(value, str):
        raise PoolFreezeV3Error(f"{where}: expected string, got {type(value).__name__}")
    return value


def _as_int(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PoolFreezeV3Error(f"{where}: expected integer, got {type(value).__name__}")
    return value


def _as_bool(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise PoolFreezeV3Error(f"{where}: expected boolean, got {type(value).__name__}")
    return value


def _get(mapping: Mapping[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise PoolFreezeV3Error(f"{where}: missing required key {key!r}")
    return mapping[key]


def _layout_payload(
    *,
    family: str,
    dataset_family: str,
    slug: str,
    description: str,
    size: str,
    split: str,
) -> dict[str, Any]:
    layout = SIZE_LAYOUT[size]
    items = [
        {
            "ref": f"{slug.replace('_', '-')}-clause-{index + 1}",
            "requirement": (
                f"{description}: satisfy uniquely worded obligation"
                f" {index + 1} for {slug.replace('_', ' ')} without sharing"
                f" wording with any other {family} {size} {split} case"
            ),
        }
        for index in range(layout["n_items"])
    ]
    constraints = [
        f"keep the {slug.replace('_', ' ')} response inside the output contract"
        f" field set ({index + 1})"
        for index in range(layout["n_constraints"])
    ]
    fields = [f"{slug}_field_{index + 1}" for index in range(layout["n_fields"])]
    distractors = [
        f"ignore the unrelated {slug.replace('_', ' ')} aside {index + 1}"
        for index in range(layout["n_distractors"])
    ]
    dependencies: list[list[str]] = []
    if layout["dep_depth"] >= 1:
        nodes = [f"{slug}-node-{n}" for n in "abcde"[: layout["dep_depth"] + 1]]
        dependencies = [[nodes[i], nodes[i + 1]] for i in range(len(nodes) - 1)]
    instruction = (
        f"Perform the distinct {family} task '{slug.replace('_', ' ')}': {description}."
        f" Do not treat this as a reseed, paraphrase, or clause expansion of any"
        f" other held-out case."
    )
    payload: dict[str, Any] = {
        "task": dataset_family,
        "instruction": instruction,
        "items": items,
        "constraints": constraints,
        "output_contract": {
            "format": "json_object" if family != "coding" else "python_source",
            "fields": fields,
            "sort_by": "none",
        },
    }
    if family == "coding":
        payload["signature"] = f"def {slug}(payload: dict[str, object]) -> dict[str, object]"
    if family == "reasoning":
        payload["question"] = (
            f"What is the uniquely determined conclusion of {slug.replace('_', ' ')}"
            f" given only the listed evidence clauses?"
        )
    if family == "planning" or layout["dep_depth"]:
        payload["dependencies"] = dependencies
    if distractors:
        payload["distractors"] = distractors
    return payload


def build_record(
    *,
    family: str,
    size: str,
    index: int,
    slug: str,
    description: str,
    split: str,
    hidden_reference_id: str,
) -> dict[str, Any]:
    dataset_family = DATASET_FAMILY[family]
    prefix = "g13v3cal" if split == CALIBRATION_SPLIT else "g13v3"
    case_id = f"{prefix}_{family}_{size}_{index:02d}"
    return {
        "schema_version": SCHEMA_VERSION,
        "pool": FREEZE_ID,
        "id": case_id,
        "split": split,
        "product_family": family,
        "family": dataset_family,
        "size": size,
        "semantic_archetype_id": f"g13v3.arch.{family}.{slug}",
        "input": _layout_payload(
            family=family,
            dataset_family=dataset_family,
            slug=slug,
            description=description,
            size=size,
            split=split,
        ),
        "hidden_reference": {
            "interface_id": INTERFACE_ID,
            "hidden_reference_id": hidden_reference_id,
        },
        "generation": {
            "synthetic": True,
            "third_party_source": False,
            "corpus_revision": "g13-corpus-v3",
            "authoring": "hand_authored_unique_objectives",
            "license": "CC0-1.0-equivalent-synthetic-original",
            "source": "SwarmAI G13 v3 synthetic authoring; no third-party dataset reuse",
        },
        "output_limit_tokens_proposed": 1024 if size in {"S", "M"} else 2048,
    }


def _jsonl_line(record: dict[str, Any]) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _scorer_identity() -> dict[str, Any]:
    return {
        "spec_of": "scorer",
        "identity": {
            "scorer_id": "g13-scorer-v3",
            "grader_contract_version": 3,
            "scoring_is_binary_per_case": True,
            "scoring_input": (
                "the model response text plus exactly one sealed reference record"
                " resolved through g13-sealed-reference-interface-v3"
            ),
            "scorer_may_read_the_corpus": True,
            "scorer_may_read_the_reference_bundle": True,
            "worker_may_read_the_reference_bundle": False,
            "scorer_kinds": ["json_exact", "topological_order", "python_unit"],
            "scorer_kind_per_product_family": {
                "coding": "python_unit",
                "extraction": "json_exact",
                "planning": "topological_order",
                "reasoning": "json_exact",
            },
            "output_contract_is_authoritative": True,
            "partial_credit": False,
            "wilson_bound": {
                "function": "swarm.evals.wilson.wilson_lower_bound",
                "default_z_in_code": 1.96,
                "default_z_is_wrong_for_this_protocol": True,
                "required_one_sided_90_percent_z": WILSON_COUNTED_Z,
                "counted_runs_must_pass_z_explicitly": True,
                "changed_by_this_packet": False,
            },
        },
        "implementation_pins": {
            "graders_module": "src/swarm/evals/graders.py",
            "sandbox_runner_module": "src/swarm/tools/sandbox_runner.py",
            "wilson_module": "src/swarm/evals/wilson.py",
        },
    }


def _tool_identity() -> dict[str, Any]:
    return {
        "spec_of": "tool_protocol",
        "identity": {
            "tool_protocol_id": "g13-tool-protocol-v3-no-model-visible-tools",
            "protocol_version": 3,
            "model_visible_tools": 0,
            "tool_descriptions_in_prompt": 0,
            "tool_calls_permitted": False,
            "retrieval_permitted": False,
            "network_access_permitted": False,
            "filesystem_access_permitted": False,
            "multi_turn_permitted": False,
            "turns_per_observation": 1,
            "response_shape": "one assistant message, rendered per input.output_contract",
            "sandbox_use": (
                "grader side only; the python_unit scorer runs candidate source in"
                " src/swarm/tools/sandbox_runner.py after the observation is complete"
            ),
        },
        "implementation_pins": {
            "prompt_module": "src/swarm/evals/g13_prompt_v3.py",
            "sandbox_runner_module": "src/swarm/tools/sandbox_runner.py",
        },
    }


def _model_config_schema() -> dict[str, Any]:
    required = [
        "provider",
        "model_id",
        "model_version_or_snapshot",
        "temperature",
        "top_p",
        "max_output_tokens",
        "stop_sequences_present",
        "seed_present",
        "reasoning_effort",
        "system_prompt_present",
        "tool_surface_id",
        "prompt_id",
        "scorer_id",
        "pool_id",
    ]
    return {
        "spec_of": "model_config_schema",
        "identity": {
            "schema_id": "g13-exact-model-config-v3",
            "schema_version": 3,
            "binding": (
                "every counted held-out observation must quote exactly one conforming"
                " exact_model_config object"
            ),
            "exact_model_config_id_rule": (
                "sha256 of json.dumps(exact_model_config, sort_keys=True,"
                " separators=(',',':'), ensure_ascii=True), first 32 hex characters,"
                " prefixed with g13emc3-"
            ),
            "unspecified_field_policy": (
                "no field may be omitted and no field may be null"
            ),
            "required_fields": required,
        },
        "json_schema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "g13-exact-model-config-v3",
            "title": "EVAL-131 exact model configuration, G13 freeze v3",
            "type": "object",
            "additionalProperties": False,
            "required": required,
            "properties": {
                "provider": {"type": "string", "minLength": 1},
                "model_id": {"type": "string", "minLength": 1},
                "model_version_or_snapshot": {"type": "string", "minLength": 1},
                "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                "top_p": {"type": "number", "exclusiveMinimum": 0, "maximum": 1},
                "max_output_tokens": {"type": "integer", "minimum": 1},
                "stop_sequences_present": {"type": "boolean"},
                "seed_present": {"type": "boolean"},
                "reasoning_effort": {"type": "string", "minLength": 1},
                "system_prompt_present": {"type": "boolean"},
                "tool_surface_id": {"type": "string", "minLength": 1},
                "prompt_id": {"type": "string", "const": PROMPT_ID},
                "scorer_id": {"type": "string", "const": "g13-scorer-v3"},
                "pool_id": {"type": "string", "const": FREEZE_ID},
            },
        },
    }


def generate_freeze(root: Path | None = None) -> Path:
    base = (root or repo_root()) / FREEZE_DIR
    holdout = base / HOLDOUT_DIRNAME
    calibration = base / CALIBRATION_DIRNAME
    holdout.mkdir(parents=True, exist_ok=True)
    calibration.mkdir(parents=True, exist_ok=True)
    holdout_records: list[dict[str, Any]] = []
    calibration_records: list[dict[str, Any]] = []
    hidden_index = 1
    shard_rows: list[str] = [
        "# g13-pool-freeze-v3 corpus shard table (split identity)",
        "# format: <product_family> <family> <size> <split> <record_count> <sha256> <shard>",
    ]
    for family in PRODUCT_FAMILIES:
        for size in SIZE_BANDS:
            lines: list[str] = []
            for index, (slug, description) in enumerate(CELL_OBJECTIVES[family][size], start=1):
                hidden_id = f"g13hr3-{hidden_index:04d}"
                hidden_index += 1
                record = build_record(
                    family=family,
                    size=size,
                    index=index,
                    slug=slug,
                    description=description,
                    split=HELD_OUT_SPLIT,
                    hidden_reference_id=hidden_id,
                )
                holdout_records.append(record)
                lines.append(_jsonl_line(record))
            shard_name = f"{family}_{size}.jsonl"
            shard_path = holdout / shard_name
            body = "\n".join(lines) + "\n"
            shard_path.write_text(body, encoding="utf-8")
            shard_rows.append(
                f"{family} {DATASET_FAMILY[family]} {size} {HELD_OUT_SPLIT}"
                f" {len(lines)} {sha256_hex(body.encode('utf-8'))} {HOLDOUT_DIRNAME}/{shard_name}"
            )
            cal_slug = f"calibration_probe_{family}_{size}"
            cal_desc = (
                f"calibration-only {family} {size} probe that must never share ids or"
                f" hashes with the held-out {family}/{size} cell"
            )
            hidden_id = f"g13hr3-{hidden_index:04d}"
            hidden_index += 1
            cal_record = build_record(
                family=family,
                size=size,
                index=1,
                slug=cal_slug,
                description=cal_desc,
                split=CALIBRATION_SPLIT,
                hidden_reference_id=hidden_id,
            )
            calibration_records.append(cal_record)
            cal_name = f"{family}_{size}.jsonl"
            cal_path = calibration / cal_name
            cal_body = _jsonl_line(cal_record) + "\n"
            cal_path.write_text(cal_body, encoding="utf-8")
            shard_rows.append(
                f"{family} {DATASET_FAMILY[family]} {size} {CALIBRATION_SPLIT}"
                f" 1 {sha256_hex(cal_body.encode('utf-8'))} {CALIBRATION_DIRNAME}/{cal_name}"
            )
    table = "\n".join(shard_rows) + "\n"
    (base / SHARD_TABLE_NAME).write_text(table, encoding="utf-8")
    handles = [handle_for(record) for record in holdout_records]
    (base / COMMITMENT_FILENAME).write_text(render_commitment(handles), encoding="utf-8")

    identities = {
        "pool": {
            "spec_of": "pool",
            "identity": {
                "pool_id": FREEZE_ID,
                "freeze_version": FREEZE_VERSION,
                "held_out_record_count": len(holdout_records),
                "calibration_record_count": len(calibration_records),
                "required_cells": 16,
            },
        },
        "records": {
            "spec_of": "records",
            "identity": {
                "records_id": "g13-records-v3",
                "record_count": len(holdout_records),
                "record_schema_version": SCHEMA_VERSION,
                "record_kind": "input_only",
                "record_key_authority": "swarm.evals.g13_prompt_v3.RECORD_KEY_ALLOWLIST",
                "answer_key_policy": "closed denylist applied at every depth",
                "record_digest_algorithm": "sha256",
                "record_digests_stored": False,
            },
        },
        "split": {
            "spec_of": "split",
            "identity": {
                "split_id": "g13-split-v3",
                "held_out_split": HELD_OUT_SPLIT,
                "calibration_split": CALIBRATION_SPLIT,
                "held_out_and_calibration_ids_disjoint": True,
                "shard_table": SHARD_TABLE_NAME,
            },
        },
        "size_classifier": {
            "spec_of": "size_classifier",
            "identity": classifier_identity(),
            "implementation_module": "src/swarm/evals/g13_size_classifier_v3.py",
        },
        "scorer": _scorer_identity(),
        "prompt": {
            "spec_of": "prompt",
            "identity": prompt_identity(),
            "implementation_module": "src/swarm/evals/g13_prompt_v3.py",
        },
        "tool_protocol": _tool_identity(),
        "model_config_schema": _model_config_schema(),
        "independence_checker": {
            "spec_of": "independence_checker",
            "identity": checker_identity(),
            "implementation_module": "src/swarm/evals/g13_independence_v3.py",
        },
        "sealed_reference_interface": {
            "spec_of": "sealed_reference_interface",
            "identity": interface_identity(),
            "implementation_module": "src/swarm/evals/g13_sealed_reference_v3.py",
        },
    }
    for name, spec in identities.items():
        (base / f"identity_{name}_v3.json").write_text(
            json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    identity_paths = {name: f"identity_{name}_v3.json" for name in identities}
    manifest = {
        "freeze_id": FREEZE_ID,
        "freeze_version": FREEZE_VERSION,
        "artifact": "ART-V13-TASK-POOL",
        "packet": "V2B-001-R4",
        "source_and_license": {
            "authoring": "hand_authored_unique_objectives",
            "third_party_source": False,
            "license": "CC0-1.0-equivalent-synthetic-original",
            "license_blocker": False,
            "hidden_answers_in_worker_visible_tree": False,
        },
        "coverage": {
            "required_product_families": list(PRODUCT_FAMILIES),
            "required_sizes": list(SIZE_BANDS),
            "min_independent_archetypes_per_cell": MIN_PER_CELL,
            "min_total_independent_held_out": MIN_TOTAL,
        },
        "identities": identity_paths,
        "corpus": {
            "holdout_dir": HOLDOUT_DIRNAME,
            "calibration_dir": CALIBRATION_DIRNAME,
            "shard_table": SHARD_TABLE_NAME,
            "shard_table_sha256": sha256_hex(table.encode("utf-8")),
            "foreign_corpus_count": 0,
        },
        "reference_bundle": {
            "bundle_id": BUNDLE_ID,
            "interface_id": INTERFACE_ID,
            "id_commitment_file": COMMITMENT_FILENAME,
            "content_digest_binding": {
                "declared_here": False,
                "reason": (
                    "the sealed bundle is not authored on this branch; quoting a"
                    " content digest here would be fabricated"
                ),
            },
        },
        "qualification_readiness": {
            "counted_qualification_ready": False,
            "w131b_started": False,
            "reason": (
                "freeze may become reviewable, but counted qualification stays false"
                " until lead binds a real sealed reference bundle content digest"
            ),
        },
        "wilson": {
            "function": "swarm.evals.wilson.wilson_lower_bound",
            "required_one_sided_90_percent_z": WILSON_COUNTED_Z,
            "thresholds_changed_by_this_packet": False,
        },
    }
    (base / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    checksum_lines = []
    for path in sorted(p for p in base.rglob("*") if p.is_file() and p.name != CHECKSUMS_NAME):
        rel = path.relative_to(base).as_posix()
        checksum_lines.append(f"{file_digest(path)}  {rel}")
    (base / CHECKSUMS_NAME).write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return base


def _load_jsonl(path: Path) -> list[LoadedRecord]:
    loaded: list[LoadedRecord] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        record = json.loads(raw)
        loaded.append(
            LoadedRecord(
                line=raw,
                record=record,
                case_id=str(record["id"]),
                product_family=str(record["product_family"]),
                size=str(record["size"]),
                split=str(record["split"]),
            )
        )
    return loaded


def _independence_record(entry: LoadedRecord, corpus_id: str) -> IndependenceRecord:
    visible = visible_input(entry.record)
    extra = [str(entry.record.get("semantic_archetype_id") or "")]
    return IndependenceRecord(
        corpus_id=corpus_id,
        split=entry.split,
        case_id=entry.case_id,
        payload_digest=visible_payload_digest(visible),
        prompt_digest=rendered_prompt_digest(visible),
        template_digest=sha256_hex(normalise_template(render_prompt(visible)).encode()),
        semantic_archetype_id=str(entry.record["semantic_archetype_id"]),
        scenario_stem=scenario_stripped_stem(render_prompt(visible), extra),
        clauses=clause_texts(list(visible.get("items") or [])),
    )


def verify_freeze(root: Path | None = None) -> FreezeVerification:
    result = FreezeVerification()
    base = (root or repo_root()) / FREEZE_DIR
    manifest_path = base / MANIFEST_NAME
    if not manifest_path.exists():
        result.add("manifest_missing", str(manifest_path))
        return result
    manifest = _as_dict(json.loads(manifest_path.read_text(encoding="utf-8")), "$")
    floating = find_floating_values(manifest)
    for float_path in floating:
        result.add("floating_identity_value", float_path)
    freeze_id = _as_str(_get(manifest, "freeze_id", "$"), "$.freeze_id")
    if freeze_id != FREEZE_ID:
        result.add("freeze_id_mismatch", freeze_id)

    identities = _as_dict(_get(manifest, "identities", "$"), "$.identities")
    for name in REQUIRED_IDENTITIES:
        rel = identities.get(name)
        if not isinstance(rel, str):
            result.add("identity_missing", name)
            continue
        identity_path = base / rel
        if not identity_path.exists():
            result.add("identity_file_missing", rel)
            continue
        spec = json.loads(identity_path.read_text(encoding="utf-8"))
        for nested_float in find_floating_values(spec):
            result.add("floating_identity_value", f"{rel}:{nested_float}")

    coverage = _as_dict(_get(manifest, "coverage", "$"), "$.coverage")
    min_per_cell = _as_int(
        _get(coverage, "min_independent_archetypes_per_cell", "$.coverage"),
        "$.coverage.min_independent_archetypes_per_cell",
    )
    min_total = _as_int(
        _get(coverage, "min_total_independent_held_out", "$.coverage"),
        "$.coverage.min_total_independent_held_out",
    )
    if min_per_cell != MIN_PER_CELL or min_total != MIN_TOTAL:
        result.add(
            "coverage_contract_mismatch",
            f"declared {min_per_cell}/cell and {min_total} total",
        )

    holdout_dir = base / HOLDOUT_DIRNAME
    calibration_dir = base / CALIBRATION_DIRNAME
    holdout: list[LoadedRecord] = []
    calibration: list[LoadedRecord] = []
    if holdout_dir.exists():
        for shard_path in sorted(holdout_dir.glob("*.jsonl")):
            holdout.extend(_load_jsonl(shard_path))
    else:
        result.add("holdout_dir_missing", str(holdout_dir))
    if calibration_dir.exists():
        for shard_path in sorted(calibration_dir.glob("*.jsonl")):
            calibration.extend(_load_jsonl(shard_path))

    answer_leaks = 0
    for entry in [*holdout, *calibration]:
        leaked = find_denylisted_keys(entry.record)
        if leaked:
            answer_leaks += 1
            result.add("answer_key_leak", f"{entry.case_id}: {leaked}")
        try:
            visible = visible_input(entry.record)
        except PromptV3Error as exc:
            result.add("prompt_refuse", f"{entry.case_id}: {exc}")
            continue
        try:
            band = classify(visible)
        except SizeClassifierV3Error as exc:
            result.add("size_classifier_error", f"{entry.case_id}: {exc}")
            continue
        if band != entry.size:
            result.add(
                "size_band_mismatch",
                f"{entry.case_id} declares {entry.size} but classifier returns {band}"
                f" load={derive_features(visible).structural_load()}",
            )

    cell_counts: Counter[str] = Counter(f"{e.product_family}/{e.size}" for e in holdout)
    for family in PRODUCT_FAMILIES:
        for size in SIZE_BANDS:
            cell = f"{family}/{size}"
            if cell_counts.get(cell, 0) < MIN_PER_CELL:
                result.add(
                    "required_cell_below_minimum",
                    f"{cell} holds {cell_counts.get(cell, 0)} records",
                )
    if len(holdout) < MIN_TOTAL:
        result.add("corpus_below_minimum_total", str(len(holdout)))

    holdout_ids = {e.case_id for e in holdout}
    calibration_ids = {e.case_id for e in calibration}
    overlap = holdout_ids & calibration_ids
    if overlap:
        result.add("calibration_holdout_id_overlap", str(sorted(overlap)))
    holdout_hashes = {record_digest(e.line) for e in holdout}
    cal_hashes = {record_digest(e.line) for e in calibration}
    hash_overlap = holdout_hashes & cal_hashes
    if hash_overlap:
        result.add("calibration_holdout_hash_overlap", str(len(hash_overlap)))

    cell_of = {e.case_id: f"{e.product_family}/{e.size}" for e in holdout}
    own = [_independence_record(e, freeze_id) for e in holdout]
    foreign = [_independence_record(e, f"{freeze_id}-calibration") for e in calibration]
    independence = check_independence(
        [*own, *foreign],
        held_out_corpus_id=freeze_id,
        held_out_split=HELD_OUT_SPLIT,
        min_archetypes_per_cell=MIN_PER_CELL,
        cell_of=cell_of,
    )
    for violation in independence.violations:
        result.add(violation.code, violation.detail)

    try:
        handles = [handle_for(e.record) for e in holdout]
        rows = load_commitment(base / COMMITMENT_FILENAME)
        for code, detail in commitment_violations(handles, rows):
            result.add(code, detail)
    except SealedReferenceIdentityError as exc:
        result.add("sealed_reference_identity", str(exc))

    checksums_path = base / CHECKSUMS_NAME
    if checksums_path.exists():
        declared: dict[str, str] = {}
        for line in checksums_path.read_text(encoding="utf-8").splitlines():
            digest, _, rel_name = line.partition("  ")
            declared[rel_name] = digest
        for file_path in sorted(
            p for p in base.rglob("*") if p.is_file() and p.name != CHECKSUMS_NAME
        ):
            rel_name = file_path.relative_to(base).as_posix()
            actual = file_digest(file_path)
            if declared.get(rel_name) != actual:
                result.add("checksum_mismatch", rel_name)
    else:
        result.add("checksums_missing", CHECKSUMS_NAME)

    bundle = _as_dict(_get(manifest, "reference_bundle", "$"), "$.reference_bundle")
    binding = _as_dict(
        _get(bundle, "content_digest_binding", "$.reference_bundle"),
        "$.reference_bundle.content_digest_binding",
    )
    bundle_bound = _as_bool(
        _get(binding, "declared_here", "$.content_digest_binding"),
        "$.content_digest_binding.declared_here",
    )
    if bundle_bound:
        result.add(
            "fabricated_sealed_bundle_digest",
            "content_digest_binding.declared_here must stay false until lead binds a real bundle",
        )
    readiness = _as_dict(
        _get(manifest, "qualification_readiness", "$"), "$.qualification_readiness"
    )
    declared_ready = _as_bool(
        _get(readiness, "counted_qualification_ready", "$.qualification_readiness"),
        "$.qualification_readiness.counted_qualification_ready",
    )
    freeze_ok_before_readiness = result.ok
    computed_ready = freeze_ok_before_readiness and bundle_bound
    if declared_ready != computed_ready:
        result.add(
            "readiness_declaration_mismatch",
            f"declared {declared_ready}, computed {computed_ready}",
        )
    if declared_ready:
        result.add(
            "counted_qualification_ready_must_be_false",
            "lead has not bound a sealed bundle; counted qualification is prohibited",
        )

    result.stats = {
        "freeze_id": freeze_id,
        "held_out_record_count": len(holdout),
        "calibration_record_count": len(calibration),
        "distinct_record_digests": len({record_digest(e.line) for e in holdout}),
        "independent_per_required_cell": dict(sorted(cell_counts.items())),
        "answer_leak_count": answer_leaks,
        "sealed_bundle_content_digest_bound": bundle_bound,
        "counted_qualification_ready_computed": computed_ready,
        "independence": independence.stats,
        "canonical_json_probe": canonical_json({"ok": True}),
    }
    return result
