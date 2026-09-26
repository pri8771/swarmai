# SW-W1-S5 — Capability-pack lifecycle + keyed HMAC signing (F-02)

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S5` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v23-w1-s5-pack-lifecycle` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | SW-W0-S2 |
| Handoff file | `docs/v2.3/sessions/SW-W1-S5.md` |
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
git checkout -b cursor/v23-w1-s5-pack-lifecycle origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W0-S2. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/contracts/v23.py && echo "OK src/swarm/contracts/v23.py" || echo "MISSING src/swarm/contracts/v23.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `src/swarm/capabilities/__init__.py` — modify
- `src/swarm/capabilities/signing.py` — create
- `src/swarm/capabilities/lifecycle.py` — create
- `tests/extensions/test_v23_pack_lifecycle.py` — create
- `tests/integration/db/test_v23_pack_installs_sql.py` — create
- `docs/v2.3/sessions/SW-W1-S5.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Fix finding **F-02**. Today a pack "signature" is `sha256(pack_id|version|digest|caps)` with no key, so anyone can forge it. This session adds:
1. **Keyed signatures**: HMAC-SHA256 (`hmac-sha256-v1:<hex>`) per publisher, with keys read from the environment and never stored in the repo.
2. **Lifecycle**: `installed → enabled_for_project → draining → disabled → uninstalled`, plus immediate `revoke`, persisted in memory or in `v23_pack_installs`.

**Compatibility.** Existing tests (`tests/controller/test_v18_v30_gaps.py::test_pack_signature_and_revoke`, `tests/controller/test_v23_v20.py`, `tests/portability/test_portable_protocol.py`) and `product/portable_protocol.py:81` use the legacy digest without keys. They keep working: legacy mode applies when `trusted_keys=None`. Keyed mode (production; SW-W3-S1 wires it) refuses unkeyed digests.

The code below was compiled and run against `dev + SW-W0-S2` (9 new passed, 50 existing pack/portability tests still pass, 1 PostgreSQL passed). Paste it **exactly**.

### Step 1 — `src/swarm/capabilities/signing.py` (create, exactly)
```python
"""Keyed capability-pack signatures (F-02): HMAC-SHA256 with per-publisher keys.

Keys never live in the repo. ``trusted_keys_from_env`` reads
``SWARM_PACK_TRUSTED_PUBLISHERS=pub_a,pub_b`` and ``SWARM_PACK_KEY_PUB_A=<secret>``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from collections.abc import Mapping
from typing import TYPE_CHECKING

from swarm.extensions.registry import ExtensionAuthzError

if TYPE_CHECKING:
    from swarm.capabilities import CapabilityPackManifest

SIGNATURE_SCHEME = "hmac-sha256-v1"


class PackSigningError(ExtensionAuthzError):
    pass


def canonical_material(manifest: CapabilityPackManifest) -> bytes:
    body = {
        "pack_id": manifest.pack_id,
        "version": manifest.version,
        "content_digest": manifest.content_digest,
        "publisher": manifest.publisher,
        "capability_declarations": sorted(manifest.capability_declarations),
        "procedures": sorted(manifest.procedures),
        "adapters": sorted(manifest.adapters),
        "schemas": sorted(manifest.schemas),
        "prompts": sorted(manifest.prompts),
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def is_keyed_signature(signature: str | None) -> bool:
    return bool(signature) and str(signature).startswith(SIGNATURE_SCHEME + ":")


def sign_manifest(manifest: CapabilityPackManifest, *, key: bytes) -> CapabilityPackManifest:
    if not manifest.publisher:
        raise PackSigningError("pack_publisher_required")
    if not key:
        raise PackSigningError("pack_signing_key_empty")
    digest = hmac.new(key, canonical_material(manifest), hashlib.sha256).hexdigest()
    return manifest.model_copy(update={"signature": f"{SIGNATURE_SCHEME}:{digest}"})


def verify_manifest(
    manifest: CapabilityPackManifest, *, trusted_keys: Mapping[str, bytes]
) -> None:
    if not is_keyed_signature(manifest.signature):
        raise PackSigningError("pack_signature_unkeyed")
    if not manifest.publisher or manifest.publisher not in trusted_keys:
        raise PackSigningError("pack_publisher_untrusted")
    expected = sign_manifest(manifest, key=trusted_keys[manifest.publisher]).signature
    if not hmac.compare_digest(str(manifest.signature), str(expected)):
        raise PackSigningError("pack_signature_invalid")


def _env_key_name(publisher: str) -> str:
    return "SWARM_PACK_KEY_" + re.sub(r"[^A-Za-z0-9]", "_", publisher).upper()


def trusted_keys_from_env(env: Mapping[str, str] | None = None) -> dict[str, bytes]:
    source = os.environ if env is None else env
    out: dict[str, bytes] = {}
    for raw in source.get("SWARM_PACK_TRUSTED_PUBLISHERS", "").split(","):
        publisher = raw.strip()
        if not publisher:
            continue
        key = source.get(_env_key_name(publisher), "")
        if key:
            out[publisher] = key.encode("utf-8")
    return out
```

### Step 2 — `src/swarm/capabilities/__init__.py` (replace the whole file, exactly)
```python
"""V2.3 capability packs — extend extension trust model, no new permission engine.

