"""Tests for V0.2 provider capability registry."""

from __future__ import annotations

from pathlib import Path

from swarm.providers.capability_registry import (
    build_capability_registry,
    routable_providers,
    save_capability_registry,
)


def test_capability_registry_offline_no_probe(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SWARM_ALLOW_PAID", "false")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
    report = build_capability_registry(probe=False, repo=Path.cwd())
    assert report["schema_version"] == "0.2.0"
    assert report["swarm_allow_paid"] is False
    assert report["provider_count"] >= 10
    ids = {p["provider_id"] for p in report["providers"]}
    assert "ollama" in ids
    assert "openai" in ids
    openai = next(p for p in report["providers"] if p["provider_id"] == "openai")
    assert openai["cost_policy"] == "deferred"
    together = next(p for p in report["providers"] if p["provider_id"] == "together")
    assert together["cost_policy"] == "paid_blocked"
    path = save_capability_registry(report, repo=tmp_path)
    assert path.exists()
    assert path.name == "capability-registry.json"


def test_routable_providers_prefers_zero_spend(monkeypatch) -> None:
    monkeypatch.setenv("SWARM_ALLOW_PAID", "false")
    report = {
        "providers": [
            {
                "provider_id": "ollama",
                "qualification_status": "auth_ok",
                "cost_policy": "zero_spend_ok",
                "health": "healthy",
            },
            {
                "provider_id": "together",
                "qualification_status": "auth_ok_inference_blocked",
                "cost_policy": "paid_blocked",
                "health": "healthy",
            },
        ]
    }
    rows = routable_providers(report)
    assert any(r["provider_id"] == "ollama" for r in rows)
    assert not any(r["provider_id"] == "together" for r in rows)
