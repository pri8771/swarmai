"""Auditable manual confirmation records — never store raw credentials."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.onboarding.inventory import scrub_mapping


@dataclass
class ManualConfirmation:
    confirmation_id: str
    provider_id: str
    actor: str
    statement: str
    fields: dict[str, Any]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "confirmation_id": self.confirmation_id,
            "provider_id": self.provider_id,
            "actor": self.actor,
            "statement": self.statement,
            "fields": scrub_mapping(self.fields),
            "created_at": self.created_at,
            "contains_credentials": False,
        }


@dataclass
class AuditLog:
    path: Path
    entries: list[ManualConfirmation] = field(default_factory=list)

    def append(
        self,
        *,
        provider_id: str,
        actor: str,
        statement: str,
        fields: dict[str, Any] | None = None,
    ) -> ManualConfirmation:
        raw = fields or {}
        blob = json.dumps(raw)
        if "sk-" in blob or "api_key=" in blob.lower() or "Bearer " in blob:
            raise ValueError("manual_confirmation_must_not_contain_credentials")
        cleaned = scrub_mapping(raw)
        entry = ManualConfirmation(
            confirmation_id=new_id("mc_"),
            provider_id=provider_id,
            actor=actor,
            statement=statement,
            fields=cleaned,
            created_at=utc_now().isoformat(),
        )
        self.entries.append(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing: list[dict[str, Any]] = []
        if self.path.exists():
            existing = json.loads(self.path.read_text())
        existing.append(entry.to_dict())
        self.path.write_text(json.dumps(existing, indent=2) + "\n")
        return entry
