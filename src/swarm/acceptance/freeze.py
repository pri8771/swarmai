"""Frozen V2.0 acceptance campaign catalog (mandate §10)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

GateId = Literal["deterministic", "live", "host", "elapsed"]

# Canonical freeze lives in-repo; harness refuses to run if missing/corrupt.
FREEZE_PATH = (
    Path(__file__).resolve().parents[3]
    / "benchmarks"
    / "v20_acceptance"
    / "scenarios.freeze.json"
)

REQUIRED_SCENARIO_IDS: tuple[str, ...] = (
    "V20-S01",
    "V20-S02",
    "V20-S03",
    "V20-S04",
    "V20-S05",
    "V20-S06",
    "V20-S07",
    "V20-S08",
    "V20-S09",
    "V20-S10",
    "V20-S11",
    "V20-S12",
)


class FreezeIntegrityError(ValueError):
    """Raised when the frozen catalog is missing, incomplete, or mutated unsafely."""


@dataclass(frozen=True)
class ScenarioSpec:
    id: str
    title: str
    mandate_ref: str
    primary_gate: GateId
    also_gates: tuple[GateId, ...]
    versions: tuple[str, ...]
    setup: str
    pass_criteria: tuple[str, ...]
    fail_criteria: tuple[str, ...]
    deterministic_probe: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "mandate_ref": self.mandate_ref,
            "primary_gate": self.primary_gate,
            "also_gates": list(self.also_gates),
            "versions": list(self.versions),
            "setup": self.setup,
            "pass_criteria": list(self.pass_criteria),
            "fail_criteria": list(self.fail_criteria),
            "deterministic_probe": self.deterministic_probe,
        }


@dataclass(frozen=True)
class AcceptanceFreeze:
    schema_version: str
    freeze_id: str
    frozen_at: str
    public_hostname: str
    version_claim_policy: str
    spend_policy: str
    gates: dict[str, dict[str, Any]]
    scenarios: tuple[ScenarioSpec, ...]
    version_matrices: dict[str, dict[str, Any]]
    observation_windows: dict[str, Any]
    raw: dict[str, Any]
    content_hash: str

    def scenario(self, scenario_id: str) -> ScenarioSpec:
        for s in self.scenarios:
            if s.id == scenario_id:
                return s
        raise KeyError(scenario_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "freeze_id": self.freeze_id,
            "frozen_at": self.frozen_at,
            "public_hostname": self.public_hostname,
            "version_claim_policy": self.version_claim_policy,
            "spend_policy": self.spend_policy,
            "content_hash": self.content_hash,
            "scenario_count": len(self.scenarios),
            "scenario_ids": [s.id for s in self.scenarios],
            "gates": sorted(self.gates.keys()),
            "version_matrices": {
                k: {
                    "title": v.get("title"),
                    "required_scenarios": list(v.get("required_scenarios") or []),
                    "accepted": bool(v.get("accepted")),
                }
                for k, v in self.version_matrices.items()
            },
            "observation_windows": self.observation_windows,
        }


def _parse_scenario(row: dict[str, Any]) -> ScenarioSpec:
    primary = str(row["primary_gate"])
    if primary not in {"deterministic", "live", "host", "elapsed"}:
        raise FreezeIntegrityError(f"invalid_primary_gate:{row.get('id')}:{primary}")
    also_raw = row.get("also_gates") or []
    also: list[GateId] = []
    for g in also_raw:
        gs = str(g)
        if gs not in {"deterministic", "live", "host", "elapsed"}:
            raise FreezeIntegrityError(f"invalid_also_gate:{row.get('id')}:{gs}")
        also.append(gs)  # type: ignore[arg-type]
    pass_c = tuple(str(x) for x in (row.get("pass_criteria") or []))
    fail_c = tuple(str(x) for x in (row.get("fail_criteria") or []))
    if not pass_c:
        raise FreezeIntegrityError(f"missing_pass_criteria:{row.get('id')}")
    return ScenarioSpec(
        id=str(row["id"]),
        title=str(row["title"]),
        mandate_ref=str(row["mandate_ref"]),
        primary_gate=primary,  # type: ignore[arg-type]
        also_gates=tuple(also),
        versions=tuple(str(v) for v in (row.get("versions") or [])),
        setup=str(row.get("setup") or ""),
        pass_criteria=pass_c,
        fail_criteria=fail_c,
        deterministic_probe=str(row.get("deterministic_probe") or ""),
    )


def content_hash_for(raw: dict[str, Any]) -> str:
    """Stable hash of freeze body excluding any post-hoc hash field."""
    payload = {k: v for k, v in raw.items() if k != "content_hash"}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def load_freeze(path: Path | None = None) -> AcceptanceFreeze:
    target = path or FREEZE_PATH
    if not target.is_file():
        raise FreezeIntegrityError(f"freeze_missing:{target}")
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FreezeIntegrityError(f"freeze_unreadable:{target}:{exc}") from exc
    if not isinstance(raw, dict):
        raise FreezeIntegrityError("freeze_not_object")
    scenarios = tuple(_parse_scenario(s) for s in (raw.get("scenarios") or []))
    freeze = AcceptanceFreeze(
        schema_version=str(raw.get("schema_version") or ""),
        freeze_id=str(raw.get("freeze_id") or ""),
        frozen_at=str(raw.get("frozen_at") or ""),
        public_hostname=str(raw.get("public_hostname") or ""),
        version_claim_policy=str(raw.get("version_claim_policy") or ""),
        spend_policy=str(raw.get("spend_policy") or ""),
        gates=dict(raw.get("gates") or {}),
        scenarios=scenarios,
        version_matrices=dict(raw.get("version_matrices") or {}),
        observation_windows=dict(raw.get("observation_windows") or {}),
        raw=raw,
        content_hash=content_hash_for(raw),
    )
    verify_freeze_integrity(freeze)
    return freeze


def verify_freeze_integrity(freeze: AcceptanceFreeze) -> None:
    if freeze.schema_version != "2.0.0":
        raise FreezeIntegrityError(f"unexpected_schema:{freeze.schema_version}")
    if freeze.version_claim_policy != "never_mark_accepted_from_harness":
        raise FreezeIntegrityError("version_claim_policy_must_forbid_harness_accept")
    if freeze.spend_policy != "zero_no_invented_live_grant":
        raise FreezeIntegrityError("spend_policy_must_forbid_invented_grants")
    if freeze.public_hostname != "swarm.splitsignal.ai":
        raise FreezeIntegrityError(f"hostname_mismatch:{freeze.public_hostname}")
    ids = [s.id for s in freeze.scenarios]
    if tuple(ids) != REQUIRED_SCENARIO_IDS:
        raise FreezeIntegrityError(
            f"scenario_set_mismatch:expected={list(REQUIRED_SCENARIO_IDS)} got={ids}"
        )
    for gate in ("deterministic", "live", "host", "elapsed"):
        if gate not in freeze.gates:
            raise FreezeIntegrityError(f"missing_gate:{gate}")
    windows = freeze.observation_windows.get("elapsed_reliability") or {}
    if windows.get("simulate_elapsed_time") is not False:
        raise FreezeIntegrityError("elapsed_simulation_forbidden")
    for ver, meta in freeze.version_matrices.items():
        if meta.get("accepted") is True:
            raise FreezeIntegrityError(f"freeze_must_not_preclaim_accepted:{ver}")
        required = list(meta.get("required_scenarios") or [])
        for sid in required:
            freeze.scenario(sid)
