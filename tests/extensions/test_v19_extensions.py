"""V1.9 extensions + install tests."""

from __future__ import annotations

import pytest

from swarm.deploy.install import InstallOrchestrator
from swarm.extensions import (
    ExtensionAuthzError,
    ExtensionLoader,
    ExtensionManifest,
    ExtensionRegistry,
    ProjectExtensionGrant,
)
from swarm.selfdev.policy import assert_cannot_self_merge


def test_extension_scope_intersection_and_bypass_blocked(tmp_path) -> None:
    reg = ExtensionRegistry()
    reg.register(
        ExtensionManifest(
            extension_id="ext.demo",
            version="1.0.0",
            content_digest="d" * 64,
            declared_capabilities=["sandbox.fs"],
            tool_operations=["write_text", "read_text"],
            provider_access=["ollama"],
        )
    )
    reg.grant(
        ProjectExtensionGrant(
            project_id="proj_a",
            extension_id="ext.demo",
            version="1.0.0",
            granted_capabilities=["sandbox.fs"],
            granted_tool_scopes=["write_text"],
            granted_provider_scopes=[],
        )
    )
    reg.assert_tool_allowed("proj_a", "ext.demo", "1.0.0", "write_text")
    with pytest.raises(ExtensionAuthzError):
        reg.assert_tool_allowed("proj_a", "ext.demo", "1.0.0", "read_text")
    # Cross-project denied.
    with pytest.raises(ExtensionAuthzError):
        reg.effective_scopes("proj_other", "ext.demo", "1.0.0")
    gw = ExtensionLoader(reg).build_gateway(
        project_id="proj_a", extension_id="ext.demo", version="1.0.0", root=tmp_path
    )
    assert gw is not None


def test_install_plans_and_support_bundle_redaction(tmp_path) -> None:
    orch = InstallOrchestrator(root=tmp_path)
    clean = orch.clean_install_plan()
    assert clean.mode == "clean"
    up = orch.upgrade_plan(from_revision="a17", to_revision="a18")
    assert up.backup_id
    rb = orch.rollback_plan(from_revision="a18", to_revision="a17")
    assert rb.mode == "rollback"
    bundle = orch.support_bundle(out_dir=tmp_path / "support")
    assert bundle.digest
    body = (tmp_path / "support" / f"support_{bundle.digest[:12]}.json").read_text()
    assert "password=" not in body.lower()


def test_selfdev_cannot_self_merge() -> None:
    bad = assert_cannot_self_merge(merged=True, author_id="a", merger_id="b")
    assert bad.allowed is False
    also = assert_cannot_self_merge(merged=False, author_id="a", merger_id="a")
    assert also.allowed is False
    ok = assert_cannot_self_merge(merged=False, author_id="a", merger_id="b")
    assert ok.allowed is True
