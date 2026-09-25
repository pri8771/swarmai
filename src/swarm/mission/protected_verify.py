"""Protected verification — server recomputes checks from artifacts (V1.7).

Worker-supplied verdicts and expected overrides are never authoritative.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

from swarm.mission.acceptance import ReviewDecision, review_attempt

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


@dataclass
class ProtectedVerifyResult:
    accepted: bool
    reasons: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)
    computed: dict[str, Any] = field(default_factory=dict)
    artifact_id: str | None = None
    content_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reasons": list(self.reasons),
            "checks": dict(self.checks),
            "computed": dict(self.computed),
            "artifact_id": self.artifact_id,
            "content_hash": self.content_hash,
            "authority": "server_protected_verifier",
        }


def _extract_emails_from_bytes(data: bytes) -> list[str]:
    text = data.decode("utf-8", errors="replace")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return sorted(set(_EMAIL_RE.findall(text)))
    if isinstance(payload, dict):
        if isinstance(payload.get("emails"), list):
            return sorted({str(x) for x in payload["emails"]})
        blob = json.dumps(payload)
        return sorted(set(_EMAIL_RE.findall(blob)))
    return sorted(set(_EMAIL_RE.findall(text)))


def compute_extract_checks(
    *,
    artifact_bytes: bytes,
    content_hash: str,
    placement: str = "server_verified",
    host_role: str = "protected_verifier",
    runtime: str = "swarm_kernel",
) -> dict[str, Any]:
    emails = _extract_emails_from_bytes(artifact_bytes)
    digest = hashlib.sha256(artifact_bytes).hexdigest()
    if digest != content_hash:
        # Prefer CAS hash; still expose mismatch.
        pass
    return {
        "email_count": len(emails),
        "artifact_sha256": content_hash,
        "content_sha256": digest,
        "placement": placement,
        "host_role": host_role,
        "runtime": runtime,
        "emails": emails,
    }


def protected_review(
    *,
    task_family: str | None,
    required_checks: dict[str, Any] | None,
    artifact_id: str | None,
    artifact_bytes: bytes | None,
    content_hash: str | None,
    worker_produced: dict[str, Any] | None = None,
) -> ProtectedVerifyResult:
    """Independently verify a mission attempt.

    For extract: recompute checks from artifact bytes. Worker ``produced`` is
    ignored for acceptance decisions.
    """
    del worker_produced  # never authoritative
    family = (task_family or "").strip().lower()
    if not artifact_id or artifact_bytes is None or not content_hash:
        return ProtectedVerifyResult(
            accepted=False,
            reasons=["missing_artifact_for_protected_verify"],
            checks={"artifact_present": False},
        )
    if family in {"extract", "extraction"}:
        computed = compute_extract_checks(
            artifact_bytes=artifact_bytes, content_hash=content_hash
        )
        decision: ReviewDecision = review_attempt(
            produced={"checks": computed},
            required_checks=required_checks,
        )
        return ProtectedVerifyResult(
            accepted=decision.accepted,
            reasons=decision.reasons,
            checks=decision.checks,
            computed={k: v for k, v in computed.items() if k != "emails"},
            artifact_id=artifact_id,
            content_hash=content_hash,
        )
    # Generic families: require frozen checks and refuse worker self-grades.
    if not required_checks:
        return ProtectedVerifyResult(
            accepted=False,
            reasons=["no_independent_checks"],
            checks={"independent_review": False},
            artifact_id=artifact_id,
            content_hash=content_hash,
        )
    # Without a family-specific oracle, presence of artifact + hash bind is not enough
    # to accept — operator/tool verifiers must be registered.
    return ProtectedVerifyResult(
        accepted=False,
        reasons=[f"protected_verifier_unsupported_family:{family or 'missing'}"],
        checks={"family_supported": False},
        artifact_id=artifact_id,
        content_hash=content_hash,
    )