Two signature modes:

* **keyed** (production): ``CapabilityPackRegistry(trusted_keys=...)``. Signatures
  must be ``hmac-sha256-v1:`` from a trusted publisher (see ``signing.py``);
  unkeyed digests are refused.
* **legacy** (fixtures only, ``trusted_keys=None``): the historical unkeyed
  sha256 digest. It proves integrity, not authorship (F-02) and must not be used
  on operational paths.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from pydantic import Field

from swarm.capabilities.signing import is_keyed_signature, verify_manifest
from swarm.contracts.common import StrictModel, new_id
from swarm.extensions.registry import ExtensionAuthzError

__all__ = [
    "CapabilityPackManifest",
    "CapabilityPackRegistry",
    "ProjectPackGrant",
]


class CapabilityPackManifest(StrictModel):
    pack_id: str
    version: str
    content_digest: str
    procedures: list[str] = Field(default_factory=list)
    adapters: list[str] = Field(default_factory=list)
    schemas: list[str] = Field(default_factory=list)
    prompts: list[str] = Field(default_factory=list)
    capability_declarations: list[str] = Field(default_factory=list)
    signature: str | None = None
    revoked: bool = False
    publisher: str | None = None


class ProjectPackGrant(StrictModel):
    grant_id: str = Field(default_factory=lambda: new_id("pgr_"))
    project_id: str
    pack_id: str
    version: str
    enabled: bool = True
    granted_capabilities: list[str] = Field(default_factory=list)


