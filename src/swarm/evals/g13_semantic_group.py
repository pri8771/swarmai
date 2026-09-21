"""Frozen G13 semantic archetype / independence-group axis, version 1.

Why this axis exists
--------------------
``g13-independence-checker-v2`` is fail-closed on eight digest and
normalised-template axes, and it stays exactly as it is: nothing here weakens
it. But it compares *strings*, and three cheap transformations produce a string
it has never seen while producing no new information:

``scenario / domain rename``
    the same recipe re-emitted with one domain noun swapped
    (``... for the harbor ledger ...`` -> ``... for the orchard ledger ...``).
    Normalisation erases upper-case identifier tokens and digit runs, so a
    lower-case noun survives it untouched.
``numeric / seed / synthetic-id substitution``
    ``ORD-310-001`` -> ``ORD-998-777``, ``43 units`` -> ``51 units``. The v2
    normaliser already collapses these, so this axis inherits that property
    rather than re-deriving it.
``cumulative clause-only growth``
    the same recipe with more clauses bolted on, so the larger record's clause
    list is a superset of the smaller one's. Arity changes, so every
    equality-based axis sees two distinct records.

A Wilson bound counts observations. Fifteen re-skins of one recipe are one
observation repeated, not fifteen, so a bound over them overstates confidence.
That is v1 blocker **B3** at a level string equality cannot see, and it is the
defect this axis closes.

The rule
--------
A record is reduced to two things:

``recipe digest``
    the ordered content tokens of ``task``, ``instruction``, ``question`` and
    ``signature``, plus the token form of the output contract.
``clause digests``
    one digest per entry of ``items``, ``constraints`` and ``distractors``,
    tagged with the section it came from, so an item can never cancel a
    constraint.

Two records are **siblings** when their recipe digests are equal *and* one's
clause-digest set is contained in the other's (equality included). Siblings are
unioned; a semantic group is a connected component of that relation. A cell's
group count is the number of distinct components its records fall into.

Containment — not equality — is what makes cumulative clause growth collapse:
the S record's clauses are a subset of the XL record's, so they are one group.

Normalisation, and why the declared ``scenario`` cannot inflate a count
-----------------------------------------------------------------------
Before tokenising, the axis erases synthetic identifiers and digit runs exactly
as ``g13-independence-checker-v2`` does, lower-cases, drops tokens shorter than
:data:`MIN_TOKEN_LENGTH`, drops :data:`STOPWORDS`, and drops every token in the
**corpus-wide scenario vocabulary** — the union of every ``scenario`` slug
declared anywhere in the corpus, not just this record's own.

That last point is the load-bearing one. Erasing a token can only make two
records look *more* alike, so it can only merge groups, never split them. A
record cannot manufacture a new group by declaring a convenient scenario,
because every other record's scenario noun is erased from it too. And a record
whose declared scenario does not occur in its own rendered prompt is refused
outright (:data:`SemanticGroupError`), so the declaration stays bound to the
content it names.

Fail-closed
-----------
Every reduction failure raises. A record that cannot be reduced is not silently
skipped and does not silently count as its own group: the freeze verifier turns
the exception into a ``semantic_group_unreducible`` violation, and a cell that
cannot reach :data:`MIN_SEMANTIC_GROUPS_PER_CELL` distinct groups fails the
freeze however many records it holds.

What this axis deliberately does **not** claim
----------------------------------------------
It is a lexical axis, not a semantic model. Two genuinely different tasks
phrased with the same content words are one group here, which is the safe
direction. Two tasks that share a recipe but whose clause sets merely overlap —
neither containing the other — are two groups, so an adversary willing to
re-author clauses rather than append them can still buy a group. Closing that
needs a model, not a digest; it is recorded as a residual limitation rather than
papered over.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from swarm.evals.g13_prompt_v2 import (
    PromptV2Error,
    canonical_json,
    render_prompt,
    sha256_hex,
    visible_input,
)

GROUP_AXIS_ID: Final[str] = "g13-semantic-group-axis-v1"
GROUP_AXIS_VERSION: Final[int] = 1

#: Protocol floor. A required cell below this many distinct semantic groups
#: fails the freeze regardless of how many records it holds.
MIN_SEMANTIC_GROUPS_PER_CELL: Final[int] = 15

#: Same two erasures the v2 independence normaliser applies, so this axis is
#: never *less* tolerant of seed isomorphism than the axis it sits beside.
_SYNTHETIC_IDENTIFIER: Final[re.Pattern[str]] = re.compile(
    r"\b[A-Z]{2,}(?:[-_][A-Za-z0-9]+)*\b"
)
_DIGIT_RUN: Final[re.Pattern[str]] = re.compile(r"[0-9]+")
_WORD: Final[re.Pattern[str]] = re.compile(r"[a-z]+")

#: A ``scenario`` must be a lower-case slug. Anything else is refused, because a
#: free-form scenario string could smuggle content words out of the vocabulary.
_SCENARIO_SLUG: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_]{2,31}$")

#: Tokens shorter than this carry no archetype information.
MIN_TOKEN_LENGTH: Final[int] = 3

#: Function words. Held as a sorted tuple, not a set literal, so the frozen
#: identity spec can mirror it in a fixed order.
STOPWORD_SEQUENCE: Final[tuple[str, ...]] = (
    "all",
    "and",
    "any",
    "are",
    "below",
    "but",
    "can",
    "each",
    "every",
    "for",
    "from",
    "has",
    "have",
    "into",
    "its",
    "not",
    "one",
    "only",
    "other",
    "our",
    "out",
    "per",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "use",
    "used",
    "using",
    "was",
    "were",
    "what",
    "when",
    "which",
    "while",
    "with",
    "you",
    "your",
)
STOPWORDS: Final[frozenset[str]] = frozenset(STOPWORD_SEQUENCE)

#: The record sections that contribute clause digests, in a fixed order. The
#: section name is part of each digest, so moving a clause between sections
#: changes it.
CLAUSE_SECTIONS: Final[tuple[str, ...]] = ("items", "constraints", "distractors")

#: The head fields that contribute to the recipe digest, in a fixed order.
RECIPE_FIELDS: Final[tuple[str, ...]] = ("task", "instruction", "question", "signature")


class SemanticGroupError(ValueError):
    """Raised when a record cannot be reduced to a semantic fingerprint."""


@dataclass(frozen=True)
class SemanticFingerprint:
    """One record reduced to the two things the sibling rule compares."""

    case_id: str
    cell: str
    recipe_digest: str
    clause_digests: frozenset[str]


def scenario_tokens(scenario: str) -> tuple[str, ...]:
    """Content tokens of one declared ``scenario`` slug."""
    return tuple(
        token for token in _WORD.findall(scenario.lower()) if len(token) >= MIN_TOKEN_LENGTH
    )


def corpus_scenario_vocabulary(records: Iterable[Mapping[str, Any]]) -> frozenset[str]:
    """Every scenario token declared anywhere in the corpus.

    Records with no usable ``scenario`` contribute nothing here; they are
    refused later by :func:`semantic_fingerprint`, which is where the failure
    belongs.
    """
    vocabulary: set[str] = set()
    for record in records:
        scenario = record.get("scenario")
        if isinstance(scenario, str) and _SCENARIO_SLUG.match(scenario):
            vocabulary.update(scenario_tokens(scenario))
    return frozenset(vocabulary)


def semantic_tokens(text: str, vocabulary: frozenset[str]) -> tuple[str, ...]:
    """Ordered content tokens of ``text`` under this axis' normalisation."""
    without_ids = _SYNTHETIC_IDENTIFIER.sub(" ", text)
    without_digits = _DIGIT_RUN.sub(" ", without_ids)
    return tuple(
        token
        for token in _WORD.findall(without_digits.lower())
        if len(token) >= MIN_TOKEN_LENGTH
        and token not in STOPWORDS
        and token not in vocabulary
    )


