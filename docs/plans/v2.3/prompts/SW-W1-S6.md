# SW-W1-S6 — Portability bundle v2: history, tombstones, remap, compatibility, value-based secret scan (F-03)

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S6` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w1-s6-portability-v2` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | none |
| Handoff file | `docs/v2.3/sessions/SW-W1-S6.md` |
| Independent reviewer | Codex (owner decision D2). You never accept your own work. |
| Plan | `docs/plans/v2.3/PLAN.md`; owner preflight `docs/plans/v2.3/OWNER_PREFLIGHT.md`; decisions `docs/swarm-mvp/DECISIONS.md` |

## 0. Hard rules (read twice)
1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.
2. Never push to, or merge into, `main`, `dev` or `cursor/sw-v23-integration-460c`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `cursor/sw-v23-integration-460c`.
3. Zero spend: no real model/provider calls, no paid APIs, no account creation, no deploys. `SWARM_ALLOW_PAID` stays `false`. Tests use fakes only.
4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n "$NAME"`.
5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.
6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).
7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.
8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.

## 1. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (S1)
git fetch origin cursor/sw-v23-integration-460c
git ls-remote --exit-code origin refs/heads/cursor/sw-v23-integration-460c >/dev/null && echo INTEG_OK || echo INTEG_MISSING
```
If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it.
```bash
git checkout -b cursor/v23-w1-s6-portability-v2 origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
This session has **no dependencies**. Go to Step 1.

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/product/portability.py` — modify
- `tests/portability/test_v23_bundle.py` — create
- `docs/v2.3/sessions/SW-W1-S6.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Complete ART-V23-PORTABILITY and fix finding **F-03**.
- Today secret stripping only checks key names; a value like `"sk-…"` under a harmless key passes, and any `"env:…"` string passes under a secret key.
- Bundles also carry no history, receipts or approvals.

**Schema 2 adds:**
- Sections `history`, `receipts`, `approvals`, `leases` and `artifact_digests`, each with its own digest.
- Approvals and leases are **tombstoned** (`executable: false`, `state: "tombstoned"`), so imported authority can never run.
- A compatibility check (`min_reader`) and a namespace remap on import (`target_project_id`).
- A value-based secret scan over every string, with strict `env:NAME` references.

Schema-1 bundles still import, and existing callers (`product/portable_protocol.py`, `tests/controller/test_v23_v20.py`, `tests/portability/test_portable_protocol.py`) are unchanged.

The code below was compiled and run against `dev @ 8e1c0fde` (7 new tests pass; the existing portability tests pass unchanged). Paste it **exactly**.

### Step 1 — `src/swarm/product/portability.py` (replace the whole file, exactly)
```python
"""V2.3 portability export/import — never include secrets or live authority.

Bundle schema 2 (ART-V23-PORTABILITY) adds verifiable history sections:
``history``, ``receipts``, ``approvals``, ``leases`` and ``artifact_digests``, each
with its own digest. Imported approvals and leases are tombstoned: they are kept
for provenance but can never execute. Schema-1 bundles still import unchanged.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, payload_hash, utc_now

FORBIDDEN = ("password", "secret", "token", "api_key", "apikey", "credential", "private_key")
BUNDLE_SCHEMA = "2"
READER_SCHEMA = 2
SECTION_NAMES = ("history", "receipts", "approvals", "leases", "artifact_digests")
ENV_REF = re.compile(r"^env:[A-Z_][A-Z0-9_]*$")
SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[abpr]-[A-Za-z0-9\-]{8,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{12,}"),
    re.compile(r"(?i)(password|secret|token|api_key)=[^\s&]+"),
)


def _reject_secrets(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            lowered = str(key).lower()
            if any(f in lowered for f in FORBIDDEN) and not isinstance(value, dict | list):
                if value not in (None, "") and not (
                    isinstance(value, str) and ENV_REF.match(value)
                ):
                    raise ValueError(f"secret_in_bundle:{path}.{key}")
            _reject_secrets(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _reject_secrets(item, f"{path}[{i}]")
    elif isinstance(obj, str):
        for pattern in SECRET_VALUE_PATTERNS:
            if pattern.search(obj):
                raise ValueError(f"secret_value_in_bundle:{path}")


def _tombstone(items: list[dict[str, Any]], bundle_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        row["original_state"] = row.get("state")
        row["state"] = "tombstoned"
        row["executable"] = False
        row["tombstoned_by_bundle"] = bundle_id
        out.append(row)
    return out


def _remap(items: list[dict[str, Any]], old: str, new: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        if row.get("project_id") == old:
            row["project_id"] = new
        out.append(row)
    return out


@dataclass
class PortabilityBundle:
    bundle_id: str
    project_id: str
    created_at: str
    integrity_digest: str
    project_config: dict[str, Any] = field(default_factory=dict)
    knowledge_refs: list[str] = field(default_factory=list)
    capability_pack_config: dict[str, Any] = field(default_factory=dict)
    policy_refs: list[str] = field(default_factory=list)
    artifact_refs: list[str] = field(default_factory=list)
    version_manifest: dict[str, str] = field(default_factory=dict)
    schema_version: str = "1"
    sections: dict[str, Any] = field(default_factory=dict)
    section_digests: dict[str, str] = field(default_factory=dict)
    compatibility: dict[str, Any] = field(default_factory=dict)
    remapped_from: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "bundle_id": self.bundle_id,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "integrity_digest": self.integrity_digest,
            "project_config": dict(self.project_config),
            "knowledge_refs": list(self.knowledge_refs),
            "capability_pack_config": dict(self.capability_pack_config),
            "policy_refs": list(self.policy_refs),
            "artifact_refs": list(self.artifact_refs),
            "version_manifest": dict(self.version_manifest),
        }
        if self.schema_version != "1":
            out["schema_version"] = self.schema_version
            out["sections"] = dict(self.sections)
            out["section_digests"] = dict(self.section_digests)
            out["compatibility"] = dict(self.compatibility)
        if self.remapped_from is not None:
            out["remapped_from"] = self.remapped_from
        return out


def _digest_body(data: dict[str, Any]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "project_id": data["project_id"],
        "project_config": data.get("project_config") or {},
        "knowledge_refs": data.get("knowledge_refs") or [],
        "capability_pack_config": data.get("capability_pack_config") or {},
        "policy_refs": data.get("policy_refs") or [],
        "artifact_refs": data.get("artifact_refs") or [],
        "version_manifest": data.get("version_manifest") or {},
    }
    if str(data.get("schema_version", "1")) != "1":
        body["schema_version"] = str(data["schema_version"])
        body["section_digests"] = data.get("section_digests") or {}
        body["compatibility"] = data.get("compatibility") or {}
    return body


class PortabilityService:
    def export_project(
        self,
        *,
        project_id: str,
        project_config: dict[str, Any],
        knowledge_refs: list[str] | None = None,
        capability_pack_config: dict[str, Any] | None = None,
        policy_refs: list[str] | None = None,
        artifact_refs: list[str] | None = None,
        version_manifest: dict[str, str] | None = None,
        out_dir: Path | None = None,
        history: list[dict[str, Any]] | None = None,
        receipts: list[dict[str, Any]] | None = None,
        approvals: list[dict[str, Any]] | None = None,
        leases: list[dict[str, Any]] | None = None,
        artifact_digests: dict[str, str] | None = None,
    ) -> PortabilityBundle:
        bundle_id = new_id("port_")
        config = dict(project_config)
        packs = dict(capability_pack_config or {})
        sections: dict[str, Any] = {
            "history": list(history or []),
            "receipts": list(receipts or []),
            "approvals": _tombstone(list(approvals or []), bundle_id),
            "leases": _tombstone(list(leases or []), bundle_id),
            "artifact_digests": dict(artifact_digests or {}),
        }
        data: dict[str, Any] = {
            "bundle_id": bundle_id,
            "project_id": project_id,
            "project_config": config,
            "knowledge_refs": list(knowledge_refs or []),
            "capability_pack_config": packs,
            "policy_refs": list(policy_refs or []),
            "artifact_refs": list(artifact_refs or []),
            "version_manifest": dict(version_manifest or {}),
            "schema_version": BUNDLE_SCHEMA,
            "sections": sections,
            "section_digests": {n: payload_hash({n: sections[n]}) for n in SECTION_NAMES},
            "compatibility": {"min_reader": READER_SCHEMA, "bundle_schema": BUNDLE_SCHEMA},
        }
        _reject_secrets(data)
        bundle = PortabilityBundle(
            bundle_id=bundle_id,
            project_id=project_id,
            created_at=utc_now().isoformat(),
            integrity_digest=payload_hash(_digest_body(data)),
            project_config=config,
            knowledge_refs=data["knowledge_refs"],
            capability_pack_config=packs,
            policy_refs=data["policy_refs"],
            artifact_refs=data["artifact_refs"],
            version_manifest=data["version_manifest"],
            schema_version=BUNDLE_SCHEMA,
            sections=sections,
            section_digests=data["section_digests"],
            compatibility=data["compatibility"],
        )
        target = out_dir or Path("var/portability")
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"{bundle.bundle_id}.json"
        path.write_text(json.dumps(bundle.to_dict(), indent=2) + "\n", encoding="utf-8")
        return bundle

    def import_bundle(
        self, path: Path, *, target_project_id: str | None = None
    ) -> PortabilityBundle:
        data = json.loads(path.read_text(encoding="utf-8"))
        _reject_secrets(data)
        schema = str(data.get("schema_version", "1"))
        if schema not in {"1", BUNDLE_SCHEMA}:
            raise ValueError(f"bundle_incompatible:schema={schema}")
        compat = data.get("compatibility") or {}
        if int(compat.get("min_reader", 1)) > READER_SCHEMA:
            raise ValueError(f"bundle_incompatible:min_reader={compat.get('min_reader')}")
        expected = data.get("integrity_digest")
        digest = payload_hash(_digest_body(data))
        if expected and expected != digest:
            raise ValueError("bundle_integrity_mismatch")
        sections: dict[str, Any] = dict(data.get("sections") or {})
        if schema != "1":
            for name in SECTION_NAMES:
                empty: Any = {} if name == "artifact_digests" else []
                got = payload_hash({name: sections.get(name, empty)})
                if (data.get("section_digests") or {}).get(name) != got:
                    raise ValueError(f"bundle_section_mismatch:{name}")
            for name in ("approvals", "leases"):
                if any(item.get("executable") for item in sections.get(name, [])):
                    raise ValueError(f"bundle_live_authority:{name}")
        project_id = str(data["project_id"])
        remapped_from: str | None = None
        if target_project_id and target_project_id != project_id:
            remapped_from = project_id
            for name in ("history", "receipts", "approvals", "leases"):
                sections[name] = _remap(list(sections.get(name, [])), project_id, target_project_id)
            project_id = target_project_id
        return PortabilityBundle(
            bundle_id=data["bundle_id"],
            project_id=project_id,
            created_at=data.get("created_at") or utc_now().isoformat(),
            integrity_digest=digest,
            project_config=data.get("project_config") or {},
            knowledge_refs=list(data.get("knowledge_refs") or []),
            capability_pack_config=data.get("capability_pack_config") or {},
            policy_refs=list(data.get("policy_refs") or []),
            artifact_refs=list(data.get("artifact_refs") or []),
            version_manifest=data.get("version_manifest") or {},
            schema_version=schema,
            sections=sections,
            section_digests=dict(data.get("section_digests") or {}),
            compatibility=dict(compat),
            remapped_from=remapped_from,
        )
```

### Step 2 — `tests/portability/test_v23_bundle.py` (create, exactly)
```python
"""SW-W1-S6: portability bundle v2 (ART acceptance item 7) and value secret scan (F-03)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from swarm.product.portability import PortabilityService


