"""Local zero-spend inference helper for mission workers (Ollama loopback)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from swarm.envfile import load_repo_dotenv
from swarm.providers.catalog import DEFAULT_ENDPOINTS


@dataclass
class InferenceResult:
    ok: bool
    text: str
    model: str
    route_id: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "text": self.text[:4000],
            "model": self.model,
            "route_id": self.route_id,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": self.cost_usd,
            "error": self.error,
        }


def _is_loopback(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1"}


def local_chat(
    *,
    messages: list[dict[str, str]],
    model: str = "gemma3:4b",
    max_tokens: int = 800,
    repo_root: Any = None,
) -> InferenceResult:
    """Call loopback Ollama only — never paid cloud endpoints."""
    from pathlib import Path

    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[3]
    load_repo_dotenv(root)
    base = (os.environ.get("OLLAMA_BASE_URL") or DEFAULT_ENDPOINTS["ollama"]).rstrip("/")
    if not _is_loopback(base):
        return InferenceResult(
            ok=False,
            text="",
            model=model,
            route_id=f"rt_ollama_{model}",
            cost_usd=0.0,
            error="non_loopback_endpoint_denied_under_zero_spend",
        )
    url = f"{base}/chat/completions"
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "max_tokens": max_tokens,
    }
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=body)
        if response.status_code >= 400:
            return InferenceResult(
                ok=False,
                text="",
                model=model,
                route_id=f"rt_ollama_{model}",
                error=f"http_{response.status_code}",
            )
        data = response.json()
        choice = (data.get("choices") or [{}])[0]
        text = ((choice.get("message") or {}).get("content")) or ""
        usage = data.get("usage") or {}
        return InferenceResult(
            ok=bool(text.strip()),
            text=text,
            model=str(data.get("model") or model),
            route_id=f"rt_ollama_{model}",
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            cost_usd=0.0,
        )
    except Exception as exc:  # noqa: BLE001 — surface as soft failure to mission
        return InferenceResult(
            ok=False,
            text="",
            model=model,
            route_id=f"rt_ollama_{model}",
            error=type(exc).__name__,
        )
