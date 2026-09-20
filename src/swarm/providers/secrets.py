"""Secret reference helpers — never log or echo values."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretRef:
    name: str

    def present(self) -> bool:
        value = os.environ.get(self.name)
        return bool(value and value.strip())

    def resolve(self) -> str:
        value = os.environ.get(self.name)
        if not value or not value.strip():
            raise LookupError(f"missing secret ref: {self.name}")
        return value


def redact(text: str, secrets: list[str]) -> str:
    redacted = text
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "***")
    return redacted
