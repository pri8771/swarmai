"""Provider onboarding service — offline-safe inventory and reports."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from swarm.contracts.common import utc_now
from swarm.onboarding.audit import AuditLog
from swarm.onboarding.inventory import inventory_secret_refs, scrub_mapping
from swarm.onboarding.status import (
    AccountOnboardingStatus,
    AdapterOnboardingStatus,
    CatalogLayer,
    RouteOnboardingStatus,
)
from swarm.providers.catalog import (
    CORE_PROVIDER_IDS,
    RETIRED_PROVIDER_IDS,
    list_providers,
    load_catalog,
)

# Providers known to require payment method before usable trial (do not attach cards).
PAYMENT_GATED_IDS = frozenset({"cerebras"})
PURPOSE_REVIEW_IDS = frozenset({"nvidia_nim", "cohere"})


@dataclass
class OnboardingBlocker:
    provider_id: str
    code: str
    message: str
    resumable: bool = True
    user_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "code": self.code,
            "message": self.message,
            "resumable": self.resumable,
            "user_action": self.user_action,
        }


@dataclass
class OnboardingService:
    state_dir: Path
    audit: AuditLog | None = None
    # In-memory account overrides from auditable manual confirmation (never secrets).
    account_overrides: dict[str, AccountOnboardingStatus] = field(default_factory=dict)
    trial_expiry: dict[str, datetime] = field(default_factory=dict)
    seen_account_aliases: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        if self.audit is None:
            self.audit = AuditLog(self.state_dir / "manual_confirmations.json")

    def _adapter_status(self, provider_id: str, retired: bool) -> AdapterOnboardingStatus:
        if retired or provider_id in RETIRED_PROVIDER_IDS:
            return AdapterOnboardingStatus.RETIRED
        if provider_id in CORE_PROVIDER_IDS:
            return AdapterOnboardingStatus.OFFLINE_TESTED
        return AdapterOnboardingStatus.NOT_IMPLEMENTED

    def _account_status(
        self, entry: dict[str, Any], *, secret_present: bool
    ) -> AccountOnboardingStatus:
        pid = entry["id"]
        if pid in RETIRED_PROVIDER_IDS or entry.get("service_status") == "retired":
            return AccountOnboardingStatus.RETIRED
        if pid in self.account_overrides:
            return self.account_overrides[pid]
        if pid in PAYMENT_GATED_IDS:
            return AccountOnboardingStatus.GATED_PAYMENT
        raw = entry.get("account_status", "unknown")
        # Secret presence is NOT authentication.
        if secret_present and raw in {"unknown", "existing_unverified"}:
            return AccountOnboardingStatus.CONFIGURED
        try:
            return AccountOnboardingStatus(raw)
        except ValueError:
            return AccountOnboardingStatus.UNKNOWN

    def _layers(self, provider_id: str, *, secret_present: bool, retired: bool) -> list[str]:
        layers = [CatalogLayer.CATALOGED.value]
        if provider_id in CORE_PROVIDER_IDS and not retired:
            layers.append(CatalogLayer.IMPLEMENTED.value)
        if secret_present:
            layers.append(CatalogLayer.CONFIGURED.value)
        # AUTHENTICATED never added from key presence alone.
        return layers

    def inspect_provider(self, provider_id: str, *, metadata_only: bool = True) -> dict[str, Any]:
        catalog = load_catalog()
        entry = next((p for p in catalog.get("providers", []) if p["id"] == provider_id), None)
        if entry is None:
            return {"error": "not_found", "provider_id": provider_id}
        retired = provider_id in RETIRED_PROVIDER_IDS or entry.get("service_status") == "retired"
        refs = inventory_secret_refs(list(entry.get("env_vars", [])))
        secret_present = any(r.present for r in refs)
        account = self._account_status(entry, secret_present=secret_present)
        adapter = self._adapter_status(provider_id, retired)
        blockers = self._blockers_for(entry, account=account, retired=retired)
        # Disable expired trials.
        expired = False
        if provider_id in self.trial_expiry and self.trial_expiry[provider_id] <= utc_now():
            expired = True
            account = AccountOnboardingStatus.BLOCKED
        return scrub_mapping(
            {
                "provider_id": provider_id,
                "name": entry.get("name"),
                "metadata_only": metadata_only,
                "retired": retired,
                "layers": self._layers(provider_id, secret_present=secret_present, retired=retired),
                "account_status": account.value,
                "adapter_status": adapter.value,
                "route_status": (
                    RouteOnboardingStatus.DISABLED.value
                    if retired or expired or account in {
                        AccountOnboardingStatus.BLOCKED,
                        AccountOnboardingStatus.GATED_PAYMENT,
                    }
                    else RouteOnboardingStatus.DISCOVERED.value
                ),
                "secret_refs": [{"name": r.name, "present": r.present} for r in refs],
                "secret_presence_is_not_auth": True,
                "charge_prevention_verified": bool(entry.get("charge_prevention_verified")),
                "published_offer_category": entry.get("published_offer_category"),
                "entry_url": entry.get("entry_url"),
                "required_next_action": entry.get("required_next_action"),
                "blockers": [b.to_dict() for b in blockers],
                "trial_expired": expired,
                "mock_vs_live": "metadata_inventory_only",
            }
        )

    def _blockers_for(
        self,
        entry: dict[str, Any],
        *,
        account: AccountOnboardingStatus,
        retired: bool,
    ) -> list[OnboardingBlocker]:
        pid = entry["id"]
        out: list[OnboardingBlocker] = []
        if retired:
            out.append(
                OnboardingBlocker(
                    pid,
                    "retired",
                    "Provider is retired — no signup or inference",
                    resumable=False,
                )
            )
            return out
        if pid in PAYMENT_GATED_IDS:
            out.append(
                OnboardingBlocker(
                    pid,
                    "payment_method_required",
                    "Documented payment-method-gated trial — do not attach a card automatically",
                    user_action=(
                        "Owner must decide whether to complete provider payment verification "
                        "themselves; SwarmAI will not add a card."
                    ),
                )
            )
        if pid in PURPOSE_REVIEW_IDS:
            out.append(
                OnboardingBlocker(
                    pid,
                    "purpose_review_required",
                    "Development/evaluation arrangement needs purpose review before activation",
                    user_action="Confirm allowed operating purpose for this provider",
                )
            )
        if account in {
            AccountOnboardingStatus.UNKNOWN,
            AccountOnboardingStatus.EXISTING_UNVERIFIED,
            AccountOnboardingStatus.SIGNUP_NEEDED,
            AccountOnboardingStatus.VERIFICATION_NEEDED,
        }:
            out.append(
                OnboardingBlocker(
                    pid,
                    "auth_session_unavailable",
                    "No authenticated browser/session available for signup or inspection",
                    user_action=(
                        f"Open {entry.get('entry_url')} ; complete login/MFA if needed; "
                        f"store least-privilege key as env "
                        f"{(entry.get('env_vars') or ['?'])[0]}; "
                        "then re-run onboarding-report"
                    ),
                )
            )
        if not entry.get("charge_prevention_verified"):
            out.append(
                OnboardingBlocker(
                    pid,
                    "charge_prevention_unverified",
                    "Zero-charge enforcement not verified — stay disabled in no-spend mode",
                    user_action="Verify free/no-charge route eligibility on the provider console",
                )
            )
        return out

    def list_with_account_status(self, *, mode: str = "mock") -> dict[str, Any]:
        rows = []
        for base in list_providers(mode=mode):
            detail = self.inspect_provider(base["id"])
            overlay_keys = (
                "layers",
                "account_status",
                "adapter_status",
                "route_status",
                "secret_refs",
                "secret_presence_is_not_auth",
                "blockers",
                "trial_expired",
            )
            overlay: dict[str, Any] = {
                k: detail[k] for k in overlay_keys if k in detail
            }
            rows.append({**base, **overlay})
        return {
            "mode": mode,
            "mock_vs_live": "catalog_inventory_not_live",
            "providers": rows,
        }

    def register_account_alias(self, alias: str) -> None:
        if alias in self.seen_account_aliases:
            raise ValueError("duplicate_account_alias_forbidden")
        self.seen_account_aliases.add(alias)

    def confirm_manual(
        self,
        *,
        provider_id: str,
        actor: str,
        statement: str,
        fields: dict[str, Any] | None = None,
        new_status: AccountOnboardingStatus | None = None,
    ) -> dict[str, Any]:
        assert self.audit is not None
        entry = self.audit.append(
            provider_id=provider_id,
            actor=actor,
            statement=statement,
            fields=fields,
        )
        if new_status is not None:
            self.account_overrides[provider_id] = new_status
        return entry.to_dict()

    def set_trial_expiry(self, provider_id: str, expires_at: datetime) -> None:
        self.trial_expiry[provider_id] = expires_at

    def onboarding_report(self) -> dict[str, Any]:
        catalog = load_catalog()
        providers = [self.inspect_provider(p["id"]) for p in catalog.get("providers", [])]
        essential_actions: list[dict[str, str]] = []
        for p in providers:
            if p.get("retired"):
                continue
            for b in p.get("blockers", []):
                if b.get("user_action"):
                    essential_actions.append(
                        {
                            "provider_id": p["provider_id"],
                            "code": b["code"],
                            "action": b["user_action"],
                        }
                    )
        report = {
            "schema_version": "1.0",
            "generated_at": utc_now().isoformat(),
            "mock_vs_live": "offline_onboarding_report",
            "live_activation_blocked": True,
            "notice": (
                "No account creation claimed. Secret presence is not auth. "
                "No payment methods attached. Live canaries blocked until "
                "operator completes access."
            ),
            "providers": providers,
            "essential_next_actions": essential_actions[:20],
            "counts": {
                "cataloged": len(providers),
                "implemented": sum(
                    1 for p in providers if CatalogLayer.IMPLEMENTED.value in p.get("layers", [])
                ),
                "configured": sum(
                    1 for p in providers if CatalogLayer.CONFIGURED.value in p.get("layers", [])
                ),
                "retired": sum(1 for p in providers if p.get("retired")),
                "gated_payment": sum(
                    1
                    for p in providers
                    if p.get("account_status") == AccountOnboardingStatus.GATED_PAYMENT.value
                ),
            },
        }
        out = self.state_dir / "onboarding-report.json"
        out.write_text(json.dumps(report, indent=2) + "\n")
        return report
