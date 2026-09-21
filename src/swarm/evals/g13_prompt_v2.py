"""Frozen G13 prompt identity, version 2 — the worker/model-visible surface.

This module is the single authority for three questions about
``g13-pool-freeze-v2``:

1. **What is model-visible?** Exactly ``record["input"]`` and nothing else.
   :func:`visible_input` returns it, and refuses to return it at all if the
   record carries a key outside :data:`RECORD_KEY_ALLOWLIST` or names anything
   on :data:`ANSWER_KEY_DENYLIST` at any depth. A v2 record is *input-only*: it
   has no place to put an answer, a grader, a rubric or a reference.
2. **How is a record turned into a prompt?** :func:`render_prompt` renders the
   structured payload into one deterministic user message. There is no system
   prompt, no exemplar, no chain-of-thought scaffold and no tool description —
   see ``g13-tool-protocol-v2``.
3. **How are model-visible bytes digested?** :func:`canonical_json` /
   :func:`sha256_hex` define it, so the independence checker and the freeze
   verifier cannot disagree about what "the same input" means.

Changing ``PROMPT_ID``, the allowlist, the denylist or the rendering is a
breaking change: mint a new prompt id and a new pool freeze version.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any, Final

PROMPT_ID: Final[str] = "g13-prompt-v2"

#: The only keys a v2 corpus record may carry. Anything else fails the freeze.
RECORD_KEY_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "pool",
        "id",
        "split",
        "product_family",
        "family",
        "size",
        "variant",
        "scenario",
        "input",
        "hidden_reference",
        "generation",
        "output_limit_tokens_proposed",
    }
)

#: Keys whose presence anywhere in a record means an answer/grader/reference has
#: leaked into the worker-visible branch. Matched on key names, at any depth.
ANSWER_KEY_DENYLIST: Final[frozenset[str]] = frozenset(
    {
        "answer",
        "answers",
        "broken_code",
        "expected",
        "expected_output",
        "gold",
        "gold_answer",
        "grader",
        "grading",
        "hidden_answer",
        "hidden_output",
        "label",
        "holdout_label",
        "reference",
        "reference_output",
        "reference_solution",
        "rubric",
        "solution",
        "target",
        "test_cases",
        "unit_tests",
    }
)

#: Keys of ``record["input"]`` that ``render_prompt`` knows how to render. An
#: unknown input key fails the freeze rather than being silently dropped from
#: the prompt (which would make the rendered prompt and the payload disagree).
INPUT_KEY_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "task",
        "instruction",
        "question",
        "signature",
        "items",
        "dependencies",
        "constraints",
        "distractors",
        "output_contract",
    }
)


class PromptV2Error(ValueError):
    """Raised when a record cannot be reduced to a legal visible payload."""


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> str:
    """Stable JSON encoding used for every model-visible digest in v2."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def find_denylisted_keys(value: Any, path: str = "$") -> list[str]:
    """JSON paths where an answer/grader/reference key name is used as a key."""
    found: list[str] = []
    if isinstance(value, Mapping):
        for key in sorted(str(k) for k in value):
            child = f"{path}.{key}"
            if key.lower() in ANSWER_KEY_DENYLIST:
                found.append(child)
            found.extend(find_denylisted_keys(value[key], child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(find_denylisted_keys(item, f"{path}[{index}]"))
    return found


def record_key_violations(record: Mapping[str, Any]) -> list[str]:
    """Record-level keys outside the allowlist, sorted."""
    return sorted(str(key) for key in record if str(key) not in RECORD_KEY_ALLOWLIST)


def visible_input(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return the model-visible payload, or refuse if the record is not clean.

    Refusal is deliberate. A "defensive copy that strips leakage keys" — the v1
    behaviour — lets a contaminated record through in sanitised form, so the
    contamination survives in the committed corpus. Here a contaminated record
    cannot produce a payload at all, and the freeze fails.
    """
    extra = record_key_violations(record)
    if extra:
        raise PromptV2Error(f"record keys outside the v2 allowlist: {extra}")
    leaked = find_denylisted_keys(record)
    if leaked:
        raise PromptV2Error(f"answer/grader/reference key names present: {leaked}")
    payload = record.get("input")
    if not isinstance(payload, Mapping):
        raise PromptV2Error("record.input: expected an object")
    unknown = sorted(str(k) for k in payload if str(k) not in INPUT_KEY_ALLOWLIST)
    if unknown:
        raise PromptV2Error(f"input keys this prompt identity cannot render: {unknown}")
    return {str(k): v for k, v in payload.items()}


def visible_payload_digest(visible: Mapping[str, Any]) -> str:
    """Digest of the exact model-visible payload object."""
    return sha256_hex(canonical_json({"input": dict(visible)}).encode("utf-8"))


def _bullet_lines(header: str, values: list[Any]) -> list[str]:
    rendered = [header]
    for value in values:
        text = value if isinstance(value, str) else canonical_json(value)
        rendered.append(f"- {text}")
    return rendered


def render_prompt(visible: Mapping[str, Any]) -> str:
    """Render one deterministic user message from a visible payload.

    Section order is fixed by this function, not by the record's key order, so
    two records with equal payloads always render byte-identically.
    """
    for required in ("task", "instruction"):
        if not isinstance(visible.get(required), str) or not visible[required]:
            raise PromptV2Error(f"input.{required}: expected a non-empty string")
    lines: list[str] = [f"TASK: {visible['task']}", f"INSTRUCTION: {visible['instruction']}"]
    question = visible.get("question")
    if question is not None:
        lines.append(f"QUESTION: {question}")
    signature = visible.get("signature")
    if signature is not None:
        lines.append(f"SIGNATURE: {signature}")

    items = visible.get("items")
    lines.extend(_bullet_lines("ITEMS:", list(items) if isinstance(items, list) else []))

    dependencies = visible.get("dependencies")
    if isinstance(dependencies, list) and dependencies:
        lines.append("DEPENDENCIES (before -> after):")
        for edge in dependencies:
            lines.append(f"- {edge[0]} -> {edge[1]}")

    constraints = visible.get("constraints")
    lines.extend(
        _bullet_lines("CONSTRAINTS:", list(constraints) if isinstance(constraints, list) else [])
    )

    distractors = visible.get("distractors")
    if isinstance(distractors, list) and distractors:
        lines.extend(_bullet_lines("DISTRACTORS (not authoritative, ignore):", list(distractors)))

    contract = visible.get("output_contract")
    if isinstance(contract, Mapping):
        fields = contract.get("fields")
        field_list = ",".join(str(f) for f in fields) if isinstance(fields, list) else ""
        lines.append("OUTPUT CONTRACT:")
        lines.append(f"- format={contract.get('format')}")
        lines.append(f"- fields={field_list}")
        lines.append(f"- sort_by={contract.get('sort_by')}")
    return "\n".join(lines) + "\n"


def rendered_prompt_digest(visible: Mapping[str, Any]) -> str:
    """Digest of the exact bytes the model would receive."""
    return sha256_hex(render_prompt(visible).encode("utf-8"))


def prompt_identity() -> dict[str, Any]:
    """Serialisable identity of the frozen v2 prompt surface."""
    return {
        "prompt_id": PROMPT_ID,
        # Expressed as an explicit false rather than null: a null in a frozen
        # identity spec is indistinguishable from an unfilled slot, and the
        # freeze verifier rejects unfilled slots.
        "system_prompt_present": False,
        "exemplars": 0,
        "model_visible_record_keys": ["input"],
        "record_key_allowlist": sorted(RECORD_KEY_ALLOWLIST),
        "input_key_allowlist": sorted(INPUT_KEY_ALLOWLIST),
        "answer_key_denylist": sorted(ANSWER_KEY_DENYLIST),
        "leakage_policy": "refuse_not_sanitise",
        "section_order": [
            "TASK",
            "INSTRUCTION",
            "QUESTION",
            "SIGNATURE",
            "ITEMS",
            "DEPENDENCIES",
            "CONSTRAINTS",
            "DISTRACTORS",
            "OUTPUT CONTRACT",
        ],
        "digest_algorithm": "sha256",
        "payload_digest_input": (
            "json.dumps({'input': visible}, sort_keys=True, separators=(',',':'),"
            " ensure_ascii=True) encoded utf-8"
        ),
        "prompt_digest_input": "render_prompt(visible) encoded utf-8",
        "trailing_newline": True,
    }