def _clause_text(value: Any) -> str:
    """Render one clause exactly as ``render_prompt`` shows it to the model."""
    return value if isinstance(value, str) else canonical_json(value)


def _contract_tokens(
    case_id: str, contract: Any, vocabulary: frozenset[str]
) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        raise SemanticGroupError(f"{case_id}: input.output_contract must be an object")
    fields = contract.get("fields")
    if not isinstance(fields, list) or not fields:
        raise SemanticGroupError(
            f"{case_id}: input.output_contract.fields must be a non-empty array"
        )
    return {
        "format": list(semantic_tokens(str(contract.get("format", "")), vocabulary)),
        "fields": sorted(
            canonical_json(list(semantic_tokens(str(field), vocabulary))) for field in fields
        ),
        "sort_by": list(semantic_tokens(str(contract.get("sort_by", "")), vocabulary)),
    }


def semantic_fingerprint(
    record: Mapping[str, Any], *, cell: str, vocabulary: frozenset[str]
) -> SemanticFingerprint:
    """Reduce one corpus record to its semantic fingerprint, or refuse."""
    case_id = record.get("id")
    if not isinstance(case_id, str) or not case_id:
        raise SemanticGroupError("record.id: expected a non-empty string")

    scenario = record.get("scenario")
    if not isinstance(scenario, str) or not _SCENARIO_SLUG.match(scenario):
        raise SemanticGroupError(
            f"{case_id}: scenario must be a lower-case slug, got {scenario!r}"
        )

    try:
        visible = visible_input(record)
        prompt = render_prompt(visible)
    except PromptV2Error as exc:
        raise SemanticGroupError(f"{case_id}: {exc}") from exc

    if scenario.lower() not in prompt.lower():
        raise SemanticGroupError(
            f"{case_id}: declared scenario {scenario!r} does not occur in the rendered"
            " prompt, so the declaration is not bound to the content it names"
        )

    head = [
        list(semantic_tokens(str(visible.get(name, "")), vocabulary)) for name in RECIPE_FIELDS
    ]
    recipe = canonical_json(
        {
            "axis": GROUP_AXIS_ID,
            "axis_version": GROUP_AXIS_VERSION,
            "head": head,
            "contract": _contract_tokens(case_id, visible.get("output_contract"), vocabulary),
        }
    )

    clause_digests: set[str] = set()
    for section in CLAUSE_SECTIONS:
        raw = visible.get(section)
        if raw is None:
            continue
        if not isinstance(raw, list):
            raise SemanticGroupError(f"{case_id}: input.{section} must be an array")
        for value in raw:
            tokens = semantic_tokens(_clause_text(value), vocabulary)
            if not tokens:
                continue
            clause_digests.add(
                sha256_hex(canonical_json([section, list(tokens)]).encode("utf-8"))
            )
    if not clause_digests:
        raise SemanticGroupError(
            f"{case_id}: no clause survives normalisation, so the record carries no"
            " archetype content this axis can measure"
        )

    return SemanticFingerprint(
        case_id=case_id,
        cell=cell,
        recipe_digest=sha256_hex(recipe.encode("utf-8")),
        clause_digests=frozenset(clause_digests),
    )


