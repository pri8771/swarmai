"""Configurable process roles — server, worker, or combined.

Deploy *profiles* describe topology (compose/DB binds). Process *roles* describe
what a single process starts: control-plane only, worker connector only, or both.
"""

from __future__ import annotations

import os
from typing import Literal

ProcessRole = Literal["server", "worker", "combined"]

PROCESS_ROLES: tuple[ProcessRole, ...] = ("server", "worker", "combined")

# Profiles that may host each process role (mac_connector kept as labelled example).
_ROLE_PROFILE_COMPAT: dict[ProcessRole, frozenset[str]] = {
    "server": frozenset({"mock", "standalone", "hybrid", "recovery", "server", "combined"}),
    "worker": frozenset({"worker", "mac_connector", "combined", "standalone", "hybrid"}),
    "combined": frozenset({"combined", "standalone", "hybrid", "mock"}),
}


class RoleConfigError(ValueError):
    """Invalid process role or incompatible profile pairing."""


def normalize_process_role(raw: str | None) -> ProcessRole:
    """Map env/config aliases onto the three portable roles."""
    if raw is None or not str(raw).strip():
        return "combined"
    value = str(raw).strip().lower().replace("-", "_")
    aliases: dict[str, ProcessRole] = {
        "server": "server",
        "control": "server",
        "control_plane": "server",
        "api": "server",
        "worker": "worker",
        "connector": "worker",
        "mac_connector": "worker",
        "combined": "combined",
        "all": "combined",
        "server_worker": "combined",
    }
    if value not in aliases:
        raise RoleConfigError(f"unknown_process_role:{raw}")
    return aliases[value]


def resolve_process_role(
    *,
    explicit: str | None = None,
    environ: dict[str, str] | None = None,
) -> ProcessRole:
    """Resolve ``SWARM_PROCESS_ROLE`` (preferred) or legacy ``SWARM_ROLE``."""
    env = environ if environ is not None else dict(os.environ)
    raw = explicit
    if raw is None:
        raw = (env.get("SWARM_PROCESS_ROLE") or env.get("SWARM_ROLE") or "").strip() or None
    return normalize_process_role(raw)


def role_starts_server(role: ProcessRole) -> bool:
    return role in {"server", "combined"}


def role_starts_worker(role: ProcessRole) -> bool:
    return role in {"worker", "combined"}


def validate_role_profile(*, role: ProcessRole, profile: str) -> None:
    """Refuse incompatible role×profile pairs with a clear error."""
    allowed = _ROLE_PROFILE_COMPAT.get(role, frozenset())
    if profile not in allowed:
        raise RoleConfigError(f"role_profile_incompatible:{role}:{profile}")
