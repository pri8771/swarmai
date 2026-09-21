"""ART-V13-TASK-POOL — ``g13-pool-freeze-v2`` freeze verification (fail-closed).

This is the executable half of the v2 freeze. The declarative half lives under
``benchmarks/g13/pool_freeze_v2/``:

``task_pool_freeze_v2.manifest.json``
    freeze identity, corpus identity, coverage, the sealed-reference binding,
    the declared foreign corpora, and the ten pinned identities.
``holdout/<product_family>_<size>.jsonl``
    the held-out corpus, sharded one file per required cell. Records are
    **input-only**: there is no field in a v2 record that can hold an answer, a
    grader fixture, a rubric or a reference — see ``g13_prompt_v2``.
``CORPUS_SHARD_DIGESTS.txt``
    the split identity: one row per shard binding
    ``(product_family, family, size, split, record_count, sha256)``.
``SEALED_REFERENCE_IDS.txt``
    the hidden-reference id commitment: opaque surrogate keys only.
``SHA256SUMS``
    cover digest over every file in the freeze directory, recursively.

Why per-record digests are not stored
-------------------------------------
v1 stored 224 per-record digests. v2 does not, for the reason v1 already gave
for *derived* digests: each shard is byte-pinned by ``CORPUS_SHARD_DIGESTS.txt``,
whose own digest is pinned by the manifest, whose digest is pinned by
``SHA256SUMS``. Every record's bytes are therefore already pinned exactly, and
the record's position is pinned by the declared canonical order. A second
per-record list would only add a place to drift. The verifier recomputes record,
payload, prompt and normalised-template digests at verification time, which is
where the contamination decisions are actually made.

Two independence axes, not one
------------------------------
``g13-independence-checker-v2`` runs exactly as it always has: eight fail-closed
id / payload-digest / prompt-digest / normalised-template invariants, inside the
held-out partition and against every foreign partition. Nothing here relaxes it.

``g13-semantic-group-axis-v1`` is stacked **on top** of it, because record depth
is not archetype depth. Fifteen records that differ only by a domain noun, by a
seed, or by extra appended clauses are one observation repeated fifteen times,
and every string-equality axis sees fifteen distinct records. The group axis
reduces each record to a recipe digest plus a clause-digest set, treats
recipe-equal records whose clause sets nest as one group, and requires
``coverage.min_semantic_groups_per_required_cell`` (floored at 15 by the axis
itself) distinct groups in **every** required cell. See ``g13_semantic_group``.

Readiness
---------
``qualification_readiness.counted_qualification_ready`` is **computed**, not
asserted. It is true only when every freeze condition below passes *and* the
sealed reference bundle's content digest has been bound by whoever mints the
bundle. The manifest's declared value must equal the computed value, so the
declaration cannot drift into an unearned claim. It is a statement about the
freeze, never about a model.

Nothing here runs a model, touches the network, or counts towards qualification.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.evals.g13_independence import (
    CHECKER_ID,
    IndependenceRecord,
    check_independence,
    normalise_template,
)
from swarm.evals.g13_prompt_v2 import (
    PROMPT_ID,
    PromptV2Error,
    canonical_json,
    find_denylisted_keys,
    render_prompt,
    rendered_prompt_digest,
    sha256_hex,
    visible_input,
    visible_payload_digest,
)
from swarm.evals.g13_sealed_reference import (
    COMMITMENT_FILENAME,
    INTERFACE_ID,
    HiddenReferenceHandle,
    SealedReferenceIdentityError,
    commitment_violations,
    handle_for,
    load_commitment,
    render_commitment,
)
from swarm.evals.g13_semantic_group import (
    GROUP_AXIS_ID,
    MIN_SEMANTIC_GROUPS_PER_CELL,
    SemanticFingerprint,
    SemanticGroupError,
    assign_groups,
    corpus_scenario_vocabulary,
    groups_per_cell,
    semantic_fingerprint,
)
from swarm.evals.g13_size_classifier_v2 import (
    CLASSIFIER_ID,
    SizeClassifierV2Error,
    classify,
    derive_features,
)

FREEZE_ID = "g13-pool-freeze-v2"
FREEZE_VERSION = 2
FREEZE_DIR = Path("benchmarks") / "g13" / "pool_freeze_v2"
MANIFEST_NAME = "task_pool_freeze_v2.manifest.json"
SHARD_TABLE_NAME = "CORPUS_SHARD_DIGESTS.txt"
CHECKSUMS_NAME = "SHA256SUMS"
HOLDOUT_DIRNAME = "holdout"

HELD_OUT_SPLIT = "holdout"

#: Values that mark an unfinished ("floating") identity or manifest.
FLOATING_VALUES: frozenset[str] = frozenset(
    {"", "tbd", "todo", "unknown", "null", "none", "n/a", "fixme", "<fill>", "changeme", "?"}
)

#: Identity blocks the v2 manifest must pin. Every one of them is required; a
#: missing block is a violation, not a default.
REQUIRED_IDENTITIES: tuple[str, ...] = (
    "pool",
    "records",
    "split",
    "size_classifier",
    "scorer",
    "prompt",
    "tool_protocol",
    "model_config_schema",
    "independence_checker",
    "semantic_group",
    "sealed_reference_interface",
)

#: ``identities.<name>`` -> (key holding the id, expected value from code).
IDENTITY_CODE_BINDINGS: dict[str, tuple[str, str]] = {
    "size_classifier": ("classifier_id", CLASSIFIER_ID),
    "prompt": ("prompt_id", PROMPT_ID),
    "independence_checker": ("checker_id", CHECKER_ID),
    "semantic_group": ("group_axis_id", GROUP_AXIS_ID),
    "sealed_reference_interface": ("interface_id", INTERFACE_ID),
}

SHARD_TABLE_HEADER: tuple[str, ...] = (
    "# g13-pool-freeze-v2 corpus shard table (split identity)",
    "# format: <product_family> <family> <size> <split> <record_count> <sha256> <shard>",
    "# digest input: the exact bytes of the shard file under"
    " benchmarks/g13/pool_freeze_v2/holdout/",
    "# order: canonical corpus order (product_family, then S, M, L, XL)",
)


class PoolFreezeV2Error(ValueError):
    """Raised when the frozen v2 artefacts cannot be parsed at all."""


@dataclass(frozen=True)
class Violation:
    code: str
    detail: str

    def __str__(self) -> str:  # pragma: no cover - formatting helper
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

    def codes(self) -> list[str]:
        return [v.code for v in self.violations]

    def report(self) -> str:
        if self.ok:
            return f"{FREEZE_ID} OK"
        lines = "\n".join(f"  - {v}" for v in self.violations)
        return f"{FREEZE_ID} violations:\n{lines}"


# --------------------------------------------------------------------------
# primitives
# --------------------------------------------------------------------------


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def file_digest(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def record_digest(line: str) -> str:
    """Digest of one JSONL record line, including its terminating ``LF``."""
    return sha256_hex((line + "\n").encode("utf-8"))


def _as_dict(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PoolFreezeV2Error(f"{where}: expected object, got {type(value).__name__}")
    return {str(k): v for k, v in value.items()}


def _as_list(value: Any, where: str) -> list[Any]:
    if not isinstance(value, list):
        raise PoolFreezeV2Error(f"{where}: expected array, got {type(value).__name__}")
    return list(value)


def _as_str(value: Any, where: str) -> str:
    if not isinstance(value, str):
        raise PoolFreezeV2Error(f"{where}: expected string, got {type(value).__name__}")
    return value


def _as_int(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PoolFreezeV2Error(f"{where}: expected integer, got {type(value).__name__}")
    return value


def _as_bool(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise PoolFreezeV2Error(f"{where}: expected boolean, got {type(value).__name__}")
    return value


def _get(mapping: Mapping[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise PoolFreezeV2Error(f"{where}: missing required key {key!r}")
    return mapping[key]


def find_floating_values(value: Any, path: str = "$") -> list[str]:
    """JSON paths whose value is a placeholder or an empty container.

    ``identities`` blocks that legitimately declare "nothing here" use an
    explicit ``false``/``0`` rather than an empty list, so an empty container is
    always an unfinished slot.
    """
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


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------


def manifest_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / FREEZE_DIR / MANIFEST_NAME


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise PoolFreezeV2Error(f"manifest not found: {path}")
    return _as_dict(json.loads(path.read_bytes().decode("utf-8")), str(path))


def load_jsonl_lines(path: Path) -> list[str]:
    """Raw record lines (no terminating newline) in file order.

    Read as bytes on purpose: ``read_text`` applies universal-newline
    translation, which would hide a CRLF checkout from a byte-exact freeze.
    """
    if not path.exists():
        raise PoolFreezeV2Error(f"shard not found: {path}")
    text = path.read_bytes().decode("utf-8")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    else:
        raise PoolFreezeV2Error(f"{path}: shard must end with a single LF")
    if not lines:
        raise PoolFreezeV2Error(f"{path}: shard is empty")
    return lines


@dataclass(frozen=True)
class ShardRow:
    """One row of the shard table = one required cell."""

    product_family: str
    family: str
    size: str
    split: str
    record_count: int
    sha256: str
    shard: str

    def cell(self) -> str:
        return f"{self.product_family}/{self.size}"


def load_shard_table(path: Path) -> list[ShardRow]:
    if not path.exists():
        raise PoolFreezeV2Error(f"shard table not found: {path}")
    rows: list[ShardRow] = []
    for line_no, raw in enumerate(path.read_bytes().decode("utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 7:
            raise PoolFreezeV2Error(f"{path}:{line_no}: expected 7 fields, got {len(parts)}")
        digest = parts[5]
        if len(digest) != 64 or not all(c in "0123456789abcdef" for c in digest):
            raise PoolFreezeV2Error(f"{path}:{line_no}: not a sha256 hex digest: {digest!r}")
        if not parts[4].isdigit():
            raise PoolFreezeV2Error(f"{path}:{line_no}: record_count {parts[4]!r} is not an int")
        rows.append(
            ShardRow(
                product_family=parts[0],
                family=parts[1],
                size=parts[2],
                split=parts[3],
                record_count=int(parts[4]),
                sha256=digest,
                shard=parts[6],
            )
        )
    if not rows:
        raise PoolFreezeV2Error(f"{path}: shard table has no rows")
    return rows


@dataclass(frozen=True)
class LoadedRecord:
    """One corpus record plus everything derived from it."""

    row: ShardRow
    line_no: int
    case_id: str
    record: dict[str, Any]
    line: str


# --------------------------------------------------------------------------
# rendering (mint side)
# --------------------------------------------------------------------------


def render_shard_table(root: Path | None = None) -> str:
    """Render ``CORPUS_SHARD_DIGESTS.txt`` from the shards on disk.

    Record counts, digests and the ``(product_family, family, size, split)``
    tuple are all read back out of each shard, so the table cannot describe a
    shard it did not measure. Shards are emitted in canonical corpus order.
    """
    holdout_dir = (root or repo_root()) / FREEZE_DIR / HOLDOUT_DIRNAME
    measured: list[tuple[str, str, str, str, int, str, str]] = []
    for shard_path in sorted(holdout_dir.glob("*.jsonl")):
        lines = load_jsonl_lines(shard_path)
        first = _as_dict(json.loads(lines[0]), f"{shard_path.name}:1")
        measured.append(
            (
                _as_str(first.get("product_family"), "product_family"),
                _as_str(first.get("family"), "family"),
                _as_str(first.get("size"), "size"),
                _as_str(first.get("split"), "split"),
                len(lines),
                file_digest(shard_path),
                shard_path.name,
            )
        )
    order = {size: index for index, size in enumerate(("S", "M", "L", "XL"))}
    measured.sort(key=lambda row: (row[0], order.get(row[2], len(order))))
    rendered = list(SHARD_TABLE_HEADER)
    rendered.extend(" ".join(str(field_value) for field_value in row) for row in measured)
    return "\n".join(rendered) + "\n"


def iter_freeze_files(root: Path | None = None) -> list[Path]:
    """Every file under the freeze directory, recursively.

    Sorted by POSIX-relative path rather than by ``Path`` order: ``Path``
    comparison is case-insensitive on Windows and case-sensitive elsewhere,
    which would make the committed ``SHA256SUMS`` platform-dependent.
    """
    base = (root or repo_root()) / FREEZE_DIR
    return sorted(
        (p for p in base.rglob("*") if p.is_file()),
        key=lambda p: p.relative_to(base).as_posix(),
    )


def render_checksums(root: Path | None = None) -> str:
    """Render a ``sha256sum``-compatible cover file for the freeze directory."""
    repo = root or repo_root()
    freeze_dir = repo / FREEZE_DIR
    lines: list[str] = []
    for path in iter_freeze_files(repo):
        if path.name == CHECKSUMS_NAME:
            continue
        rel = path.relative_to(freeze_dir).as_posix()
        lines.append(f"{file_digest(path)} *{rel}\n")
    return "".join(lines)


# --------------------------------------------------------------------------
# corpus loading and per-record checks
# --------------------------------------------------------------------------


def _load_corpus(
    result: FreezeVerification, base: Path, rows: list[ShardRow]
) -> list[LoadedRecord]:
    loaded: list[LoadedRecord] = []
    holdout_dir = base / FREEZE_DIR / HOLDOUT_DIRNAME
    for row in rows:
        shard_path = holdout_dir / row.shard
        if not shard_path.exists():
            result.add("shard_missing", f"{row.shard} is in the shard table but not on disk")
            continue
        actual = file_digest(shard_path)
        if actual != row.sha256:
            result.add(
                "shard_digest_mismatch",
                f"{row.shard} expected {row.sha256} got {actual}"
                " (frozen corpus bytes changed — mint a new freeze version)",
            )
        lines = load_jsonl_lines(shard_path)
        if len(lines) != row.record_count:
            result.add(
                "shard_record_count_mismatch",
                f"{row.shard} holds {len(lines)} records, shard table declares"
                f" {row.record_count}",
            )
        for line_no, line in enumerate(lines, start=1):
            where = f"{row.shard}:{line_no}"
            record = _as_dict(json.loads(line), where)
            case_id = record.get("id")
            if not isinstance(case_id, str) or not case_id:
                result.add("record_id_missing", f"{where}: record has no usable id")
                continue
            loaded.append(
                LoadedRecord(
                    row=row, line_no=line_no, case_id=case_id, record=record, line=line
                )
            )

    on_disk = sorted(p.name for p in holdout_dir.glob("*.jsonl")) if holdout_dir.exists() else []
    declared = sorted(row.shard for row in rows)
    for orphan in sorted(set(on_disk) - set(declared)):
        result.add("shard_not_in_table", f"{orphan} is on disk but not in the shard table")
    return loaded


def _check_record_envelope(
    result: FreezeVerification, entry: LoadedRecord, expected_pool: str
) -> None:
    where = f"{entry.row.shard}:{entry.line_no}"
    record = entry.record
    for key, expected in (
        ("pool", expected_pool),
        ("split", entry.row.split),
        ("product_family", entry.row.product_family),
        ("family", entry.row.family),
        ("size", entry.row.size),
    ):
        actual = record.get(key)
        if actual != expected:
            result.add(
                "record_field_mismatch",
                f"{where}: {key} is {actual!r}, shard table implies {expected!r}",
            )
    generation = record.get("generation")
    if not isinstance(generation, Mapping):
        result.add("record_generation_missing", f"{where}: generation block is absent")
        return
    if generation.get("synthetic") is not True:
        result.add("record_not_marked_synthetic", f"{where}: generation.synthetic is not true")
    if generation.get("third_party_source") is not False:
        result.add(
            "record_third_party_source",
            f"{where}: generation.third_party_source must be explicitly false",
        )


def _check_leakage(result: FreezeVerification, entry: LoadedRecord) -> int:
    """Return 1 if this record leaks an answer/grader/reference key, else 0."""
    where = f"{entry.row.shard}:{entry.line_no}"
    leaked = find_denylisted_keys(entry.record)
    if leaked:
        result.add(
            "visible_answer_leak",
            f"{where}: answer/grader/reference key names present: {leaked}",
        )
        return 1
    return 0


# --------------------------------------------------------------------------
# identity pinning
# --------------------------------------------------------------------------


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
                f"{where}: {rel} expected {expected} got {actual}"
                " (frozen identity changed — mint a new freeze version)",
            )


def _check_identities(
    result: FreezeVerification, base: Path, manifest: Mapping[str, Any]
) -> None:
    identities = _as_dict(_get(manifest, "identities", "$"), "$.identities")
    for name in REQUIRED_IDENTITIES:
        if name not in identities:
            result.add("identity_missing", f"$.identities.{name} is not pinned")
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
        payload = json.loads(target.read_bytes().decode("utf-8"))
        for floating in find_floating_values(payload, f"{rel}$"):
            result.add("floating_identity_value", f"{floating} is empty/placeholder")
        for leaked in find_denylisted_keys(payload, f"{rel}$"):
            result.add(
                "answer_key_in_identity_spec",
                f"{leaked} names an answer/grader/reference field",
            )
        pinned = block.get("pinned_files")
        if pinned is not None:
            _check_pinned_files(
                result, base, _as_dict(pinned, f"{where}.pinned_files"), f"{where}.pinned_files"
            )
        binding = IDENTITY_CODE_BINDINGS.get(name)
        if binding is None:
            continue
        id_key, code_value = binding
        declared = block.get(id_key)
        if declared != code_value:
            result.add(
                "identity_id_code_mismatch",
                f"{where}.{id_key} is {declared!r}, the implementation says {code_value!r}",
            )


# --------------------------------------------------------------------------
# sealed reference
# --------------------------------------------------------------------------


def _check_sealed_reference(
    result: FreezeVerification,
    base: Path,
    manifest: Mapping[str, Any],
    records: list[LoadedRecord],
) -> tuple[list[HiddenReferenceHandle], bool]:
    """Verify the sealed-reference identity. Returns (handles, bundle_bound)."""
    block = _as_dict(_get(manifest, "sealed_reference", "$"), "$.sealed_reference")
    declared_interface = _as_str(
        _get(block, "interface_id", "$.sealed_reference"), "$.sealed_reference.interface_id"
    )
    if declared_interface != INTERFACE_ID:
        result.add(
            "sealed_reference_interface_mismatch",
            f"manifest {declared_interface!r} vs code {INTERFACE_ID!r}",
        )

    commitment = _as_dict(
        _get(block, "id_commitment", "$.sealed_reference"), "$.sealed_reference.id_commitment"
    )
    rel = _as_str(_get(commitment, "path", "$..id_commitment"), "$..id_commitment.path")
    expected_digest = _as_str(
        _get(commitment, "sha256", "$..id_commitment"), "$..id_commitment.sha256"
    )
    declared_entries = _as_int(
        _get(commitment, "entry_count", "$..id_commitment"), "$..id_commitment.entry_count"
    )
    path = base / rel
    if path.name != COMMITMENT_FILENAME:
        result.add(
            "sealed_reference_commitment_filename",
            f"{rel} is not the frozen commitment filename {COMMITMENT_FILENAME}",
        )

    handles: list[HiddenReferenceHandle] = []
    for entry in records:
        try:
            handles.append(handle_for(entry.record))
        except SealedReferenceIdentityError as exc:
            result.add("hidden_reference_identity_invalid", str(exc))

    if not path.exists():
        result.add("sealed_reference_commitment_missing", f"{rel} does not exist")
    else:
        actual = file_digest(path)
        if actual != expected_digest:
            result.add(
                "sealed_reference_commitment_digest_mismatch",
                f"{rel} expected {expected_digest} got {actual}",
            )
        rows = load_commitment(path)
        if len(rows) != declared_entries:
            result.add(
                "sealed_reference_entry_count_mismatch",
                f"{rel} holds {len(rows)} rows, manifest declares {declared_entries}",
            )
        if len(rows) != len(records):
            result.add(
                "sealed_reference_coverage_mismatch",
                f"{rel} holds {len(rows)} rows for {len(records)} corpus records",
            )
        for code, detail in commitment_violations(handles, rows):
            result.add(code, detail)

    bundle = _as_dict(
        _get(block, "reference_bundle", "$.sealed_reference"),
        "$.sealed_reference.reference_bundle",
    )
    location = _as_str(
        _get(bundle, "location", "$..reference_bundle"), "$..reference_bundle.location"
    )
    if location != "outside_the_worker_visible_branch":
        result.add(
            "sealed_reference_bundle_inside_branch",
            f"reference_bundle.location is {location!r}: held-out references must not be"
            " reachable from the worker-visible branch",
        )
    binding = _as_dict(
        _get(bundle, "content_digest_binding", "$..reference_bundle"),
        "$..reference_bundle.content_digest_binding",
    )
    bundle_bound = _as_bool(
        _get(binding, "declared_here", "$..content_digest_binding"),
        "$..content_digest_binding.declared_here",
    )
    if bundle_bound and "sha256" not in binding:
        result.add(
            "sealed_reference_bundle_digest_absent",
            "content_digest_binding.declared_here is true but no sha256 is declared",
        )

    # Nothing that could be a local reference bundle may live in the freeze dir.
    for path_on_disk in iter_freeze_files(base):
        name = path_on_disk.name.lower()
        if "reference" in name and name != COMMITMENT_FILENAME.lower():
            if not name.startswith("identity_sealed_reference"):
                result.add(
                    "sealed_reference_local_artefact",
                    f"{path_on_disk.name} looks like a local reference store inside the"
                    " worker-visible freeze directory",
                )
    return handles, bundle_bound


# --------------------------------------------------------------------------
# foreign corpora (for cross-corpus independence)
# --------------------------------------------------------------------------


def _foreign_records(
    result: FreezeVerification, base: Path, manifest: Mapping[str, Any]
) -> list[IndependenceRecord]:
    declared = _as_list(_get(manifest, "foreign_corpora", "$"), "$.foreign_corpora")
    out: list[IndependenceRecord] = []
    for position, raw in enumerate(declared):
        where = f"$.foreign_corpora[{position}]"
        block = _as_dict(raw, where)
        corpus_id = _as_str(_get(block, "corpus_id", where), f"{where}.corpus_id")
        rel = _as_str(_get(block, "path", where), f"{where}.path")
        expected = _as_str(_get(block, "sha256", where), f"{where}.sha256")
        prompt_field = _as_str(
            _get(block, "prompt_field", where), f"{where}.prompt_field"
        )
        path = base / rel
        if not path.exists():
            result.add("foreign_corpus_missing", f"{where}: {rel} does not exist")
            continue
        actual = file_digest(path)
        if actual != expected:
            result.add(
                "foreign_corpus_digest_mismatch",
                f"{where}: {rel} expected {expected} got {actual}",
            )
        for line_no, line in enumerate(load_jsonl_lines(path), start=1):
            record = _as_dict(json.loads(line), f"{rel}:{line_no}")
            payload = record.get("input")
            if not isinstance(payload, Mapping):
                result.add(
                    "foreign_record_no_input", f"{rel}:{line_no}: record has no input object"
                )
                continue
            visible = {str(k): v for k, v in payload.items()}
            text = visible.get(prompt_field)
            prompt_text = text if isinstance(text, str) else canonical_json(visible)
            out.append(
                IndependenceRecord(
                    corpus_id=corpus_id,
                    split=str(record.get("split", "unknown")),
                    case_id=str(record.get("id", f"{rel}:{line_no}")),
                    payload_digest=visible_payload_digest(visible),
                    prompt_digest=sha256_hex(prompt_text.encode("utf-8")),
                    template_digest=sha256_hex(
                        normalise_template(prompt_text).encode("utf-8")
                    ),
                )
            )
    return out


# --------------------------------------------------------------------------
# main verification
# --------------------------------------------------------------------------


def _required_cells(manifest: Mapping[str, Any]) -> list[tuple[str, str]]:
    coverage = _as_dict(_get(manifest, "coverage", "$"), "$.coverage")
    families = _as_list(
        _get(coverage, "required_product_families", "$.coverage"),
        "$.coverage.required_product_families",
    )
    sizes = _as_list(
        _get(coverage, "required_sizes", "$.coverage"), "$.coverage.required_sizes"
    )
    return [
        (_as_str(f, "required_product_families[]"), _as_str(s, "required_sizes[]"))
        for f in families
        for s in sizes
    ]


def verify_pool_freeze_v2(
    root: Path | None = None, *, manifest_file: Path | None = None
) -> FreezeVerification:
    """Deterministically verify ``g13-pool-freeze-v2``. No model calls, no network."""
    base = root or repo_root()
    result = FreezeVerification()
    manifest = load_manifest(manifest_file or manifest_path(base))

    freeze_id = _as_str(_get(manifest, "freeze_id", "$"), "$.freeze_id")
    if freeze_id != FREEZE_ID:
        result.add("freeze_id_mismatch", f"expected {FREEZE_ID!r}, manifest says {freeze_id!r}")
    freeze_version = _as_int(_get(manifest, "freeze_version", "$"), "$.freeze_version")
    if freeze_version != FREEZE_VERSION:
        result.add(
            "freeze_version_mismatch",
            f"expected {FREEZE_VERSION}, manifest says {freeze_version}",
        )

    for floating in find_floating_values(manifest):
        result.add("floating_manifest_value", f"{floating} is empty/placeholder")
    for leaked in find_denylisted_keys(manifest):
        result.add(
            "answer_key_in_manifest", f"{leaked} names an answer/grader/reference field"
        )

    # --- corpus + split identity ----------------------------------------
    corpus = _as_dict(_get(manifest, "corpus", "$"), "$.corpus")
    table_block = _as_dict(_get(corpus, "shard_table", "$.corpus"), "$.corpus.shard_table")
    table_rel = _as_str(
        _get(table_block, "path", "$.corpus.shard_table"), "$.corpus.shard_table.path"
    )
    table_expected = _as_str(
        _get(table_block, "sha256", "$.corpus.shard_table"), "$.corpus.shard_table.sha256"
    )
    table_path = base / table_rel
    if not table_path.exists():
        result.add("shard_table_missing", f"{table_rel} does not exist")
        return result
    table_actual = file_digest(table_path)
    if table_actual != table_expected:
        result.add(
            "shard_table_digest_mismatch",
            f"{table_rel} expected {table_expected} got {table_actual}",
        )
    rows = load_shard_table(table_path)

    declared_shards = _as_int(
        _get(corpus, "shard_count", "$.corpus"), "$.corpus.shard_count"
    )
    if len(rows) != declared_shards:
        result.add(
            "shard_count_mismatch",
            f"shard table has {len(rows)} rows, manifest declares {declared_shards}",
        )
    for row in rows:
        if row.split != HELD_OUT_SPLIT:
            result.add(
                "shard_split_not_holdout",
                f"{row.shard}: split {row.split!r}; the v2 corpus is held-out only",
            )

    records = _load_corpus(result, base, rows)
    declared_records = _as_int(
        _get(corpus, "record_count", "$.corpus"), "$.corpus.record_count"
    )
    if len(records) != declared_records:
        result.add(
            "corpus_record_count_mismatch",
            f"corpus holds {len(records)} records, manifest declares {declared_records}",
        )

    # --- per-record envelope, leakage, size band ------------------------
    expected_pool = freeze_id
    answer_leak_count = 0
    for entry in records:
        _check_record_envelope(result, entry, expected_pool)
        answer_leak_count += _check_leakage(result, entry)
        where = f"{entry.row.shard}:{entry.line_no}"
        try:
            visible = visible_input(entry.record)
        except PromptV2Error as exc:
            result.add("visible_payload_refused", f"{where}: {exc}")
            continue
        if visible.get("task") != entry.row.family:
            result.add(
                "record_task_family_mismatch",
                f"{where}: input.task is {visible.get('task')!r},"
                f" shard family is {entry.row.family!r}",
            )
        try:
            features = derive_features(visible)
            derived = classify(visible)
        except SizeClassifierV2Error as exc:
            result.add("size_classifier_error", f"{where}: {exc}")
            continue
        if derived != entry.row.size:
            result.add(
                "size_classifier_disagreement",
                f"{entry.case_id}: shard declares {entry.row.size} but {CLASSIFIER_ID}"
                f" derives {derived} from structural_load"
                f" {features.structural_load()} {features.as_dict()}",
            )
        item_ids = {
            str(item.get("id"))
            for item in visible.get("items", [])
            if isinstance(item, Mapping) and "id" in item
        }
        for edge in visible.get("dependencies", []) or []:
            for endpoint in edge:
                if item_ids and str(endpoint) not in item_ids:
                    result.add(
                        "dependency_endpoint_unknown",
                        f"{entry.case_id}: dependency endpoint {endpoint!r} is not a"
                        " declared item id",
                    )

    # --- identities ------------------------------------------------------
    _check_identities(result, base, manifest)

    # --- sealed reference ------------------------------------------------
    _handles, bundle_bound = _check_sealed_reference(result, base, manifest, records)

    # --- coverage --------------------------------------------------------
    coverage = _as_dict(_get(manifest, "coverage", "$"), "$.coverage")
    min_per_cell = _as_int(
        _get(coverage, "min_independent_per_required_cell", "$.coverage"),
        "$.coverage.min_independent_per_required_cell",
    )
    declared_min_total = _as_int(
        _get(coverage, "min_total_independent_held_out", "$.coverage"),
        "$.coverage.min_total_independent_held_out",
    )
    cell_counts: Counter[str] = Counter(entry.row.cell() for entry in records)
    required = _required_cells(manifest)
    if len(required) * min_per_cell != declared_min_total:
        result.add(
            "coverage_arithmetic_mismatch",
            f"{len(required)} required cells x {min_per_cell} != declared minimum"
            f" {declared_min_total}",
        )
    for product_family, size in required:
        cell = f"{product_family}/{size}"
        count = cell_counts.get(cell, 0)
        if count < min_per_cell:
            result.add(
                "required_cell_below_minimum",
                f"{cell} holds {count} independent held-out inputs, the protocol"
                f" minimum is {min_per_cell}",
            )
    for cell in sorted(set(cell_counts) - {f"{f}/{s}" for f, s in required}):
        result.add("unexpected_cell", f"{cell} is not a required cell")
    if len(records) < declared_min_total:
        result.add(
            "corpus_below_minimum_total",
            f"corpus holds {len(records)} held-out inputs, the minimum is"
            f" {declared_min_total}",
        )

    # --- semantic archetype / independence-group axis --------------------
    # Record *depth* is not archetype *depth*: fifteen re-skins of one recipe
    # are one observation repeated. This axis is additive — every digest and
    # normalised-template invariant above still runs, unchanged.
    declared_min_groups = _as_int(
        _get(coverage, "min_semantic_groups_per_required_cell", "$.coverage"),
        "$.coverage.min_semantic_groups_per_required_cell",
    )
    if declared_min_groups < MIN_SEMANTIC_GROUPS_PER_CELL:
        result.add(
            "semantic_group_minimum_below_protocol",
            f"manifest declares min_semantic_groups_per_required_cell={declared_min_groups},"
            f" {GROUP_AXIS_ID} floors it at {MIN_SEMANTIC_GROUPS_PER_CELL}",
        )
    effective_min_groups = max(declared_min_groups, MIN_SEMANTIC_GROUPS_PER_CELL)
    vocabulary = corpus_scenario_vocabulary(entry.record for entry in records)
    fingerprints: list[SemanticFingerprint] = []
    for entry in records:
        try:
            fingerprints.append(
                semantic_fingerprint(
                    entry.record, cell=entry.row.cell(), vocabulary=vocabulary
                )
            )
        except SemanticGroupError as exc:
            result.add(
                "semantic_group_unreducible",
                f"{entry.row.shard}:{entry.line_no}: {exc}",
            )
    cell_groups: dict[str, int] = {}
    distinct_groups = 0
    try:
        cell_groups = groups_per_cell(fingerprints)
        distinct_groups = len(set(assign_groups(fingerprints).values()))
    except SemanticGroupError as exc:
        result.add("semantic_group_axis_failed", str(exc))
    for product_family, size in required:
        cell = f"{product_family}/{size}"
        groups = cell_groups.get(cell, 0)
        if groups < effective_min_groups:
            result.add(
                "required_cell_below_minimum_semantic_groups",
                f"{cell} holds {cell_counts.get(cell, 0)} records but only {groups} distinct"
                f" semantic groups under {GROUP_AXIS_ID}; the protocol minimum is"
                f" {effective_min_groups}. Scenario renames, numeric substitutions and"
                " cumulative clause growth do not make a new group",
            )

    # --- independence ----------------------------------------------------
    own = [
        IndependenceRecord(
            corpus_id=freeze_id,
            split=entry.row.split,
            case_id=entry.case_id,
            payload_digest=_safe_payload_digest(entry),
            prompt_digest=_safe_prompt_digest(entry),
            template_digest=_safe_template_digest(entry),
        )
        for entry in records
    ]
    foreign = _foreign_records(result, base, manifest)
    independence = check_independence(
        [*own, *foreign], held_out_corpus_id=freeze_id, held_out_split=HELD_OUT_SPLIT
    )
    for violation in independence.violations:
        result.add(violation.code, violation.detail)

    # --- readiness (computed, then compared to the declaration) ----------
    readiness = _as_dict(
        _get(manifest, "qualification_readiness", "$"), "$.qualification_readiness"
    )
    declared_ready = _as_bool(
        _get(readiness, "counted_qualification_ready", "$.qualification_readiness"),
        "$.qualification_readiness.counted_qualification_ready",
    )
    freeze_conditions_pass = result.ok
    computed_ready = freeze_conditions_pass and bundle_bound
    if declared_ready != computed_ready:
        result.add(
            "readiness_declaration_mismatch",
            f"manifest declares counted_qualification_ready={declared_ready},"
            f" the verifier computes {computed_ready}"
            f" (freeze_conditions_pass={freeze_conditions_pass},"
            f" sealed_bundle_content_digest_bound={bundle_bound})",
        )

    record_digests = {entry.case_id: record_digest(entry.line) for entry in records}
    result.stats = {
        "freeze_id": freeze_id,
        "freeze_version": freeze_version,
        "shard_table_sha256": table_actual,
        "shard_count": len(rows),
        "held_out_record_count": len(records),
        "distinct_record_digests": len(set(record_digests.values())),
        "independent_per_required_cell": {cell: cell_counts[cell] for cell in sorted(cell_counts)},
        "semantic_group_axis_id": GROUP_AXIS_ID,
        "min_semantic_groups_per_required_cell": effective_min_groups,
        "semantic_groups_per_required_cell": cell_groups,
        "distinct_semantic_groups": distinct_groups,
        "semantic_fingerprints": len(fingerprints),
        "answer_leak_count": answer_leak_count,
        "sealed_reference_handles": len(_handles),
        "sealed_bundle_content_digest_bound": bundle_bound,
        "freeze_conditions_pass": freeze_conditions_pass,
        "counted_qualification_ready_computed": computed_ready,
        "independence": independence.stats,
    }
    return result


def _safe_visible(entry: LoadedRecord) -> dict[str, Any]:
    try:
        return visible_input(entry.record)
    except PromptV2Error:
        return {"task": "unrenderable", "instruction": entry.case_id}


def _safe_payload_digest(entry: LoadedRecord) -> str:
    return visible_payload_digest(_safe_visible(entry))


def _safe_prompt_digest(entry: LoadedRecord) -> str:
    return rendered_prompt_digest(_safe_visible(entry))


def _safe_template_digest(entry: LoadedRecord) -> str:
    return sha256_hex(normalise_template(render_prompt(_safe_visible(entry))).encode("utf-8"))


def verify_checksums_v2(root: Path | None = None) -> FreezeVerification:
    """Verify ``SHA256SUMS`` covers every file in the freeze directory."""
    base = root or repo_root()
    result = FreezeVerification()
    freeze_dir = base / FREEZE_DIR
    sums_path = freeze_dir / CHECKSUMS_NAME
    if not sums_path.exists():
        result.add("checksums_missing", f"{sums_path} does not exist")
        return result
    listed: dict[str, str] = {}
    for line_no, raw in enumerate(sums_path.read_bytes().decode("utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise PoolFreezeV2Error(f"{sums_path}:{line_no}: malformed line {raw!r}")
        listed[parts[1].lstrip("*").strip()] = parts[0]
    for name in sorted(listed):
        target = freeze_dir / name
        if not target.exists():
            result.add("checksum_target_missing", name)
            continue
        actual = file_digest(target)
        if actual != listed[name]:
            result.add("checksum_mismatch", f"{name}: expected {listed[name]} got {actual}")
    on_disk = {
        p.relative_to(freeze_dir).as_posix()
        for p in iter_freeze_files(base)
        if p.name != CHECKSUMS_NAME
    }
    for uncovered in sorted(on_disk - set(listed)):
        result.add("checksum_uncovered_file", uncovered)
    result.stats = {"covered_files": len(listed)}
    return result


def canonical_corpus_records(root: Path | None = None) -> list[LoadedRecord]:
    """Every corpus record in canonical order, read straight off the shards.

    Used by the mint path, which must not depend on the shard table it is about
    to rewrite.
    """
    base = root or repo_root()
    holdout_dir = base / FREEZE_DIR / HOLDOUT_DIRNAME
    size_order = {size: index for index, size in enumerate(("S", "M", "L", "XL"))}
    shards: list[tuple[str, int, Path]] = []
    for shard_path in sorted(holdout_dir.glob("*.jsonl")):
        first = _as_dict(json.loads(load_jsonl_lines(shard_path)[0]), f"{shard_path.name}:1")
        shards.append(
            (
                _as_str(first.get("product_family"), "product_family"),
                size_order.get(_as_str(first.get("size"), "size"), len(size_order)),
                shard_path,
            )
        )
    shards.sort(key=lambda entry: (entry[0], entry[1]))

    out: list[LoadedRecord] = []
    for _product_family, _size_index, shard_path in shards:
        lines = load_jsonl_lines(shard_path)
        first = _as_dict(json.loads(lines[0]), f"{shard_path.name}:1")
        row = ShardRow(
            product_family=_as_str(first.get("product_family"), "product_family"),
            family=_as_str(first.get("family"), "family"),
            size=_as_str(first.get("size"), "size"),
            split=_as_str(first.get("split"), "split"),
            record_count=len(lines),
            sha256=file_digest(shard_path),
            shard=shard_path.name,
        )
        for line_no, line in enumerate(lines, start=1):
            record = _as_dict(json.loads(line), f"{shard_path.name}:{line_no}")
            out.append(
                LoadedRecord(
                    row=row,
                    line_no=line_no,
                    case_id=_as_str(record.get("id"), f"{shard_path.name}:{line_no}.id"),
                    record=record,
                    line=line,
                )
            )
    return out


def render_commitment_file(records: Iterable[LoadedRecord]) -> str:
    """Render ``SEALED_REFERENCE_IDS.txt`` from the corpus, for the mint path."""
    return render_commitment([handle_for(entry.record) for entry in records])
