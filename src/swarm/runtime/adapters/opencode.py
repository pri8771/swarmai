"""OpenCode optional worker runtime adapter — discovery without false qualification.

OpenCode binary presence or vendor configuration does **not** enforce SwarmAI
contracts (permissions, budgets, succession, kernel tool mediation). Until each
required capability is proven through SwarmAI-mediated evidence, capabilities
remain unavailable and the runtime stays discovered_unqualified.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from swarm.runtime.adapters.base import (
    AgentRuntimeAdapter,
    CapabilityStatus,
    RuntimeAvailability,
    RuntimeQualification,
    all_capabilities,
)

# Discovery pin hint only — not a claim that this pin is mission-qualified.
PINNED_VERSION_HINT = "v2.0.15"
DEFAULT_SEARCH_PATHS = (
    Path.home() / ".opencode" / "bin" / "opencode",
    Path("/usr/local/bin/opencode"),
    Path("/opt/homebrew/bin/opencode"),
)


def resolve_opencode_binary(*, explicit: str | None = None) -> Path | None:
    env = (explicit or os.environ.get("SWARM_OPENCODE_BIN") or "").strip()
    if env:
        path = Path(env)
        return path if path.is_file() and os.access(path, os.X_OK) else None
    which = shutil.which("opencode")
    if which:
        return Path(which)
    for candidate in DEFAULT_SEARCH_PATHS:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def probe_opencode_version(binary: Path, *, timeout_s: float = 8.0) -> str | None:
    try:
        proc = subprocess.run(
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if not text:
        return None
    line = text.splitlines()[0].strip()
    for token in line.split():
        if token.startswith("v") and any(ch.isdigit() for ch in token):
            return token
    return line


class OpenCodeRuntimeAdapter:
    """Optional coding worker runtime — unqualified until SwarmAI mediation proven."""

    runtime_id = "opencode"

    def __init__(self, *, binary: Path | None = None) -> None:
        self._binary = binary

    def qualify(self) -> RuntimeQualification:
        binary = self._binary if self._binary is not None else resolve_opencode_binary()
        if binary is None or not binary.is_file() or not os.access(binary, os.X_OK):
            return RuntimeQualification(
                runtime_id=self.runtime_id,
                display_name="OpenCode",
                availability=RuntimeAvailability.UNAVAILABLE,
                pinned_version=PINNED_VERSION_HINT,
                discovered_version=None,
                install_path=str(binary) if binary else None,
                summary="OpenCode binary not found on PATH or known install locations.",
                capabilities=all_capabilities(
                    CapabilityStatus.UNAVAILABLE,
                    "opencode binary missing — capability cannot be qualified",
                ),
                blockers=[
                    "OpenCode executable not discovered",
                    "No SwarmAI-mediated OpenCode mission evidence",
                ],
                config_alone_enforces_swarm_contracts=False,
                kernel_mediation_proven=False,
                live_inference_authorized=False,
                notes=[
                    "Do not treat missing OpenCode as a native-path failure.",
                    "Framework config alone does not enforce SwarmAI contracts.",
                ],
            )

        version = probe_opencode_version(binary)
        version_mismatch = bool(
            version and PINNED_VERSION_HINT and version != PINNED_VERSION_HINT
        )
        blockers = [
            "OpenCode settings/config alone do not enforce SwarmAI contracts",
            "SwarmAI kernel mediation (gateway/leases/budgets/succession) not proven for OpenCode",
            "No authorized live inference / spend for OpenCode mission qualification this packet",
            "Required capability matrix remains unavailable without mediated evidence",
        ]
        if version_mismatch:
            blockers.append(
                f"discovered version {version} differs from pinned hint {PINNED_VERSION_HINT}"
            )

        return RuntimeQualification(
            runtime_id=self.runtime_id,
            display_name="OpenCode",
            availability=RuntimeAvailability.DISCOVERED_UNQUALIFIED,
            pinned_version=PINNED_VERSION_HINT,
            discovered_version=version,
            install_path=str(binary),
            summary=(
                "OpenCode binary discovered for optional worker use, but mission "
                "capabilities are NOT qualified. Vendor configuration is not SwarmAI "
                "policy enforcement."
            ),
            capabilities=all_capabilities(
                CapabilityStatus.UNAVAILABLE,
                (
                    "unqualified: OpenCode config/settings do not enforce SwarmAI "
                    "contracts; kernel-mediated proof missing"
                ),
            ),
            blockers=blockers,
            config_alone_enforces_swarm_contracts=False,
            kernel_mediation_proven=False,
            live_inference_authorized=False,
            notes=[
                "Discovery ≠ qualification.",
                "Disable nested OpenCode subagent trees until admission/budget mapping exists.",
                "Do not start OpenCode service or paid models from this qualification probe.",
            ],
        )


_: type[AgentRuntimeAdapter] = OpenCodeRuntimeAdapter