def are_siblings(left: SemanticFingerprint, right: SemanticFingerprint) -> bool:
    """True when two fingerprints are the same archetype under this axis."""
    if left.recipe_digest != right.recipe_digest:
        return False
    return (
        left.clause_digests <= right.clause_digests
        or right.clause_digests <= left.clause_digests
    )


def assign_groups(fingerprints: Sequence[SemanticFingerprint]) -> dict[str, str]:
    """Map every case id to its semantic group label.

    The label is the lexicographically smallest case id in the component, so the
    labelling is stable under input order.
    """
    parent: dict[str, str] = {}
    for item in fingerprints:
        if item.case_id in parent:
            raise SemanticGroupError(f"{item.case_id}: duplicate case id in the group axis")
        parent[item.case_id] = item.case_id

    def find(case_id: str) -> str:
        root = case_id
        while parent[root] != root:
            root = parent[root]
        while parent[case_id] != root:
            parent[case_id], case_id = root, parent[case_id]
        return root

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root == right_root:
            return
        if left_root < right_root:
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    buckets: dict[str, list[SemanticFingerprint]] = {}
    for item in fingerprints:
        buckets.setdefault(item.recipe_digest, []).append(item)
    for bucket in buckets.values():
        for index, left in enumerate(bucket):
            for right in bucket[index + 1 :]:
                if are_siblings(left, right):
                    union(left.case_id, right.case_id)

    members: dict[str, list[str]] = {}
    for item in fingerprints:
        members.setdefault(find(item.case_id), []).append(item.case_id)
    labels: dict[str, str] = {}
    for ids in members.values():
        label = min(ids)
        for case_id in ids:
            labels[case_id] = label
    return labels


