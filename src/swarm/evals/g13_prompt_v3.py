"""Frozen G13 prompt identity, version 3 — worker/model-visible surface."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any, Final

PROMPT_ID: Final[str] = "g13-prompt-v3"

RECORD_KEY_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "pool",
        "id",
        "split",
        "product_family",
        "family",
        "size",
        "semantic_archetype_id",
        "input",
        "hidden_reference",
        "generation",
        "output_limit_tokens_proposed",
    }
)

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


class PromptV3Error(ValueError):
    """Raised when a record cannot be reduced to a legal visible payload."""


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def find_denylisted_keys(value: Any, path: str = "$") -> list[str]:
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
    return sorted(str(key) for key in record if str(key) not in RECORD_KEY_ALLOWLIST)


def visible_input(record: Mapping[str, Any]) -> dict[str, Any]:
    extra = record_key_violations(record)
    if extra:
        raise PromptV3Error(f"record keys outside the v3 allowlist: {extra}")
    leaked = find_denylisted_keys(record)
    if leaked:
        raise PromptV3Error(f"answer/grader/reference key names present: {leaked}")
    payload = record.get("input")
    if not isinstance(payload, Mapping):
        raise PromptV3Error("record.input: expected an object")
    unknown = sorted(str(k) for k in payload if str(k) not in INPUT_KEY_ALLOWLIST)
    if unknown:
        raise PromptV3Error(f"input keys this prompt identity cannot render: {unknown}")
    return {str(k): v for k, v in payload.items()}


def visible_payload_digest(visible: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_json({"input": dict(visible)}).encode("utf-8"))


def _bullet_lines(header: str, values: list[Any]) -> list[str]:
    rendered = [header]
    for value in values:
        text = value if isinstance(value, str) else canonical_json(value)
        rendered.append(f"- {text}")
    return rendered


def render_prompt(visible: Mapping[str, Any]) -> str:
    for required in ("task", "instruction"):
        if not isinstance(visible.get(required), str) or not visible[required]:
            raise PromptV3Error(f"input.{required}: expected a non-empty string")
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
    return sha256_hex(render_prompt(visible).encode("utf-8"))


def prompt_identity() -> dict[str, Any]:
    return {
        "prompt_id": PROMPT_ID,
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
