"""V2A-H2 / ART-V15 — membership token hashing (never persist raw tokens)."""

from __future__ import annotations

import hashlib
import hmac
import secrets

_TOKEN_NAMESPACE = b"swarm.worker.membership.v1"


def hash_membership_token(token: str) -> str:
    """Return a stable hex digest for durable storage. Never reverseable to token."""
    return hmac.new(_TOKEN_NAMESPACE, token.encode("utf-8"), hashlib.sha256).hexdigest()


def new_token_id() -> str:
    """Public opaque token identifier (not the secret membership token)."""
    return f"wtok_{secrets.token_hex(12)}"


def verify_membership_token(*, token: str, token_hash: str) -> bool:
    expected = hash_membership_token(token)
    return hmac.compare_digest(expected, token_hash)