def _export(svc: PortabilityService, out: Path, **kw: object):
    base: dict[str, object] = {
        "project_id": "proj_src",
        "project_config": {"name": "demo", "db_url": "env:SWARM_DATABASE_URL"},
        "out_dir": out,
    }
    base.update(kw)
    return svc.export_project(**base)  # type: ignore[arg-type]


def test_value_based_secret_scan(tmp_path: Path) -> None:
    svc = PortabilityService()
    for config in (
        {"notes": "use sk-abcdefghijklmnop to call"},
        {"endpoint": "https://x.test/?token=abcd1234"},
        {"header": "Bearer abcdefghijklmnopqrstuvwxyz"},
        {"api_key": "env:not a valid ref"},
        {"password": 12345},
    ):
        with pytest.raises(ValueError, match="secret"):
            _export(svc, tmp_path, project_config=config)
    with pytest.raises(ValueError, match="secret"):
        _export(svc, tmp_path, history=[{"event": "call", "detail": "sk-live-abcdefghijk"}])


def test_roundtrip_with_history_into_clean_root(tmp_path: Path) -> None:
    svc = PortabilityService()
    bundle = _export(
        svc,
        tmp_path / "a",
        history=[{"event": "mission.created", "project_id": "proj_src", "mission_id": "msn_1"}],
        receipts=[{"receipt_id": "sdr_1", "project_id": "proj_src", "digest": "d1"}],
        approvals=[{"approval_id": "apr_1", "state": "approved", "project_id": "proj_src"}],
        leases=[{"lease_id": "ls_1", "state": "active"}],
        artifact_digests={"art_1": "sha256:aa"},
    )
    clean = tmp_path / "clean"
    clean.mkdir()
    src = tmp_path / "a" / f"{bundle.bundle_id}.json"
    (clean / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    loaded = svc.import_bundle(clean / src.name)
    assert loaded.integrity_digest == bundle.integrity_digest
    assert loaded.schema_version == "2"
    assert loaded.sections["artifact_digests"] == {"art_1": "sha256:aa"}
    for name in ("approvals", "leases"):
        for item in loaded.sections[name]:
            assert item["executable"] is False
            assert item["state"] == "tombstoned"
    assert loaded.sections["approvals"][0]["original_state"] == "approved"


def test_tampered_section_rejected(tmp_path: Path) -> None:
    svc = PortabilityService()
    bundle = _export(svc, tmp_path, receipts=[{"receipt_id": "sdr_1", "digest": "d1"}])
    path = tmp_path / f"{bundle.bundle_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["sections"]["receipts"][0]["digest"] = "forged"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="bundle_section_mismatch:receipts"):
        svc.import_bundle(path)


def test_executable_approval_injection_rejected(tmp_path: Path) -> None:
    svc = PortabilityService()
    bundle = _export(svc, tmp_path, approvals=[{"approval_id": "apr_1", "state": "approved"}])
    path = tmp_path / f"{bundle.bundle_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["sections"]["approvals"][0]["executable"] = True
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="bundle_(section_mismatch|live_authority)"):
        svc.import_bundle(path)