def groups_per_cell(fingerprints: Sequence[SemanticFingerprint]) -> dict[str, int]:
    """Distinct semantic group count per cell, in sorted cell order."""
    labels = assign_groups(fingerprints)
    per_cell: dict[str, set[str]] = {}
    for item in fingerprints:
        per_cell.setdefault(item.cell, set()).add(labels[item.case_id])
    return {cell: len(groups) for cell, groups in sorted(per_cell.items())}


def group_axis_identity() -> dict[str, Any]:
    """Serialisable identity of the frozen semantic-group axis."""
    return {
        "group_axis_id": GROUP_AXIS_ID,
        "group_axis_version": GROUP_AXIS_VERSION,
        "mode": "fail_closed",
        "min_semantic_groups_per_required_cell": MIN_SEMANTIC_GROUPS_PER_CELL,
        "group_key_source": "derived_from_model_visible_payload",
        # An explicit false, not an omission: a record may not declare its own
        # group, because a declaration is exactly what a re-skin would forge.
        "records_declare_their_own_group": False,
        "normalisation": {
            "synthetic_identifier_pattern": _SYNTHETIC_IDENTIFIER.pattern,
            "digit_run_pattern": _DIGIT_RUN.pattern,
            "word_pattern": _WORD.pattern,
            "case_folding": "lower",
            "min_token_length": MIN_TOKEN_LENGTH,
            "stopwords": list(STOPWORD_SEQUENCE),
            "scenario_vocabulary": "corpus_wide_union_of_every_declared_scenario_slug",
            "scenario_slug_pattern": _SCENARIO_SLUG.pattern,
            "order": [
                "erase synthetic identifiers",
                "erase digit runs",
                "lower-case",
                "split into words",
                "drop tokens shorter than min_token_length",
                "drop stopwords",
                "drop corpus-wide scenario vocabulary",
            ],
        },
        "recipe_fields": list(RECIPE_FIELDS),
        "clause_sections": list(CLAUSE_SECTIONS),
        "sibling_rule": (
            "equal recipe digests AND one clause-digest set contained in the other"
            " (equality included); groups are connected components of that relation"
        ),
        "transformations_that_must_not_create_a_group": [
            "scenario or domain rename",
            "numeric, seed or synthetic-identifier substitution",
            "cumulative clause-only growth from one recipe",
        ],
        "refusals": [
            "record.id absent or empty",
            "scenario absent or not a lower-case slug",
            "declared scenario absent from the record's own rendered prompt",
            "input.output_contract missing, or its fields array empty",
            "a clause section that is not an array",
            "no clause survives normalisation",
            "duplicate case id inside the axis",
        ],
        "weakens_existing_axes": False,
        "residual_limitation": (
            "lexical, not semantic: two records sharing a recipe whose clause sets merely"
            " overlap without containment are counted as two groups, so re-authored (not"
            " appended) clauses can still buy a group"
        ),
    }
