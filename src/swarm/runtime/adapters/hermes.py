"""Hermes optional planning-agent adapter — unavailable until installed and mediated.

Hermes is an optional initial planning agent only after a pinned build passes the
same SwarmAI contracts. Framework defaults / prompts / config are not tool
restrictions or resource limits. This package does not install Hermes and does
not authorize live inference.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
from pathlib import Path

from swarm.runtime.adapters.base import (
    AgentRuntimeAdapter,
    CapabilityStatus,
    RuntimeAvailability,
    RuntimeQualification,
    all_capabilities,
)

# Planning pin from SOURCE_AUDIT — identity only; not installed here.
PINNED_HERMES_REF = "59004a62356f3a4697ab0fe8ad5086d2b405e2a6"
PINNED_HERMES_RELEASE = "v2026.9.24"


def hermes_importable() -> bool:
    return importlib.util.find_spec("hermes_agent") is not None or (
        importlib.util.find_spec("hermes") is not None
    )


def resolve_hermes_cli() -> Path | None:
    env = (os.environ.get("SWARM_HERMES_BIN") or "").strip()
    if env:
        path = Path(env)
        return path if path.is_file() and os.access(path, os.X_OK) else None
    which = shutil.which("hermes")
    return Path(which) if which else None


class HermesRuntimeAdapter:
    """Optional Hermes planning seed — blocked until install + SwarmAI mediation."""

    runtime_id = "hermes"

    def qualify(self) -> RuntimeQualification:
        cli = resolve_hermes_cli()
        importable = hermes_importable()
        if cli is None and not importable:
            return RuntimeQualification(
                runtime_id=self.runtime_id,
                display_name="Hermes (optional planning agent)",
                availability=RuntimeAvailability.UNAVAILABLE,
                pinned_version=PINNED_HERMES_RELEASE,
                discovered_version=None,
                install_path=None,
                summary=(
                    "Hermes not installed in this environment. Native missions remain "
                    "usable without Hermes. Pinned research ref "
                    f"{PINNED_HERMES_REF} was not fetched or executed."
                ),
                capabilities=all_capabilities(
                    CapabilityStatus.UNAVAILABLE,
                    "hermes missing — capability cannot be qualified",
                ),
                blockers=[
                    "Hermes CLI/package not discovered",
                    "Hermes packaging prefers isolated process/container (Py>=3.14 constraints)",
                    "No SwarmAI-mediated Hermes planning-seed evidence",
                    "Hermes config/prompts alone do not enforce SwarmAI tool or budget limits",
                    "Live Hermes qualification not authorized (no install / no spend)",
                ],
                config_alone_enforces_swarm_contracts=False,
                kernel_mediation_proven=False,
                live_inference_authorized=False,
                notes=[
                    "Absence of Hermes must not fail native acceptance.",
                    "Adapter stop condition: do not weaken core contracts for a Hermes badge.",
                    f"Research pin: {PINNED_HERMES_REF} ({PINNED_HERMES_RELEASE}).",
                ],
            )

        # Present but still unqualified — discovery without mediation proof.
        return RuntimeQualification(
            runtime_id=self.runtime_id,
            display_name="Hermes (optional planning agent)",
            availability=RuntimeAvailability.DISCOVERED_UNQUALIFIED,
            pinned_version=PINNED_HERMES_RELEASE,
            discovered_version="present_unverified",
            install_path=str(cli) if cli else "python-import",
            summary=(
                "Hermes appears present, but SwarmAI kernel mediation is not proven. "
                "Role prompts and Hermes defaults are not tool restrictions."
            ),
            capabilities=all_capabilities(
                CapabilityStatus.UNAVAILABLE,
                (
                    "unqualified: Hermes config/prompts do not enforce SwarmAI "
                    "contracts; kernel-mediated proof missing"
                ),
            ),
            blockers=[
                "Hermes config/prompts alone do not enforce SwarmAI contracts",
                "Context compression / children / background review must be disabled or mapped",
                "No mediated fake-router proof for all Hermes inference egress",
            ],
            config_alone_enforces_swarm_contracts=False,
            kernel_mediation_proven=False,
            live_inference_authorized=False,
            notes=[
                "Discovery ≠ qualification.",
                "Do not claim performance advantage without measured comparison.",
            ],
        )


_: type[AgentRuntimeAdapter] = HermesRuntimeAdapter