def test_incompatible_reader_rejected(tmp_path: Path) -> None:
    svc = PortabilityService()
    bundle = _export(svc, tmp_path)
    path = tmp_path / f"{bundle.bundle_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["compatibility"]["min_reader"] = 99
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="bundle_incompatible"):
        svc.import_bundle(path)


def test_namespace_remap(tmp_path: Path) -> None:
    svc = PortabilityService()
    bundle = _export(
        svc, tmp_path, history=[{"event": "mission.created", "project_id": "proj_src"}]
    )
    loaded = svc.import_bundle(
        tmp_path / f"{bundle.bundle_id}.json", target_project_id="proj_dst"
    )
    assert loaded.project_id == "proj_dst"
    assert loaded.remapped_from == "proj_src"
    assert loaded.sections["history"][0]["project_id"] == "proj_dst"


def test_schema1_bundle_still_imports(tmp_path: Path) -> None:
    from swarm.contracts.common import payload_hash

    body = {
        "project_id": "p",
        "project_config": {"name": "old"},
        "knowledge_refs": [],
        "capability_pack_config": {},
        "policy_refs": [],
        "artifact_refs": [],
        "version_manifest": {},
    }
    data = {"bundle_id": "port_old", "created_at": "2026-01-01T00:00:00+00:00", **body}
    data["integrity_digest"] = payload_hash(body)
    path = tmp_path / "port_old.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    loaded = PortabilityService().import_bundle(path)
    assert loaded.schema_version == "1"
    assert loaded.project_config == {"name": "old"}
