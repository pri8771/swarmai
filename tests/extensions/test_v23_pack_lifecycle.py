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
