"""V2B-001-R4 G13 v3 freeze and independence checker tests."""

from __future__ import annotations

import json
from pathlib import Path

from swarm.evals.g13_independence_v3 import (
    IndependenceRecord,
    check_independence,
    is_clause_prefix_or_containment,
    scenario_stripped_stem,
)
from swarm.evals.g13_prompt_v3 import PromptV3Error, find_denylisted_keys, visible_input
from swarm.evals.g13_sealed_reference_v3 import SealedReferenceUnavailable, resolve
from swarm.evals.task_pool_freeze_v3 import (
    FREEZE_ID,
    MIN_PER_CELL,
    MIN_TOTAL,
    build_record,
    generate_freeze,
    verify_freeze,
)

ROOT = Path(__file__).resolve().parents[2]


def _record(
    *,
    case_id: str,
    archetype: str,
    stem: str,
    clauses: tuple[str, ...],
    split: str = "holdout",
) -> IndependenceRecord:
    return IndependenceRecord(
        corpus_id=FREEZE_ID,
        split=split,
        case_id=case_id,
        payload_digest=f"payload-{case_id}",
        prompt_digest=f"prompt-{case_id}",
        template_digest=f"template-{case_id}",
        semantic_archetype_id=archetype,
        scenario_stem=stem,
        clauses=clauses,
    )


def test_scenario_substitution_siblings_are_rejected() -> None:
    ledger = "write one pure python function for the ledger pipeline that sums amounts"
    telemetry = "write one pure python function for the telemetry pipeline that sums amounts"
    assert scenario_stripped_stem(ledger) == scenario_stripped_stem(telemetry)
    report = check_independence(
        [
            _record(case_id="a", archetype="arch.a", stem=scenario_stripped_stem(ledger), clauses=("x",)),
            _record(
                case_id="b",
                archetype="arch.b",
                stem=scenario_stripped_stem(telemetry),
                clauses=("y",),
            ),
        ],
        held_out_corpus_id=FREEZE_ID,
        held_out_split="holdout",
        cell_of={"a": "coding/S", "b": "coding/S"},
        min_archetypes_per_cell=1,
    )
    assert any(v.code == "holdout_scenario_substitution_sibling" for v in report.violations)


def test_numeric_reseed_and_identifier_templates_are_rejected() -> None:
    report = check_independence(
        [
            _record(
                case_id="a",
                archetype="arch.a",
                stem="stem a",
                clauses=("alpha",),
            ),
            _record(
                case_id="b",
                archetype="arch.b",
                stem="stem b",
                clauses=("beta",),
            ),
        ],
        held_out_corpus_id=FREEZE_ID,
        held_out_split="holdout",
        min_archetypes_per_cell=1,
    )
    # Force a template collision by rebuilding with shared digest.
    collided = [
        _record(case_id="a", archetype="arch.a", stem="stem a", clauses=("alpha",)),
        IndependenceRecord(
            corpus_id=FREEZE_ID,
            split="holdout",
            case_id="b",
            payload_digest="payload-b",
            prompt_digest="prompt-b",
            template_digest="template-a",  # same as default template-{case} only if we set equal
            semantic_archetype_id="arch.b",
            scenario_stem="stem b",
            clauses=("beta",),
        ),
    ]
    collided[0] = IndependenceRecord(
        corpus_id=FREEZE_ID,
        split="holdout",
        case_id="a",
        payload_digest="payload-a",
        prompt_digest="prompt-a",
        template_digest="shared-template",
        semantic_archetype_id="arch.a",
        scenario_stem="stem a",
        clauses=("alpha",),
    )
    collided[1] = IndependenceRecord(
        corpus_id=FREEZE_ID,
        split="holdout",
        case_id="b",
        payload_digest="payload-b",
        prompt_digest="prompt-b",
        template_digest="shared-template",
        semantic_archetype_id="arch.b",
        scenario_stem="stem b",
        clauses=("beta",),
    )
    report = check_independence(
        collided, held_out_corpus_id=FREEZE_ID, held_out_split="holdout", min_archetypes_per_cell=1
    )
    assert any(v.code == "holdout_template_duplicate" for v in report.violations)


