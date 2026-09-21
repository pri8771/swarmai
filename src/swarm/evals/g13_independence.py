"""Frozen G13 independence / contamination checker, version 2.

What changed from v1
--------------------
The v1 freeze enforced four invariants (id, record-digest and visible-prompt
overlap across splits, plus duplicate held-out prompts) and *reported* two more
as statistics: ``cross_split_template_isomorphs`` and
``distinct_held_out_templates``. It said so plainly — driving seed-isomorphism to
zero required regenerating the pool, which was out of scope. That left blocker
**B3**: held-out records that differ only in their synthetic identifiers are not
statistically independent, so a Wilson bound over them overstates confidence.

``g13-independence-checker-v2`` is **fail-closed on every one of those axes**.
Nothing is reported-but-tolerated: a normalised-template collision is a
violation, not a statistic.

Enforced invariants
-------------------
Inside the qualification held-out partition:

``holdout_case_id_duplicate``
    two held-out records share a case id.
``holdout_payload_digest_duplicate``
    two held-out records share a model-visible payload digest.
``holdout_prompt_digest_duplicate``
    two held-out records share a rendered-prompt digest.
``holdout_template_duplicate``
    two held-out records share a normalised template — seed-isomorphic
    siblings. They would each be counted as a distinct case by
    ``ProfileStore``, which is exactly the overstatement this rejects.

Between the held-out partition and **every** foreign partition — the v2
screening split, and every split of the burned v1 pool whose answers were
worker-visible:

``cross_partition_case_id_overlap``
``cross_partition_payload_digest_overlap``
``cross_partition_prompt_digest_overlap``
``cross_partition_template_isomorph``

Normalisation
-------------
:func:`normalise_template` reduces a prompt to its structure by erasing the two
things a seeded generator varies for free:

1. synthetic identifier tokens — a run of two or more upper-case letters,
   optionally followed by ``-``/``_``-joined alphanumeric groups (``EV-3``,
   ``ORD-310-001``, ``ING``) — become ``@``;
2. every run of decimal digits becomes ``#``;

and then lower-cases what is left. Two prompts with the same normalised
template differ only in synthetic naming and numbering, so they are treated as
one observation, not two.

The normalisation is deliberately aggressive. A false collision fails the
freeze, which is recoverable; a missed collision silently inflates a
qualification bound, which is not.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Final

CHECKER_ID: Final[str] = "g13-independence-checker-v2"
CHECKER_VERSION: Final[int] = 2

_SYNTHETIC_IDENTIFIER: Final[re.Pattern[str]] = re.compile(
    r"\b[A-Z]{2,}(?:[-_][A-Za-z0-9]+)*\b"
)
_DIGIT_RUN: Final[re.Pattern[str]] = re.compile(r"[0-9]+")

IDENTIFIER_PLACEHOLDER: Final[str] = "@"
DIGIT_PLACEHOLDER: Final[str] = "#"


def normalise_template(text: str) -> str:
    """Erase synthetic identifiers and numbering, then lower-case."""
    without_ids = _SYNTHETIC_IDENTIFIER.sub(IDENTIFIER_PLACEHOLDER, text)
    without_digits = _DIGIT_RUN.sub(DIGIT_PLACEHOLDER, without_ids)
    return without_digits.lower()


@dataclass(frozen=True)
class IndependenceRecord:
    """One record reduced to the identities the checker compares."""

    corpus_id: str
    split: str
    case_id: str
    payload_digest: str
    prompt_digest: str
    template_digest: str

    @property
    def partition(self) -> str:
        return f"{self.corpus_id}:{self.split}"


@dataclass(frozen=True)
class IndependenceViolation:
    """A single independence failure."""

    code: str
    detail: str

    def __str__(self) -> str:  # pragma: no cover - formatting helper
        return f"{self.code}: {self.detail}"


@dataclass
class IndependenceReport:
    """Fail-closed result of an independence check."""

    checker_id: str = CHECKER_ID
    violations: list[IndependenceViolation] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.violations

    def add(self, code: str, detail: str) -> None:
        self.violations.append(IndependenceViolation(code=code, detail=detail))

    def report(self) -> str:
        if self.ok:
            return f"{self.checker_id} OK"
        lines = "\n".join(f"  - {v}" for v in self.violations)
        return f"{self.checker_id} violations:\n{lines}"


_AXES: Final[tuple[tuple[str, str], ...]] = (
    ("payload_digest", "model-visible payload digest"),
    ("prompt_digest", "rendered prompt digest"),
    ("template_digest", "normalised template"),
)


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
) -> IndependenceReport:
    """Verify the qualification held-out partition is independent of everything.

    ``records`` may mix corpora. Exactly one ``(corpus_id, split)`` partition is
    the qualification held-out set; every other partition — including a *foreign
    corpus' own held-out split* — is treated as potentially contaminating, on
    the grounds that a split whose answers were once worker-visible is burned
    and cannot be reused.
    """
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

    # --- inside the held-out partition -----------------------------------
    for digest, ids in _duplicates(held_out, "case_id"):
        report.add("holdout_case_id_duplicate", f"case id {digest} used by {len(ids)} records")
    for attribute, label in _AXES:
        for digest, ids in _duplicates(held_out, attribute):
            code = f"holdout_{'template' if attribute == 'template_digest' else attribute}"
            report.add(
                f"{code}_duplicate",
                f"{', '.join(ids)} share a {label} ({digest[:16]}…); they are not"
                " independent observations",
            )

    # --- held-out against every foreign partition ------------------------
    held_out_ids = {r.case_id for r in held_out}
    held_out_by_axis = {
        attribute: {getattr(r, attribute): r.case_id for r in held_out}
        for attribute, _ in _AXES
    }

    for record in foreign:
        if record.case_id in held_out_ids:
            report.add(
                "cross_partition_case_id_overlap",
                f"{record.case_id} appears in both {held_out_corpus_id}:{held_out_split}"
                f" and {record.partition}",
            )
        for attribute, label in _AXES:
            match = held_out_by_axis[attribute].get(getattr(record, attribute))
            if match is None:
                continue
            code = (
                "cross_partition_template_isomorph"
                if attribute == "template_digest"
                else f"cross_partition_{attribute}_overlap"
            )
            report.add(
                code,
                f"held-out {match} shares a {label} with {record.case_id}"
                f" in {record.partition}",
            )

    partition_sizes: Counter[str] = Counter(r.partition for r in foreign)
    report.stats = {
        "checker_id": CHECKER_ID,
        "checker_version": CHECKER_VERSION,
        "held_out_partition": f"{held_out_corpus_id}:{held_out_split}",
        "held_out_count": len(held_out),
        "foreign_count": len(foreign),
        "foreign_partitions": dict(sorted(partition_sizes.items())),
        "distinct_held_out_case_ids": len({r.case_id for r in held_out}),
        "distinct_held_out_payload_digests": len({r.payload_digest for r in held_out}),
        "distinct_held_out_prompt_digests": len({r.prompt_digest for r in held_out}),
        "distinct_held_out_templates": len({r.template_digest for r in held_out}),
        "held_out_template_collisions": len(_duplicates(held_out, "template_digest")),
        "cross_partition_case_id_overlaps": len(
            {r.case_id for r in foreign if r.case_id in held_out_ids}
        ),
        "cross_partition_payload_overlaps": len(
            {
                r.payload_digest
                for r in foreign
                if r.payload_digest in held_out_by_axis["payload_digest"]
            }
        ),
        "cross_partition_prompt_overlaps": len(
            {
                r.prompt_digest
                for r in foreign
                if r.prompt_digest in held_out_by_axis["prompt_digest"]
            }
        ),
        "cross_partition_template_isomorphs": len(
            {
                r.template_digest
                for r in foreign
                if r.template_digest in held_out_by_axis["template_digest"]
            }
        ),
    }
    return report


def checker_identity() -> dict[str, Any]:
    """Serialisable identity of the frozen v2 independence checker."""
    return {
        "checker_id": CHECKER_ID,
        "checker_version": CHECKER_VERSION,
        "mode": "fail_closed",
        # A count, not an empty list: the freeze verifier treats an empty
        # container in a frozen identity spec as an unfilled slot.
        "reported_but_tolerated_axis_count": 0,
        "normalisation": {
            "synthetic_identifier_pattern": _SYNTHETIC_IDENTIFIER.pattern,
            "synthetic_identifier_placeholder": IDENTIFIER_PLACEHOLDER,
            "digit_run_pattern": _DIGIT_RUN.pattern,
            "digit_run_placeholder": DIGIT_PLACEHOLDER,
            "case_folding": "lower",
            "order": [
                "substitute synthetic identifiers",
                "substitute digit runs",
                "lower-case",
            ],
        },
        "intra_holdout_invariants": [
            "holdout_case_id_duplicate",
            "holdout_payload_digest_duplicate",
            "holdout_prompt_digest_duplicate",
            "holdout_template_duplicate",
        ],
        "cross_partition_invariants": [
            "cross_partition_case_id_overlap",
            "cross_partition_payload_digest_overlap",
            "cross_partition_prompt_digest_overlap",
            "cross_partition_template_isomorph",
        ],
        "foreign_partition_policy": (
            "every partition other than the declared qualification held-out partition is"
            " treated as contaminating, including a foreign corpus' own held-out split:"
            " a split whose reference answers were ever worker-visible is burned"
        ),
    }
