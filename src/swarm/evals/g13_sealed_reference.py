"""Frozen G13 sealed grader-reference interface, version 2.

The v1 freeze recorded, as blocker **B2**, that ``expected_output``, ``grader``,
``reference_solution`` and ``broken_code`` sat in plaintext inside
``benchmarks/starter.jsonl``: any worker with repository read access could read
the held-out answers, which makes a counted qualification run over that split
contestable. This module is the interface that removes the condition rather than
documenting it.

The contract
------------
On the worker-visible branch, a held-out record exposes **only**:

* ``hidden_reference.hidden_reference_id`` — an opaque surrogate key. It is a
  bare index into the sealed bundle's own ordering. It is not derived from, and
  reveals nothing about, the reference content: no length, no shape, no digest
  of the answer.
* ``hidden_reference.interface_id`` — which version of this interface the record
  speaks.

Nothing else is permitted inside the ``hidden_reference`` block
(:data:`HANDLE_KEY_ALLOWLIST`), so there is no field in which an answer, a
grader fixture, a rubric or an answer digest could ride along.

Identity without content
------------------------
The corpus commits ``SEALED_REFERENCE_IDS.txt``: one ``<case_id>
<hidden_reference_id>`` line per held-out record. That file is worker-visible
and answer-free, and its sha256 is the **commitment digest**. A sealed bundle is
only accepted by :func:`resolve` if it quotes the same commitment digest, which
binds the external references to exactly this corpus and this split without
revealing anything about them.

The bundle's own *content* digest is deliberately **not** declared by the freeze:
the bundle is not authored on this branch and must not be, so any content digest
quoted here would be fabricated. It is bound at seal time by the party that
mints the bundle, and :func:`resolve` fails closed until then.

Fail-closed
-----------
:func:`resolve` has no default source. On this branch there is no sealed bundle,
so every call raises :class:`SealedReferenceUnavailable`. There is no fallback
path that reads a local file, and no code path in this module ever returns
reference content it has not been handed by an explicit external source.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Protocol, runtime_checkable

INTERFACE_ID: Final[str] = "g13-sealed-reference-interface-v2"
INTERFACE_VERSION: Final[int] = 2

BUNDLE_ID: Final[str] = "g13-sealed-reference-bundle-v2"

COMMITMENT_FILENAME: Final[str] = "SEALED_REFERENCE_IDS.txt"

#: Opaque surrogate key format: ``g13hr2-`` plus a zero-padded 4-digit index.
HIDDEN_REFERENCE_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^g13hr2-[0-9]{4}$")

#: The only keys a record's ``hidden_reference`` block may carry.
HANDLE_KEY_ALLOWLIST: Final[frozenset[str]] = frozenset({"interface_id", "hidden_reference_id"})

COMMITMENT_HEADER: Final[tuple[str, ...]] = (
    "# g13-sealed-reference-interface-v2 hidden-reference id commitment",
    "# format: <case_id> <hidden_reference_id>",
    "# contains opaque surrogate keys only: no reference answer, no grader"
    " fixture, no rubric, no answer digest",
    "# order: corpus canonical order (product_family, size, record index)",
)


class SealedReferenceUnavailable(RuntimeError):
    """Raised when reference content is requested and no sealed source exists."""


class SealedReferenceIdentityError(ValueError):
    """Raised when hidden-reference identity is missing, malformed or mismatched."""


@dataclass(frozen=True)
class HiddenReferenceHandle:
    """Everything the worker-visible branch knows about one hidden reference."""

    case_id: str
    hidden_reference_id: str
    interface_id: str


@runtime_checkable
class SealedReferenceSource(Protocol):
    """A sealed bundle, supplied by the qualification harness, never by a worker."""

    bundle_id: str
    commitment_sha256: str

    def fetch(self, hidden_reference_id: str) -> Mapping[str, Any]:
        """Return the reference record for an opaque id."""


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def handle_for(record: Mapping[str, Any]) -> HiddenReferenceHandle:
    """Build the handle for one corpus record, refusing anything malformed."""
    case_id = record.get("id")
    if not isinstance(case_id, str) or not case_id:
        raise SealedReferenceIdentityError("record.id: expected a non-empty string")
    block = record.get("hidden_reference")
    if not isinstance(block, Mapping):
        raise SealedReferenceIdentityError(f"{case_id}: hidden_reference block is absent")
    extra = sorted(str(k) for k in block if str(k) not in HANDLE_KEY_ALLOWLIST)
    if extra:
        raise SealedReferenceIdentityError(
            f"{case_id}: hidden_reference carries keys outside the allowlist: {extra}"
        )
    interface_id = block.get("interface_id")
    if interface_id != INTERFACE_ID:
        raise SealedReferenceIdentityError(
            f"{case_id}: hidden_reference.interface_id is {interface_id!r},"
            f" expected {INTERFACE_ID!r}"
        )
    hidden_reference_id = block.get("hidden_reference_id")
    if not isinstance(hidden_reference_id, str) or not HIDDEN_REFERENCE_ID_PATTERN.match(
        hidden_reference_id
    ):
        raise SealedReferenceIdentityError(
            f"{case_id}: hidden_reference_id {hidden_reference_id!r} is not an opaque"
            " g13hr2-NNNN surrogate key"
        )
    return HiddenReferenceHandle(
        case_id=case_id,
        hidden_reference_id=hidden_reference_id,
        interface_id=interface_id,
    )


def render_commitment(handles: list[HiddenReferenceHandle]) -> str:
    """Render ``SEALED_REFERENCE_IDS.txt`` exactly as it is committed."""
    lines = list(COMMITMENT_HEADER)
    lines.extend(f"{h.case_id} {h.hidden_reference_id}" for h in handles)
    return "\n".join(lines) + "\n"


def load_commitment(path: Path) -> list[tuple[str, str]]:
    """Parse ``<case_id> <hidden_reference_id>`` rows in file order."""
    if not path.exists():
        raise SealedReferenceIdentityError(f"id commitment file not found: {path}")
    rows: list[tuple[str, str]] = []
    for line_no, raw in enumerate(path.read_bytes().decode("utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            raise SealedReferenceIdentityError(f"{path}:{line_no}: malformed row {raw!r}")
        if not HIDDEN_REFERENCE_ID_PATTERN.match(parts[1]):
            raise SealedReferenceIdentityError(
                f"{path}:{line_no}: {parts[1]!r} is not an opaque g13hr2-NNNN surrogate key"
            )
        rows.append((parts[0], parts[1]))
    return rows


def commitment_violations(
    handles: list[HiddenReferenceHandle], rows: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    """``(code, detail)`` pairs for every hidden-reference identity defect."""
    problems: list[tuple[str, str]] = []

    seen_ids: dict[str, str] = {}
    for handle in handles:
        clash = seen_ids.get(handle.hidden_reference_id)
        if clash is not None:
            problems.append(
                (
                    "hidden_reference_id_duplicate",
                    f"{handle.hidden_reference_id} is used by {clash} and {handle.case_id}",
                )
            )
            continue
        seen_ids[handle.hidden_reference_id] = handle.case_id

    committed = dict(rows)
    if len(committed) != len(rows):
        problems.append(
            ("commitment_duplicate_case", f"{len(rows) - len(committed)} duplicated case rows")
        )
    committed_ids: dict[str, str] = {}
    for case_id, reference_id in rows:
        clash = committed_ids.get(reference_id)
        if clash is not None:
            problems.append(
                (
                    "commitment_duplicate_reference_id",
                    f"{reference_id} is committed for both {clash} and {case_id}",
                )
            )
            continue
        committed_ids[reference_id] = case_id

    by_case = {h.case_id: h.hidden_reference_id for h in handles}
    for case_id in sorted(set(by_case) - set(committed)):
        problems.append(
            ("hidden_reference_not_committed", f"{case_id} has no row in the id commitment")
        )
    for case_id in sorted(set(committed) - set(by_case)):
        problems.append(
            ("commitment_case_not_in_corpus", f"{case_id} is committed but not in the corpus")
        )
    for case_id in sorted(set(by_case) & set(committed)):
        if by_case[case_id] != committed[case_id]:
            problems.append(
                (
                    "hidden_reference_id_mismatch",
                    f"{case_id}: record says {by_case[case_id]},"
                    f" commitment says {committed[case_id]}",
                )
            )
    return problems


def resolve(
    handle: HiddenReferenceHandle,
    source: SealedReferenceSource | None = None,
    *,
    expected_commitment_sha256: str | None = None,
) -> Mapping[str, Any]:
    """Resolve one hidden reference, or fail closed.

    There is no default source and no local fallback. On the worker-visible
    branch ``source`` is always ``None``, so this always raises. That is the
    point: the held-out references are not reachable from here.
    """
    if source is None:
        raise SealedReferenceUnavailable(
            f"{handle.case_id}: hidden reference {handle.hidden_reference_id} lives in"
            f" sealed bundle {BUNDLE_ID}, which is not present on the worker-visible"
            " branch. Supply a SealedReferenceSource from the qualification harness."
        )
    if source.bundle_id != BUNDLE_ID:
        raise SealedReferenceIdentityError(
            f"sealed source declares bundle {source.bundle_id!r}, expected {BUNDLE_ID!r}"
        )
    if expected_commitment_sha256 is None:
        raise SealedReferenceIdentityError(
            "refusing to resolve without an expected commitment digest: an unbound"
            " bundle cannot be shown to describe this corpus and this split"
        )
    if source.commitment_sha256 != expected_commitment_sha256:
        raise SealedReferenceIdentityError(
            f"sealed bundle commitment digest {source.commitment_sha256} does not match"
            f" the frozen commitment {expected_commitment_sha256}"
        )
    return source.fetch(handle.hidden_reference_id)


def interface_identity() -> dict[str, Any]:
    """Serialisable identity of the frozen sealed-reference interface."""
    return {
        "interface_id": INTERFACE_ID,
        "interface_version": INTERFACE_VERSION,
        "bundle_id": BUNDLE_ID,
        "worker_visible_fields": sorted(HANDLE_KEY_ALLOWLIST),
        "hidden_reference_id_pattern": HIDDEN_REFERENCE_ID_PATTERN.pattern,
        "hidden_reference_id_kind": "opaque_surrogate_key",
        "hidden_reference_id_derived_from_reference_content": False,
        "commitment_file": COMMITMENT_FILENAME,
        "commitment_digest_algorithm": "sha256",
        "reference_content_location": "outside_the_worker_visible_branch",
        "reference_content_digest_declared_by_this_freeze": False,
        "reference_content_digest_reason": (
            "the sealed bundle is not authored by this packet and must not be, so a"
            " content digest quoted here would be fabricated. It is bound at seal time"
            " by whoever mints the bundle."
        ),
        "resolver_default_source_present": False,
        "resolver_behaviour_without_source": "raise SealedReferenceUnavailable",
        "resolver_requires_commitment_match": True,
        "local_fallback_paths": 0,
    }