def test_clause_prefix_and_containment_siblings_are_rejected() -> None:
    assert is_clause_prefix_or_containment(("keep empty",), ("keep empty", "also skip"))
    report = check_independence(
        [
            _record(case_id="a", archetype="arch.a", stem="stem a", clauses=("keep empty",)),
            _record(
                case_id="b",
                archetype="arch.b",
                stem="stem b",
                clauses=("keep empty", "also skip negatives"),
            ),
        ],
        held_out_corpus_id=FREEZE_ID,
        held_out_split="holdout",
        min_archetypes_per_cell=1,
    )
    assert any(v.code == "holdout_clause_prefix_containment_sibling" for v in report.violations)


def test_fifteen_records_with_five_archetypes_fail() -> None:
    records = []
    cell_of = {}
    for i in range(15):
        case_id = f"c{i:02d}"
        records.append(
            _record(
                case_id=case_id,
                archetype=f"arch.{i % 5}",
                stem=f"stem {i}",
                clauses=(f"clause {i}",),
            )
        )
        cell_of[case_id] = "coding/S"
    report = check_independence(
        records,
        held_out_corpus_id=FREEZE_ID,
        held_out_split="holdout",
        min_archetypes_per_cell=15,
        cell_of=cell_of,
    )
    assert any(v.code == "required_cell_archetype_depth_below_minimum" for v in report.violations)
    assert any(v.code == "holdout_semantic_archetype_duplicate" for v in report.violations)


def test_hidden_answer_keys_are_refused() -> None:
    record = build_record(
        family="coding",
        size="S",
        index=1,
        slug="unit_test_probe",
        description="probe record",
        split="holdout",
        hidden_reference_id="g13hr3-0001",
    )
    leaked = dict(record)
    leaked["expected_output"] = "secret"
    assert find_denylisted_keys(leaked)
    try:
        visible_input(leaked)
        raise AssertionError("contaminated record must not render")
    except PromptV3Error:
        pass


def test_sealed_resolver_has_no_local_fallback() -> None:
    record = build_record(
        family="extraction",
        size="S",
        index=1,
        slug="probe_extract",
        description="probe",
        split="holdout",
        hidden_reference_id="g13hr3-0001",
    )
    from swarm.evals.g13_sealed_reference_v3 import handle_for

    handle = handle_for(record)
    try:
        resolve(handle, source=None, expected_commitment_sha256="abc")
        raise AssertionError("resolver must fail closed")
    except SealedReferenceUnavailable:
        pass


def test_generated_v3_freeze_verifies_and_stays_unready(tmp_path: Path) -> None:
    generate_freeze(tmp_path)
    result = verify_freeze(tmp_path)
    assert result.ok, result.report()
    assert result.stats["held_out_record_count"] == MIN_TOTAL
    assert result.stats["calibration_record_count"] == 16
    assert result.stats["sealed_bundle_content_digest_bound"] is False
    assert result.stats["counted_qualification_ready_computed"] is False
    independence = result.stats["independence"]
    assert independence["distinct_held_out_semantic_archetypes"] == MIN_TOTAL
    for count in result.stats["independent_per_required_cell"].values():
        assert count == MIN_PER_CELL


def test_repo_freeze_if_present() -> None:
    freeze_dir = ROOT / "benchmarks" / "g13" / "pool_freeze_v3"
    if not freeze_dir.exists():
        return
    result = verify_freeze(ROOT)
    assert result.ok, result.report()
    manifest = json.loads((freeze_dir / "task_pool_freeze_v3.manifest.json").read_text())
    assert manifest["qualification_readiness"]["counted_qualification_ready"] is False
    assert manifest["qualification_readiness"]["w131b_started"] is False