```

### Step 3 — run
```bash
uv run pytest tests/portability/test_v23_bundle.py -q          # 7 passed
uv run pytest tests/portability tests/controller/test_v23_v20.py -q   # all pass
```

### Section-5 acceptance
- [ ] Secret values are caught anywhere (config, history, receipts); `env:` references must match `^env:[A-Z_][A-Z0-9_]*$`.
- [ ] Round-trip into a clean directory verifies the integrity and section digests; imported approvals and leases are non-executable tombstones.
- [ ] Tampered sections, injected `executable: true` and incompatible `min_reader` are rejected.
- [ ] Remap rewrites `project_id` in sections and records `remapped_from`.
- [ ] Schema-1 bundles still import.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s6 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s6
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/portability -q
uv run pytest tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives tests/onboarding tests/product tests/providers tests/recovery tests/regressions tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers tests/workspace tests/e2e tests/acceptance tests/portability -q --ignore=tests/integration

# PostgreSQL integration (install steps in “PostgreSQL” below)
uv run pytest tests/integration -q -m integration

git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files
git status --porcelain            # every path listed must be one of YOUR files
```

### PostgreSQL (for the integration line)
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.
If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.

## 7. Acceptance checklist (tick every box in the handoff)
- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.
- [ ] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [ ] `uv run alembic heads` prints exactly one head.
- [ ] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [ ] Integration run passed, or SKIPPED with reason in the handoff.
- [ ] `git status --porcelain` lists only files from section 3 + the handoff.
- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [ ] The Codex review packet (section 11) is in the PR description and the handoff.

