"""Frozen G13 independence checker, version 3.

v2 fail-closed on id/payload/prompt/normalised-template overlap. It still
accepted scenario-noun substitutions, identifier reseeds that survived as
lowercase names, and cumulative clause-prefix siblings as distinct trials.

v3 adds mechanical semantic-archetype grouping and rejects those sibling
classes. A 15-record cell is independent only when it also has 15 distinct
semantic archetype ids *and* 15 distinct v3 stems.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final

CHECKER_ID: Final[str] = "g13-independence-checker-v3"
CHECKER_VERSION: Final[int] = 3

_SYNTHETIC_IDENTIFIER: Final[re.Pattern[str]] = re.compile(
    r"\b[A-Z]{2,}(?:[-_][A-Za-z0-9]+)*\b"
)
_DIGIT_RUN: Final[re.Pattern[str]] = re.compile(r"[0-9]+")
_NON_ALNUM: Final[re.Pattern[str]] = re.compile(r"[^a-z0-9]+")
IDENTIFIER_PLACEHOLDER: Final[str] = "@"
DIGIT_PLACEHOLDER: Final[str] = "#"

#: Common scenario/domain nouns that v2 used to mint fake independence.
_SCENARIO_NOUNS: Final[frozenset[str]] = frozenset(
    {
        "ledger",
        "telemetry",
        "roster",
        "inventory",
        "pipeline",
        "billing",
        "warehouse",
        "catalog",
        "mailbox",
        "sensor",
        "ticket",
        "invoice",
        "shipment",
        "session",
        "tenant",
        "workspace",
        "cluster",
        "queue",
        "batch",
        "stream",
    }
)


def normalise_template(text: str) -> str:
    without_ids = _SYNTHETIC_IDENTIFIER.sub(IDENTIFIER_PLACEHOLDER, text)
    without_digits = _DIGIT_RUN.sub(DIGIT_PLACEHOLDER, without_ids)
    return without_digits.lower()


def scenario_stripped_stem(text: str, extra_tokens: Iterable[str] = ()) -> str:
    """Collapse scenario-noun and identifier/numeric reseeds to a semantic stem."""
    lowered = normalise_template(text)
    banned = set(_SCENARIO_NOUNS)
    banned.update(token.lower() for token in extra_tokens if token)
    tokens = [part for part in _NON_ALNUM.split(lowered) if part and part not in banned]
    return " ".join(tokens)


def clause_texts(items: Sequence[Any]) -> tuple[str, ...]:
    texts: list[str] = []
    for item in items:
        if isinstance(item, Mapping):
            requirement = item.get("requirement")
            if isinstance(requirement, str):
                texts.append(normalise_template(requirement).strip())
            else:
                texts.append(normalise_template(str(item)).strip())
        else:
            texts.append(normalise_template(str(item)).strip())
    return tuple(t for t in texts if t)


def is_clause_prefix_or_containment(left: Sequence[str], right: Sequence[str]) -> bool:
    if not left or not right or left == right:
        return False
    if len(left) <= len(right) and tuple(right[: len(left)]) == tuple(left):
        return True
    if len(right) <= len(left) and tuple(left[: len(right)]) == tuple(right):
        return True
    left_set, right_set = set(left), set(right)
    return left_set < right_set or right_set < left_set


@dataclass(frozen=True)
class IndependenceRecord:
    corpus_id: str
    split: str
    case_id: str
    payload_digest: str
    prompt_digest: str
    template_digest: str
    semantic_archetype_id: str
    scenario_stem: str
    clauses: tuple[str, ...]

    @property
    def partition(self) -> str:
        return f"{self.corpus_id}:{self.split}"


@dataclass(frozen=True)
class IndependenceViolation:
    code: str
    detail: str

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


@dataclass
class IndependenceReport:
    checker_id: str = CHECKER_ID
    violations: list[IndependenceViolation] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.violations

    def add(self, code: str, detail: str) -> None:
        self.violations.append(IndependenceViolation(code=code, detail=detail))


def _duplicates(
    records: Sequence[IndependenceRecord], attribute: str
) -> list[tuple[str, list[str]]]:
    grouped: dict[str, list[str]] = {}
    for record in records:
        grouped.setdefault(str(getattr(record, attribute)), []).append(record.case_id)
    return [(key, sorted(ids)) for key, ids in sorted(grouped.items()) if len(ids) > 1]


def check_independence(
    records: Iterable[IndependenceRecord],
    *,
    held_out_corpus_id: str,
    held_out_split: str,
    min_archetypes_per_cell: int = 15,
    cell_of: dict[str, str] | None = None,
) -> IndependenceReport:
    report = IndependenceReport()
    all_records = list(records)
    target = f"{held_out_corpus_id}:{held_out_split}"
    held_out = [r for r in all_records if r.partition == target]
    foreign = [r for r in all_records if r.partition != target]
    if not held_out:
        report.add(
            "held_out_partition_empty",
            f"no records in partition {held_out_corpus_id}:{held_out_split}",
        )
        report.stats = {"held_out_count": 0, "foreign_count": len(foreign)}
        return report

    for digest, ids in _duplicates(held_out, "case_id"):
        report.add("holdout_case_id_duplicate", f"case id {digest} used by {len(ids)} records")
    for attribute, label, code in (
        ("payload_digest", "model-visible payload digest", "holdout_payload_digest_duplicate"),
        ("prompt_digest", "rendered prompt digest", "holdout_prompt_digest_duplicate"),
        ("template_digest", "normalised template", "holdout_template_duplicate"),
        (
            "semantic_archetype_id",
            "semantic archetype id",
            "holdout_semantic_archetype_duplicate",
        ),
        ("scenario_stem", "scenario-stripped stem", "holdout_scenario_substitution_sibling"),
    ):
        for digest, ids in _duplicates(held_out, attribute):
            report.add(
                code,
                f"{', '.join(ids)} share a {label} ({digest[:48]}); they are not"
                " independent observations",
            )

    for i, left in enumerate(held_out):
        for right in held_out[i + 1 :]:
            if is_clause_prefix_or_containment(left.clauses, right.clauses):
                report.add(
                    "holdout_clause_prefix_containment_sibling",
                    f"{left.case_id} and {right.case_id} are clause-prefix or"
                    " containment siblings",
                )

    if cell_of:
        by_cell: dict[str, list[IndependenceRecord]] = defaultdict(list)
        for record in held_out:
            cell = cell_of.get(record.case_id)
            if cell:
                by_cell[cell].append(record)
        for cell, group in sorted(by_cell.items()):
            archetypes = {r.semantic_archetype_id for r in group}
            if len(archetypes) < min_archetypes_per_cell:
                report.add(
                    "required_cell_archetype_depth_below_minimum",
                    f"{cell} has {len(archetypes)} distinct semantic archetypes;"
                    f" minimum is {min_archetypes_per_cell}",
                )

    held_out_ids = {r.case_id for r in held_out}
    held_axes = {
        "payload_digest": {r.payload_digest: r.case_id for r in held_out},
        "prompt_digest": {r.prompt_digest: r.case_id for r in held_out},
        "template_digest": {r.template_digest: r.case_id for r in held_out},
        "semantic_archetype_id": {r.semantic_archetype_id: r.case_id for r in held_out},
        "scenario_stem": {r.scenario_stem: r.case_id for r in held_out},
    }
    for record in foreign:
        if record.case_id in held_out_ids:
            report.add(
                "cross_partition_case_id_overlap",
                f"{record.case_id} appears in both {target} and {record.partition}",
            )
        for attribute, code in (
            ("payload_digest", "cross_partition_payload_digest_overlap"),
            ("prompt_digest", "cross_partition_prompt_digest_overlap"),
            ("template_digest", "cross_partition_template_isomorph"),
            ("semantic_archetype_id", "cross_partition_semantic_archetype_overlap"),
            ("scenario_stem", "cross_partition_scenario_stem_overlap"),
        ):
            match = held_axes[attribute].get(getattr(record, attribute))
            if match is not None:
                report.add(
                    code,
                    f"held-out {match} shares {attribute} with {record.case_id} in"
                    f" {record.partition}",
                )

    report.stats = {
        "checker_id": CHECKER_ID,
        "checker_version": CHECKER_VERSION,
        "held_out_count": len(held_out),
        "foreign_count": len(foreign),
        "distinct_held_out_semantic_archetypes": len(
            {r.semantic_archetype_id for r in held_out}
        ),
        "distinct_held_out_scenario_stems": len({r.scenario_stem for r in held_out}),
        "distinct_held_out_templates": len({r.template_digest for r in held_out}),
        "held_out_clause_sibling_pairs": sum(
            1
            for i, left in enumerate(held_out)
            for right in held_out[i + 1 :]
            if is_clause_prefix_or_containment(left.clauses, right.clauses)
        ),
    }
    return report


def checker_identity() -> dict[str, Any]:
    return {
        "checker_id": CHECKER_ID,
        "checker_version": CHECKER_VERSION,
        "mode": "fail_closed",
        "reported_but_tolerated_axis_count": 0,
        "rejects": [
            "semantic-archetype duplicates",
            "scenario-substitution siblings",
            "identifier/numeric reseeds",
            "clause-prefix/containment siblings",
            "payload/prompt/template digest overlap",
        ],
        "normalisation": {
            "synthetic_identifier_pattern": _SYNTHETIC_IDENTIFIER.pattern,
            "digit_run_pattern": _DIGIT_RUN.pattern,
            "scenario_noun_blocklist_count": len(_SCENARIO_NOUNS),
            "case_folding": "lower",
        },
        "intra_holdout_invariants": [
            "holdout_case_id_duplicate",
            "holdout_payload_digest_duplicate",
            "holdout_prompt_digest_duplicate",
            "holdout_template_duplicate",
            "holdout_semantic_archetype_duplicate",
            "holdout_scenario_substitution_sibling",
            "holdout_clause_prefix_containment_sibling",
            "required_cell_archetype_depth_below_minimum",
        ],
        "cross_partition_invariants": [
            "cross_partition_case_id_overlap",
            "cross_partition_payload_digest_overlap",
            "cross_partition_prompt_digest_overlap",
            "cross_partition_template_isomorph",
            "cross_partition_semantic_archetype_overlap",
            "cross_partition_scenario_stem_overlap",
        ],
    }
