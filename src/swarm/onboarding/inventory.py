"""Secret-reference inventory — presence only, never values."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SecretRefPresence:
    name: str
    present: bool
    # Never store or return the value.
    source: str = "env"


def env_secret_present(name: str) -> bool:
    value = os.environ.get(name)
    return bool(value and value.strip())


def inventory_secret_refs(names: list[str]) -> list[SecretRefPresence]:
    return [SecretRefPresence(name=n, present=env_secret_present(n)) for n in names]


def scrub_mapping(data: dict[str, Any]) -> dict[str, Any]:
    banned_exact = {
        "api_key",
        "secret",
        "password",
        "authorization",
        "token_value",
        "credential",
        "secret_value",
    }
    allow = {"secret_ref_names", "secret_refs", "secret_presence_is_not_auth", "secret_ref_present"}
    out: dict[str, Any] = {}
    for k, v in data.items():
        lk = k.lower()
        if lk in allow:
            out[k] = v
            continue
        if lk in banned_exact or any(
            lk.startswith(b + "_") or lk.endswith("_" + b) for b in banned_exact
        ):
            continue
        if isinstance(v, str) and (v.startswith("sk-") or "api_key=" in v.lower()):
            out[k] = "[redacted]"
        elif isinstance(v, dict):
            out[k] = scrub_mapping(v)
        else:
            out[k] = v
    return out
