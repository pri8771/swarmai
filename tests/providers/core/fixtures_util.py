"""Recorded fixture helpers for core provider tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def openai_success(model: str = "fixture-model", *, with_usage: bool = True) -> dict[str, Any]:
    usage = (
        {"prompt_tokens": 11, "completion_tokens": 5, "total_tokens": 16}
        if with_usage
        else None
    )
    body: dict[str, Any] = {
        "id": "chatcmpl_test",
        "model": model,
        "choices": [{"message": {"role": "assistant", "content": "ok"}}],
    }
    if usage is not None:
        body["usage"] = usage
    return body


def write_scenario_fixture(path: Path, exchanges: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(exchanges, indent=2) + "\n")


def exchange(
    *,
    status: int,
    response: dict[str, Any] | None = None,
    text: str | None = None,
    method: str = "POST",
    url: str = "https://example.test/v1/chat/completions",
) -> dict[str, Any]:
    return {
        "method": method,
        "url": url,
        "status_code": status,
        "request_json": None,
        "response_json": response,
        "response_text": text,
        "headers": {},
    }
