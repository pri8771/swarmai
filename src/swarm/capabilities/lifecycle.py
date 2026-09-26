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
