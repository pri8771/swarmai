"""Zero-spend cost ledger for missions and CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import utc_now


@dataclass
class CostEntry:
    source: str
    route_id: str | None
    model: str | None
    requests: int = 0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float = 0.0
    at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "route_id": self.route_id,
            "model": self.model,
            "requests": self.requests,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": self.cost_usd,
            "at": self.at,
        }


@dataclass
class CostLedger:
    spend_policy: str = "zero"
    allow_paid: bool = False
    entries: list[CostEntry] = field(default_factory=list)

    @property
    def total_usd(self) -> float:
        return round(sum(e.cost_usd for e in self.entries), 6)

    def add(self, entry: CostEntry) -> None:
        if entry.cost_usd > 0 and not self.allow_paid:
            raise PermissionError("paid_cost_denied_under_zero_spend_policy")
        self.entries.append(entry)

    def to_dict(self) -> dict[str, Any]:
        return {
            "spend_policy": self.spend_policy,
            "allow_paid": self.allow_paid,
            "total_usd": self.total_usd,
            "entries": [e.to_dict() for e in self.entries],
        }


def load_mission_costs(missions_dir: Path) -> CostLedger:
    ledger = CostLedger()
    if not missions_dir.is_dir():
        return ledger
    for path in sorted(missions_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        cost = data.get("cost") or {}
        ledger.add(
            CostEntry(
                source=str(data.get("mission_id") or path.name),
                route_id=None,
                model=None,
                requests=int(cost.get("requests") or 0),
                prompt_tokens=cost.get("prompt_tokens"),
                completion_tokens=cost.get("completion_tokens"),
                cost_usd=float(cost.get("total_usd") or 0.0),
                at=str(data.get("updated_at") or utc_now().isoformat()),
            )
        )
    return ledger


def format_cost_show(ledger: CostLedger) -> dict[str, Any]:
    return {
        "spend_policy": ledger.spend_policy,
        "allow_paid": ledger.allow_paid,
        "total_usd": ledger.total_usd,
        "entry_count": len(ledger.entries),
        "entries": [e.to_dict() for e in ledger.entries],
        "note": "Zero-spend policy enforced; local inference recorded at $0.00",
    }
