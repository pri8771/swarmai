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

    restarted = PackLifecycleService(
        CapabilityPackRegistry(require_signature=True, trusted_keys={"acme": KEY}),
        SqlPackInstallStore(factory),
    )
    restarted.check_use("pack.logs", "1.0.0", "proj_a", "read_logs")
    restarted.begin_drain("pack.logs", "1.0.0")

    fresh = SqlPackInstallStore(factory)
    inst = fresh.get("pack.logs", "1.0.0", "*")
    proj = fresh.get("pack.logs", "1.0.0", "proj_a")
    assert inst is not None and inst.state == PackLifecycleState.DRAINING
    assert proj is not None and proj.state == PackLifecycleState.DRAINING
    with pytest.raises(StaleVersionError):
        fresh.put(inst, expected_version=inst.version - 1)