def _expected_signature(manifest: CapabilityPackManifest) -> str:
    material = (
        f"{manifest.pack_id}|{manifest.version}|{manifest.content_digest}|"
        f"{','.join(sorted(manifest.capability_declarations))}"
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class CapabilityPackRegistry:
    def __init__(
        self,
        *,
        require_signature: bool = False,
        trusted_keys: Mapping[str, bytes] | None = None,
    ) -> None:
        self.require_signature = require_signature
        self.trusted_keys = dict(trusted_keys) if trusted_keys is not None else None
        self._packs: dict[tuple[str, str], CapabilityPackManifest] = {}
        self._grants: dict[tuple[str, str, str], ProjectPackGrant] = {}

    @property
    def keyed(self) -> bool:
        return self.trusted_keys is not None

    def _check_signature(self, manifest: CapabilityPackManifest) -> None:
        if not manifest.signature:
            if self.require_signature:
                raise ExtensionAuthzError("pack_signature_required")
            return
        if self.trusted_keys is not None:
            verify_manifest(manifest, trusted_keys=self.trusted_keys)
            return
        if is_keyed_signature(manifest.signature):
            raise ExtensionAuthzError("pack_keyed_signature_needs_trusted_keys")
        if manifest.signature != _expected_signature(manifest):
            raise ExtensionAuthzError("pack_signature_invalid")

    def register(self, manifest: CapabilityPackManifest) -> None:
        if manifest.revoked:
            raise ExtensionAuthzError("pack_revoked")
        self._check_signature(manifest)
        self._packs[(manifest.pack_id, manifest.version)] = manifest

    def revoke(self, pack_id: str, version: str) -> None:
        pack = self._packs.get((pack_id, version))
        if pack is None:
            raise ExtensionAuthzError("pack_missing")
        pack.revoked = True

    def verify_trust(self, pack_id: str, version: str) -> CapabilityPackManifest:
        pack = self._packs.get((pack_id, version))
        if pack is None:
            raise ExtensionAuthzError("pack_missing")
        if pack.revoked:
            raise ExtensionAuthzError("pack_revoked")
        self._check_signature(pack)
        return pack

    def grant(self, grant: ProjectPackGrant) -> ProjectPackGrant:
        pack = self.verify_trust(grant.pack_id, grant.version)
        # Cannot widen beyond declarations.
        illegal = set(grant.granted_capabilities) - set(pack.capability_declarations)
        if illegal:
            raise ExtensionAuthzError(f"capability_widen_forbidden:{sorted(illegal)}")
        self._grants[(grant.project_id, grant.pack_id, grant.version)] = grant
        return grant

    def effective(self, project_id: str, pack_id: str, version: str) -> set[str]:
        pack = self.verify_trust(pack_id, version)
        grant = self._grants.get((project_id, pack_id, version))
        if grant is None or not grant.enabled:
            raise ExtensionAuthzError("pack_not_enabled")
        return set(pack.capability_declarations) & set(grant.granted_capabilities)

    @staticmethod
    def sign(manifest: CapabilityPackManifest) -> CapabilityPackManifest:
        """Legacy unkeyed digest (fixtures only). Use signing.sign_manifest for real packs."""
        return manifest.model_copy(update={"signature": _expected_signature(manifest)})
```

### Step 3 — `src/swarm/capabilities/lifecycle.py` (create, exactly)
```python
"""Capability-pack lifecycle (ART-V23-CAPABILITY-PACKS).

    installed --enable_for_project--> (project record) enabled_for_project
    installed --begin_drain--> draining --disable--> disabled --uninstall--> uninstalled
    any --revoke--> disabled (immediately; security path)

Install-level records use ``project_id="*"``. A pack is usable by a project only
while the install record is ``installed`` and that project's record is
``enabled_for_project``; effective capabilities are declared ∩ granted, so
lifecycle never widens permissions or changes model qualification.
"""

from __future__ import annotations

import threading
from typing import Any, Protocol

from pydantic import Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from swarm.capabilities import CapabilityPackManifest, CapabilityPackRegistry, ProjectPackGrant
from swarm.contracts.common import StrictModel, new_id, utc_now
from swarm.contracts.v23 import PackLifecycleState, StaleVersionError
from swarm.db.engine import session_scope
from swarm.db.models import V23PackInstallRow
from swarm.extensions.registry import ExtensionAuthzError

INSTALL_SCOPE = "*"


class PackLifecycleError(ExtensionAuthzError):
    pass


class PackInstall(StrictModel):
    install_id: str = Field(default_factory=lambda: new_id("pki_"))
    pack_id: str
    pack_version: str
    project_id: str = INSTALL_SCOPE
    state: PackLifecycleState = PackLifecycleState.INSTALLED
    granted_capabilities: list[str] = Field(default_factory=list)
    history: list[dict[str, Any]] = Field(default_factory=list)
    version: int = 0


_INSTALL_TRANSITIONS: dict[PackLifecycleState, set[PackLifecycleState]] = {
    PackLifecycleState.INSTALLED: {PackLifecycleState.DRAINING, PackLifecycleState.DISABLED},
    PackLifecycleState.DRAINING: {PackLifecycleState.DISABLED},
    PackLifecycleState.DISABLED: {PackLifecycleState.UNINSTALLED},
    PackLifecycleState.UNINSTALLED: set(),
    PackLifecycleState.ENABLED_FOR_PROJECT: set(),
}


class PackInstallStore(Protocol):
    def get(self, pack_id: str, pack_version: str, project_id: str) -> PackInstall | None: ...

    def put(self, record: PackInstall, *, expected_version: int | None) -> PackInstall: ...

    def list(self, pack_id: str, pack_version: str) -> list[PackInstall]: ...


class InMemoryPackInstallStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._rows: dict[tuple[str, str, str], PackInstall] = {}

    def get(self, pack_id: str, pack_version: str, project_id: str) -> PackInstall | None:
        with self._lock:
            row = self._rows.get((pack_id, pack_version, project_id))
            return row.model_copy() if row else None

    def put(self, record: PackInstall, *, expected_version: int | None) -> PackInstall:
        key = (record.pack_id, record.pack_version, record.project_id)
        with self._lock:
            cur = self._rows.get(key)
            if expected_version is None:
                if cur is not None:
                    raise StaleVersionError(f"already_exists:{key}")
                version = 1
            else:
                if cur is None or cur.version != expected_version:
                    raise StaleVersionError(f"stale_version:{key}")
                version = expected_version + 1
            stored = record.model_copy(update={"version": version})
            self._rows[key] = stored
            return stored.model_copy()

    def list(self, pack_id: str, pack_version: str) -> list[PackInstall]:
        with self._lock:
            return [
                r.model_copy()
                for k, r in sorted(self._rows.items())
                if k[0] == pack_id and k[1] == pack_version
            ]


class SqlPackInstallStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    def _select(self, pack_id: str, pack_version: str, project_id: str) -> Any:
        return select(V23PackInstallRow).where(
            V23PackInstallRow.pack_id == pack_id,
            V23PackInstallRow.pack_version == pack_version,
            V23PackInstallRow.project_id == project_id,
        )

    def get(self, pack_id: str, pack_version: str, project_id: str) -> PackInstall | None:
        with session_scope(self._factory) as s:
            row = s.scalar(self._select(pack_id, pack_version, project_id))
            return PackInstall.model_validate(row.payload) if row else None

    def put(self, record: PackInstall, *, expected_version: int | None) -> PackInstall:
        with session_scope(self._factory) as s:
            row = s.scalar(
                self._select(record.pack_id, record.pack_version, record.project_id)
                .with_for_update()
            )
            if expected_version is None:
                if row is not None:
                    raise StaleVersionError(f"already_exists:{record.install_id}")
                version = 1
            else:
                if row is None or row.version != expected_version:
                    raise StaleVersionError(f"stale_version:{record.install_id}")
                version = expected_version + 1
            stored = record.model_copy(update={"version": version})
            payload = stored.model_dump(mode="json")
            if row is None:
                s.add(
                    V23PackInstallRow(
                        install_id=stored.install_id,
                        pack_id=stored.pack_id,
                        pack_version=stored.pack_version,
                        project_id=stored.project_id,
                        state=stored.state.value,
                        version=version,
                        payload=payload,
                    )
                )
            else:
                row.state = stored.state.value
                row.version = version
                row.payload = payload
            try:
                s.flush()
            except IntegrityError as exc:
                raise StaleVersionError(f"conflict:{record.install_id}") from exc
            return stored

    def list(self, pack_id: str, pack_version: str) -> list[PackInstall]:
        with session_scope(self._factory) as s:
            rows = s.scalars(
                select(V23PackInstallRow)
                .where(
                    V23PackInstallRow.pack_id == pack_id,
                    V23PackInstallRow.pack_version == pack_version,
                )
                .order_by(V23PackInstallRow.project_id)
            )
            return [PackInstall.model_validate(r.payload) for r in rows]


class PackLifecycleService:
    def __init__(
        self, registry: CapabilityPackRegistry, store: PackInstallStore | None = None
    ) -> None:
        self.registry = registry
        self.store: PackInstallStore = store or InMemoryPackInstallStore()

    def _event(self, record: PackInstall, action: str, **detail: Any) -> list[dict[str, Any]]:
        entry = {"action": action, "at": utc_now().isoformat(), **detail}
        return [*record.history, entry]

    def _install_record(self, pack_id: str, version: str) -> PackInstall:
        rec = self.store.get(pack_id, version, INSTALL_SCOPE)
        if rec is None:
            raise PackLifecycleError("pack_not_installed")
        return rec

    def _move(self, rec: PackInstall, to: PackLifecycleState, action: str) -> PackInstall:
        if to not in _INSTALL_TRANSITIONS[rec.state]:
            raise PackLifecycleError(f"pack_transition_illegal:{rec.state.value}->{to.value}")
        return self.store.put(
            rec.model_copy(update={"state": to, "history": self._event(rec, action)}),
            expected_version=rec.version,
        )

    def install(self, manifest: CapabilityPackManifest) -> PackInstall:
        self.registry.register(manifest)
        rec = PackInstall(pack_id=manifest.pack_id, pack_version=manifest.version)
        rec = rec.model_copy(update={"history": self._event(rec, "install")})
        return self.store.put(rec, expected_version=None)

    def enable_for_project(
        self, pack_id: str, version: str, project_id: str, capabilities: list[str]
    ) -> PackInstall:
        if project_id == INSTALL_SCOPE:
            raise PackLifecycleError("pack_project_id_invalid")
        inst = self._install_record(pack_id, version)
        if inst.state != PackLifecycleState.INSTALLED:
            raise PackLifecycleError(f"pack_not_enableable:{inst.state.value}")
        self.registry.grant(
            ProjectPackGrant(
                project_id=project_id,
                pack_id=pack_id,
                version=version,
                granted_capabilities=sorted(capabilities),
            )
        )
        cur = self.store.get(pack_id, version, project_id)
        base = cur or PackInstall(pack_id=pack_id, pack_version=version, project_id=project_id)
        updated = base.model_copy(
            update={
                "state": PackLifecycleState.ENABLED_FOR_PROJECT,
                "granted_capabilities": sorted(capabilities),
                "history": self._event(base, "enable", capabilities=sorted(capabilities)),
            }
        )
        return self.store.put(updated, expected_version=cur.version if cur else None)

    def check_use(self, pack_id: str, version: str, project_id: str, capability: str) -> None:
        inst = self._install_record(pack_id, version)
        if inst.state == PackLifecycleState.DRAINING:
            raise PackLifecycleError("pack_draining")
        if inst.state != PackLifecycleState.INSTALLED:
            raise PackLifecycleError(f"pack_unavailable:{inst.state.value}")
        proj = self.store.get(pack_id, version, project_id)
        if proj is None or proj.state != PackLifecycleState.ENABLED_FOR_PROJECT:
            raise PackLifecycleError("pack_not_enabled_for_project")
        if capability not in self.registry.effective(project_id, pack_id, version):
            raise PackLifecycleError(f"pack_capability_denied:{capability}")

    def _set_projects(self, pack_id: str, version: str, state: PackLifecycleState) -> None:
        for rec in self.store.list(pack_id, version):
            if rec.project_id == INSTALL_SCOPE or rec.state == state:
                continue
            self.store.put(
                rec.model_copy(
                    update={"state": state, "history": self._event(rec, f"set:{state.value}")}
                ),
                expected_version=rec.version,
            )
            if state == PackLifecycleState.DISABLED:
                self.registry._grants.pop((rec.project_id, pack_id, version), None)  # noqa: SLF001

    def begin_drain(self, pack_id: str, version: str) -> PackInstall:
        current = self._install_record(pack_id, version)
        rec = self._move(current, PackLifecycleState.DRAINING, "drain")
        self._set_projects(pack_id, version, PackLifecycleState.DRAINING)
        return rec

    def disable(self, pack_id: str, version: str) -> PackInstall:
        current = self._install_record(pack_id, version)
        rec = self._move(current, PackLifecycleState.DISABLED, "disable")
        self._set_projects(pack_id, version, PackLifecycleState.DISABLED)
        return rec

    def uninstall(self, pack_id: str, version: str) -> PackInstall:
        return self._move(
            self._install_record(pack_id, version), PackLifecycleState.UNINSTALLED, "uninstall"
        )

    def revoke(self, pack_id: str, version: str) -> PackInstall:
        self.registry.revoke(pack_id, version)
        rec = self._install_record(pack_id, version)
        if rec.state in {PackLifecycleState.INSTALLED, PackLifecycleState.DRAINING}:
            rec = self._move(rec, PackLifecycleState.DISABLED, "revoke")
        self._set_projects(pack_id, version, PackLifecycleState.DISABLED)
        return rec

    def history(self, pack_id: str, version: str) -> list[dict[str, Any]]:
        return self._install_record(pack_id, version).history
```

### Step 4 — tests (create, exactly)
`tests/extensions/test_v23_pack_lifecycle.py`:
```python
"""SW-W1-S5: keyed pack signatures (F-02) and pack lifecycle (ART acceptance item 6)."""

from __future__ import annotations

import pytest

from swarm.capabilities import CapabilityPackManifest, CapabilityPackRegistry
from swarm.capabilities.lifecycle import PackLifecycleError, PackLifecycleService
from swarm.capabilities.signing import (
    PackSigningError,
    sign_manifest,
    trusted_keys_from_env,
)
from swarm.contracts.v23 import PackLifecycleState
from swarm.extensions.registry import ExtensionAuthzError

KEY = b"test-only-key-not-a-secret"


def _manifest(**kw: object) -> CapabilityPackManifest:
    base: dict[str, object] = {
        "pack_id": "pack.logs",
        "version": "1.0.0",
        "content_digest": "sha256:abc",
        "publisher": "acme",
        "capability_declarations": ["read_logs", "summarize_logs"],
    }
    base.update(kw)
    return CapabilityPackManifest(**base)  # type: ignore[arg-type]


def _keyed_registry() -> CapabilityPackRegistry:
    return CapabilityPackRegistry(require_signature=True, trusted_keys={"acme": KEY})


def test_keyed_signature_accepts_trusted_publisher() -> None:
    reg = _keyed_registry()
    reg.register(sign_manifest(_manifest(), key=KEY))
    assert reg.verify_trust("pack.logs", "1.0.0").publisher == "acme"


def test_unkeyed_legacy_digest_refused_in_keyed_mode() -> None:
    reg = _keyed_registry()
    with pytest.raises(PackSigningError, match="pack_signature_unkeyed"):
        reg.register(CapabilityPackRegistry.sign(_manifest()))


def test_wrong_key_and_untrusted_publisher_refused() -> None:
    reg = _keyed_registry()
    with pytest.raises(PackSigningError, match="pack_signature_invalid"):
        reg.register(sign_manifest(_manifest(), key=b"attacker-key"))
    with pytest.raises(PackSigningError, match="pack_publisher_untrusted"):
        reg.register(sign_manifest(_manifest(publisher="mallory"), key=KEY))


def test_tampered_manifest_refused() -> None:
    reg = _keyed_registry()
    signed = sign_manifest(_manifest(), key=KEY)
    tampered = signed.model_copy(update={"capability_declarations": ["read_logs", "delete_logs"]})
    with pytest.raises(PackSigningError, match="pack_signature_invalid"):
        reg.register(tampered)


def test_unsigned_refused_when_required() -> None:
    with pytest.raises(ExtensionAuthzError, match="pack_signature_required"):
        _keyed_registry().register(_manifest())


def test_trusted_keys_from_env() -> None:
    env = {"SWARM_PACK_TRUSTED_PUBLISHERS": "acme, beta-co", "SWARM_PACK_KEY_ACME": "k1"}
    assert trusted_keys_from_env(env) == {"acme": b"k1"}


def test_full_lifecycle_and_isolation() -> None:
    svc = PackLifecycleService(_keyed_registry())
    svc.install(sign_manifest(_manifest(), key=KEY))
    svc.enable_for_project("pack.logs", "1.0.0", "proj_a", ["read_logs"])
    svc.check_use("pack.logs", "1.0.0", "proj_a", "read_logs")
    with pytest.raises(PackLifecycleError, match="pack_not_enabled_for_project"):
        svc.check_use("pack.logs", "1.0.0", "proj_b", "read_logs")
    with pytest.raises(PackLifecycleError, match="pack_capability_denied"):
        svc.check_use("pack.logs", "1.0.0", "proj_a", "summarize_logs")
    with pytest.raises(ExtensionAuthzError, match="capability_widen_forbidden"):
        svc.enable_for_project("pack.logs", "1.0.0", "proj_a", ["delete_logs"])

    svc.begin_drain("pack.logs", "1.0.0")
    with pytest.raises(PackLifecycleError, match="pack_draining"):
        svc.check_use("pack.logs", "1.0.0", "proj_a", "read_logs")
    with pytest.raises(PackLifecycleError, match="pack_not_enableable"):
        svc.enable_for_project("pack.logs", "1.0.0", "proj_b", ["read_logs"])

    svc.disable("pack.logs", "1.0.0")
    with pytest.raises(PackLifecycleError):
        svc.check_use("pack.logs", "1.0.0", "proj_a", "read_logs")
    final = svc.uninstall("pack.logs", "1.0.0")
    assert final.state == PackLifecycleState.UNINSTALLED
    actions = [h["action"] for h in svc.history("pack.logs", "1.0.0")]
    assert actions == ["install", "drain", "disable", "uninstall"]


def test_illegal_transition_and_revoke() -> None:
    svc = PackLifecycleService(_keyed_registry())
    svc.install(sign_manifest(_manifest(), key=KEY))
    with pytest.raises(PackLifecycleError, match="pack_transition_illegal"):
        svc.uninstall("pack.logs", "1.0.0")
    svc.enable_for_project("pack.logs", "1.0.0", "proj_a", ["read_logs"])
    rec = svc.revoke("pack.logs", "1.0.0")
    assert rec.state == PackLifecycleState.DISABLED
    with pytest.raises(PackLifecycleError):
        svc.check_use("pack.logs", "1.0.0", "proj_a", "read_logs")


def test_legacy_mode_unchanged_for_fixtures() -> None:
    reg = CapabilityPackRegistry(require_signature=True)
    reg.register(CapabilityPackRegistry.sign(_manifest()))
    with pytest.raises(ExtensionAuthzError, match="pack_keyed_signature_needs_trusted_keys"):
        CapabilityPackRegistry().register(sign_manifest(_manifest(), key=KEY))
```
`tests/integration/db/test_v23_pack_installs_sql.py`:
```python
"""SW-W1-S5: pack lifecycle persisted in v23_pack_installs survives a new service (PostgreSQL)."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from swarm.capabilities import CapabilityPackManifest, CapabilityPackRegistry
from swarm.capabilities.lifecycle import PackLifecycleService, SqlPackInstallStore
from swarm.capabilities.signing import sign_manifest
from swarm.contracts.v23 import PackLifecycleState, StaleVersionError
from swarm.db.engine import create_db_engine, make_session_factory, ping
from swarm.db.models import Base

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "SWARM_DATABASE_URL", "postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm"
)
KEY = b"test-only-key-not-a-secret"


@pytest.fixture()
def factory():
    eng = create_db_engine(DATABASE_URL)
    try:
        ping(eng)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"postgres_unavailable:{type(exc).__name__}")
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE v23_pack_installs"))
    yield make_session_factory(eng)
    eng.dispose()


def test_lifecycle_persists_across_service_instances(factory) -> None:
    manifest = sign_manifest(
        CapabilityPackManifest(
            pack_id="pack.logs",
            version="1.0.0",
            content_digest="sha256:abc",
            publisher="acme",
            capability_declarations=["read_logs"],
        ),
        key=KEY,
    )
    reg = CapabilityPackRegistry(require_signature=True, trusted_keys={"acme": KEY})
    svc = PackLifecycleService(reg, SqlPackInstallStore(factory))
    svc.install(manifest)
    svc.enable_for_project("pack.logs", "1.0.0", "proj_a", ["read_logs"])
    svc.begin_drain("pack.logs", "1.0.0")

    fresh = SqlPackInstallStore(factory)
    inst = fresh.get("pack.logs", "1.0.0", "*")
    proj = fresh.get("pack.logs", "1.0.0", "proj_a")
    assert inst is not None and inst.state == PackLifecycleState.DRAINING
    assert proj is not None and proj.state == PackLifecycleState.DRAINING
    with pytest.raises(StaleVersionError):
        fresh.put(inst, expected_version=inst.version - 1)
```

### Step 5 — run
```bash
uv run pytest tests/extensions/test_v23_pack_lifecycle.py -q            # 9 passed
uv run pytest tests/controller/test_v18_v30_gaps.py tests/controller/test_v23_v20.py tests/portability -q   # unchanged, all pass
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s5 OWNER swarm;" || true
SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s5 uv run pytest tests/integration/db/test_v23_pack_installs_sql.py -q -m integration   # 1 passed
```

### Section-5 acceptance
- [ ] Keyed mode: forged, tampered, wrong-key, untrusted-publisher and unsigned packs are refused.
- [ ] Lifecycle: enable is per project; other projects are denied; capabilities are never widened; draining blocks new use and new enables; disable and uninstall follow the transition table; revoke disables immediately.
- [ ] Legacy fixture tests pass unchanged.
- [ ] Handoff "Needs other owner": "SW-W3-S1 must build the operational registry as `CapabilityPackRegistry(require_signature=True, trusted_keys=trusted_keys_from_env())`."

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s5 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s5
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/extensions/test_v23_pack_lifecycle.py tests/controller/test_v18_v30_gaps.py tests/controller/test_v23_v20.py tests/portability -q
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
git add src/swarm/capabilities/__init__.py src/swarm/capabilities/signing.py src/swarm/capabilities/lifecycle.py tests/extensions/test_v23_pack_lifecycle.py tests/integration/db/test_v23_pack_installs_sql.py docs/v2.3/sessions/SW-W1-S5.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(v2.3): capability pack lifecycle state machine and keyed publisher signatures (F-02)" -m "Session: SW-W1-S5. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v23-w1-s5-pack-lifecycle
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v23-w1-s5-pack-lifecycle --title "[SW-W1-S5] Capability-pack lifecycle + keyed HMAC signing (F-02)" --body-file docs/v2.3/sessions/SW-W1-S5.md
git ls-remote origin refs/heads/cursor/v23-w1-s5-pack-lifecycle   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S5.md` with exactly these headings:
```markdown
# SW-W1-S5 handoff
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
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S5.md` then `git commit -m "WIP(SW-W1-S5): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v23-w1-s5-pack-lifecycle` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v23-w1-s5-pack-lifecycle?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S5
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `src/swarm/capabilities/__init__.py`, `src/swarm/capabilities/signing.py`, `src/swarm/capabilities/lifecycle.py`, `tests/extensions/test_v23_pack_lifecycle.py`, `tests/integration/db/test_v23_pack_installs_sql.py`, `docs/v2.3/sessions/SW-W1-S5.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: pack signatures are keyed (F-02); unsigned or tampered packs are refused.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
