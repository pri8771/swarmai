"""Bounded local action gateway construction for isolated mission worktrees."""

from __future__ import annotations

from pathlib import Path

from swarm.tools.adapter_registry import AdapterRegistry
from swarm.tools.adapters.local_sandbox import LocalSandboxAdapter
from swarm.tools.effects import DurableEffectRepository, InMemoryEffectStore
from swarm.tools.fences import StaticFenceProvider, StaticPolicyProvider
from swarm.tools.manifests import MANIFEST_DIR, load_manifest
from swarm.tools.v17_gateway import ConsequentialToolGateway


def local_worktree_gateway(
    root: Path,
    *,
    store: InMemoryEffectStore | DurableEffectRepository | None = None,
) -> ConsequentialToolGateway:
    """Build the R28d local-only boundary rooted at exactly one worktree."""
    registry = AdapterRegistry()
    registry.register(
        LocalSandboxAdapter(
            load_manifest(MANIFEST_DIR / "local.sandbox@1.json"), root=root
        )
    )
    return ConsequentialToolGateway(
        registry=registry,
        store=store or InMemoryEffectStore(),
        fences=StaticFenceProvider(lease_generation=1, cancellation_generation=0),
        policy=StaticPolicyProvider(
            {"fs.worktree", "proc.test"}, policy_version="v17-policy-1"
        ),
    )
