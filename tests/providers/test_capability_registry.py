"""Tests for V0.2 provider capability registry (fail-closed readiness)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

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
    # Fail closed: unprobed providers are not available and not free-eligible.
    ollama = next(p for p in report["providers"] if p["provider_id"] == "ollama")
    assert ollama["health"] == "unprobed"
    assert ollama["available"] is False
    assert ollama["cost_policy"] == "price_unverified"
    assert ollama["coding_suitability"] == "unknown"
    assert ollama["qualification_status"] == "unqualified"
    assert report["available_for_routing"] == 0
    path = save_capability_registry(report, repo=tmp_path)
    assert path.exists()
    assert path.name == "capability-registry.json"


def test_paid_false_alone_never_zero_spend_ok(monkeypatch) -> None:
    monkeypatch.setenv("SWARM_ALLOW_PAID", "false")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_fake_for_registry_test")
    with patch(
        "swarm.providers.capability_registry._probe",
        return_value=("healthy", 12.0, 3, "auth probe ok"),
    ):
        report = build_capability_registry(probe=True, repo=Path.cwd())
    groq = next(p for p in report["providers"] if p["provider_id"] == "groq")
    assert groq["health"] == "healthy"
    assert groq["qualification_status"] == "auth_ok"
    assert groq["cost_policy"] == "price_unverified"
    assert groq["coding_suitability"] == "unknown"
    assert groq["available"] is False  # not free-eligible without price proof


def test_cloudflare_unprobed_not_promoted(monkeypatch) -> None:
    monkeypatch.setenv("SWARM_ALLOW_PAID", "false")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "cf_fake")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "acct_fake")
    report = build_capability_registry(probe=False, repo=Path.cwd())
    cf = next(
        (p for p in report["providers"] if p["provider_id"] == "cloudflare_workers_ai"),
        None,
    )
    if cf is None:
        return
    assert cf["health"] == "unprobed"
    assert cf["qualification_status"] == "unqualified"
    assert cf["available"] is False
    assert cf["coding_suitability"] == "unknown"


def test_ollama_healthy_probe_is_zero_spend_ok(monkeypatch) -> None:
    monkeypatch.setenv("SWARM_ALLOW_PAID", "false")
    with patch(
        "swarm.providers.capability_registry._probe",
        side_effect=lambda pid: (
            ("healthy", 5.0, 2, "auth probe ok")
            if pid == "ollama"
            else ("unprobed", None, None, "skipped")
        ),
    ):
        report = build_capability_registry(probe=True, repo=Path.cwd())
    ollama = next(p for p in report["providers"] if p["provider_id"] == "ollama")
    assert ollama["health"] == "healthy"
    assert ollama["cost_policy"] == "zero_spend_ok"
    assert ollama["available"] is True
    assert ollama["qualification_status"] == "auth_ok"
    assert ollama["coding_suitability"] == "unknown"
    rows = routable_providers(report)
    assert any(r["provider_id"] == "ollama" for r in rows)


def test_routable_providers_fail_closed_on_unprobed(monkeypatch) -> None:
    monkeypatch.setenv("SWARM_ALLOW_PAID", "false")
    report = {
        "providers": [
            {
                "provider_id": "ollama",
                "qualification_status": "unqualified",
                "cost_policy": "price_unverified",
                "health": "unprobed",
            },
            {
                "provider_id": "ollama_ok",
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
    assert [r["provider_id"] for r in rows] == ["ollama_ok"]


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