## 8. Commit, push, draft PR
```bash
git checkout -- schemas/v1 docs/evidence/fix-004 var
git add src/swarm/product/portability.py tests/portability/test_v23_bundle.py docs/v2.3/sessions/SW-W1-S6.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): portability bundle v2 with section digests, remap, compatibility checks and value secret scan (F-03)" -m "Session: SW-W1-S6. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w1-s6-portability-v2
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w1-s6-portability-v2 --title "[SW-W1-S6] Portability bundle v2: history, tombstones, remap, compatibility, value-based secret scan (F-03)" --body-file docs/v2.3/sessions/SW-W1-S6.md
git ls-remote origin refs/heads/cursor/v23-w1-s6-portability-v2   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S6.md` with exactly these headings:
```markdown
# SW-W1-S6 handoff
- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>
- PR: <url, or compare URL>
## Done
<bullet list of what you implemented>
## Verification
<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>
## Acceptance
<copy the checkboxes from sections 5 and 7, ticked>
## Decisions
<choices you made under hard rule 8, or 'none'>
## Needs other owner
<files outside your scope that should change, with the exact change; or 'none'>
## Codex review packet
<the block from section 11, filled in>
## Status
implemented + tested (NOT accepted; needs Codex review)
```

## 10. STOP conditions (never wait for a human)
STOP immediately when any of these is true:
- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)
- **S2** a dependency check prints `MISSING`.
- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.
- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.
- **S5** finishing would require editing a file that is not in section 3.
- **S6** a required environment variable prints `MISSING`.
- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.
- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).

What to do on STOP, in this order:
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S6.md` then `git commit -m "WIP(SW-W1-S6): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w1-s6-portability-v2` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w1-s6-portability-v2?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S6
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/product/portability.py`, `tests/portability/test_v23_bundle.py`, `docs/v2.3/sessions/SW-W1-S6.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: export redacts secrets by value, not only key name (F-03); import refuses foreign tenants.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
