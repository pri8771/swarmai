"""V1.0 public contract freeze + compatibility surface."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.product.contracts import PUBLIC_RESOURCES, public_product_contract

# Frozen V1 public surface — bump only with explicit migration notes.
V1_CONTRACT_VERSION = "1.0.0"
V1_COMPATIBILITY_POLICY = "backward_compatible_additive_only"


@dataclass
class ContractFreezeReport:
    run_id: str
    contract_version: str = V1_CONTRACT_VERSION
    ok: bool = False
    resources: list[str] = field(default_factory=list)
    endpoints: dict[str, list[str]] = field(default_factory=dict)
    cli: dict[str, list[str]] = field(default_factory=dict)
    schema_files: list[str] = field(default_factory=list)
    hash: str = ""
    policy: str = V1_COMPATIBILITY_POLICY
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "contract_version": self.contract_version,
            "ok": self.ok,
            "resources": self.resources,
            "endpoints": self.endpoints,
            "cli": self.cli,
            "schema_files": self.schema_files,
            "hash": self.hash,
            "policy": self.policy,
            "notes": self.notes,
            "generated_at": utc_now().isoformat(),
            "mock_vs_live": "contract_freeze_offline",
        }


def freeze_public_contracts(repo: Path) -> ContractFreezeReport:
    """Snapshot and persist the V1 public contract surface."""
    repo = repo.resolve()
    contract = public_product_contract()
    schema_dir = repo / "schemas" / "contracts"
    schema_files = sorted(str(p.relative_to(repo)) for p in schema_dir.glob("*.schema.json"))
    # Also write a frozen product contract snapshot (versioned).
    freeze_dir = repo / "schemas" / "v1"
    freeze_dir.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "contract_version": V1_CONTRACT_VERSION,
        "policy": V1_COMPATIBILITY_POLICY,
        "resources": list(PUBLIC_RESOURCES),
        "product_contract": contract,
        "frozen_at": utc_now().isoformat(),
    }
    raw = json.dumps(snapshot, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    snapshot["hash"] = digest
    (freeze_dir / "product_contract.v1.json").write_text(
        json.dumps(snapshot, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (freeze_dir / "COMPATIBILITY.md").write_text(
        "\n".join(
            [
                f"# V1 Contract Compatibility (`{V1_CONTRACT_VERSION}`)",
                "",
                f"Policy: **{V1_COMPATIBILITY_POLICY}**",
                "",
                "- Additive fields/endpoints OK without major bump",
                "- Removals/renames require major version + migration guide",
                "- Secret values must never appear in contracts or reports",
                "- Zero-spend remains the default unless explicitly overridden",
                "",
                f"Frozen hash: `{digest}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    report = ContractFreezeReport(
        run_id=new_id("freeze_"),
        resources=list(PUBLIC_RESOURCES),
        endpoints=dict(contract.get("endpoints") or {}),
        cli=dict(contract.get("cli") or {}),
        schema_files=schema_files + ["schemas/v1/product_contract.v1.json"],
        hash=digest,
        ok=True,
        notes=[
            "Public product resources frozen for V1 RC",
            "Breaking changes require explicit migration + version bump",
        ],
    )
    out = repo / "var" / "reports" / "v1"
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest_contract_freeze.json").write_text(
        json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
    return report
