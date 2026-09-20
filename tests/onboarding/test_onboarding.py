"""P15 onboarding tests — offline only."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pytest

from swarm.contracts.common import utc_now
from swarm.onboarding.audit import AuditLog
from swarm.onboarding.canary import CanaryDeniedError, bounded_canary
from swarm.onboarding.inventory import inventory_secret_refs
from swarm.onboarding.service import OnboardingService
from swarm.onboarding.status import AccountOnboardingStatus


def test_secret_presence_is_not_authentication(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-not-a-real-key-value")
    refs = inventory_secret_refs(["OPENROUTER_API_KEY"])
    assert refs[0].present is True
    svc = OnboardingService(tmp_path / "onboarding")
    detail = svc.inspect_provider("openrouter")
    assert detail["secret_presence_is_not_auth"] is True
    assert AccountOnboardingStatus.AUTH_VERIFIED.value not in detail["account_status"]
    assert detail["account_status"] == AccountOnboardingStatus.CONFIGURED.value
    assert "sk-test" not in json.dumps(detail)


def test_retired_provider_skipped(tmp_path: Path) -> None:
    svc = OnboardingService(tmp_path / "onboarding")
    detail = svc.inspect_provider("github_models")
    assert detail["retired"] is True
    assert detail["account_status"] == AccountOnboardingStatus.RETIRED.value
    assert detail["blockers"][0]["code"] == "retired"
    assert detail["blockers"][0]["resumable"] is False


def test_auth_session_unavailable_is_resumable_blocker(tmp_path: Path) -> None:
    svc = OnboardingService(tmp_path / "onboarding")
    detail = svc.inspect_provider("groq")
    codes = {b["code"] for b in detail["blockers"]}
    assert "auth_session_unavailable" in codes
    blocker = next(b for b in detail["blockers"] if b["code"] == "auth_session_unavailable")
    assert blocker["resumable"] is True
    assert blocker["user_action"]


@pytest.mark.asyncio
async def test_paid_and_unknown_cost_denied() -> None:
    with pytest.raises(CanaryDeniedError):
        await bounded_canary(route_id="rt_fake_alpha", allow_paid=True)
    denied = await bounded_canary(
        route_id="rt_paid",
        mode="live",
        billing_known_zero=False,
    )
    assert denied["denied"] is True
    assert denied["status"] == "unknown_cost_denied"


@pytest.mark.asyncio
async def test_bounded_mock_probe_counted() -> None:
    result = await bounded_canary(route_id="rt_fake_alpha", mode="mock", billing_known_zero=True)
    assert result["denied"] is False
    assert result["probe_counted"] is True
    assert result["consumed_allowance"] >= 1
    assert result["mock_vs_live"] == "mock_broker_fixtures_only"


def test_no_duplicate_accounts(tmp_path: Path) -> None:
    svc = OnboardingService(tmp_path / "onboarding")
    svc.register_account_alias("personal_groq")
    with pytest.raises(ValueError, match="duplicate"):
        svc.register_account_alias("personal_groq")


def test_expiring_trial_disabled_at_expiry(tmp_path: Path) -> None:
    svc = OnboardingService(tmp_path / "onboarding")
    svc.set_trial_expiry("cerebras", utc_now() - timedelta(hours=1))
    detail = svc.inspect_provider("cerebras")
    assert detail["trial_expired"] is True
    assert detail["account_status"] == AccountOnboardingStatus.BLOCKED.value
    assert detail["route_status"] == "disabled"


def test_manual_confirmation_auditable_no_credentials(tmp_path: Path) -> None:
    audit = AuditLog(tmp_path / "audit.json")
    svc = OnboardingService(tmp_path / "onboarding", audit=audit)
    entry = svc.confirm_manual(
        provider_id="ollama",
        actor="operator",
        statement="Local ollama endpoint reachable on loopback",
        fields={"endpoint": "http://127.0.0.1:11434", "secret_ref_names": ["unused"]},
        new_status=AccountOnboardingStatus.CONFIGURED,
    )
    assert entry["contains_credentials"] is False
    blob = (tmp_path / "audit.json").read_text()
    assert "sk-" not in blob
    with pytest.raises(ValueError, match="credentials"):
        svc.confirm_manual(
            provider_id="groq",
            actor="operator",
            statement="bad",
            fields={"note": "sk-abc1234567890"},
        )


def test_onboarding_report_written(tmp_path: Path) -> None:
    svc = OnboardingService(tmp_path / "onboarding")
    report = svc.onboarding_report()
    assert report["live_activation_blocked"] is True
    assert (tmp_path / "onboarding" / "onboarding-report.json").exists()
    assert report["counts"]["cataloged"] >= 1
    assert report["essential_next_actions"]
