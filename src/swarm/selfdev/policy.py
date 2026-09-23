"""Policy gates for controlled self-development."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Paths/patterns a code-generating worker must never touch.
FORBIDDEN_DIFF_PATTERNS = (
    re.compile(r"(^|/)(\.env|secrets?|credentials?)(/|$|\.)", re.I),
    re.compile(r"(^|/)(approval|release[_-]?rights|policy)(/|$)", re.I),
    re.compile(r"(^|/)docs/release/", re.I),
    re.compile(r"(^|/)src/swarm/deploy/", re.I),
    re.compile(r"main$|master$"),
)

PRIVILEGE_EXPANSION_MARKERS = (
    "auto_merge",
    "self_approve",
    "bypass_approval",
    "grant_release",
    "read_host_secrets",
    "mount_docker_socket",
    "ALLOW_PRODUCTION_WRITE",
)


@dataclass
class PolicyVerdict:
    allowed: bool
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"allowed": self.allowed, "reasons": self.reasons}


def path_forbidden(path: str, *, extra_globs: list[str] | None = None) -> bool:
    normalized = path.replace("\\", "/")
    for pat in FORBIDDEN_DIFF_PATTERNS:
        if pat.search(normalized):
            return True
    for glob in extra_globs or []:
        # Simple substring / suffix match for pack-defined globs.
        g = glob.replace("**/", "").replace("*", "")
        if g and g.lower() in normalized.lower():
            return True
    return False


def scan_diff_for_privilege_expansion(diff_text: str) -> list[str]:
    hits = []
    lower = diff_text.lower()
    for marker in PRIVILEGE_EXPANSION_MARKERS:
        if marker.lower() in lower:
            hits.append(marker)
    return hits


def validate_worker_patch(
    *,
    changed_paths: list[str],
    diff_text: str,
    allowlisted_paths: list[str],
    forbidden_globs: list[str] | None = None,
    author_role: str,
    reviewer_role: str,
    author_id: str,
    reviewer_id: str,
) -> PolicyVerdict:
    reasons: list[str] = []
    if author_role == "operator":
        reasons.append("operator_must_not_generate_code_as_worker")
    if author_id == reviewer_id:
        reasons.append("self_approval_forbidden")
    if reviewer_role != "reviewer":
        reasons.append("reviewer_role_required")

    allow = {p.replace("\\", "/") for p in allowlisted_paths}
    for path in changed_paths:
        norm = path.replace("\\", "/")
        if norm not in allow and not any(norm.endswith(a.split("/")[-1]) for a in allow):
            # Allow basename match when worktree-relative.
            base_ok = any(Path(a).name == Path(norm).name for a in allow)
            if not base_ok:
                reasons.append(f"path_not_allowlisted:{norm}")
        if path_forbidden(norm, extra_globs=forbidden_globs):
            reasons.append(f"forbidden_path:{norm}")

    for hit in scan_diff_for_privilege_expansion(diff_text):
        reasons.append(f"privilege_expansion:{hit}")

    return PolicyVerdict(allowed=len(reasons) == 0, reasons=reasons)


def assert_cannot_self_merge(*, merged: bool, author_id: str, merger_id: str) -> PolicyVerdict:
    """V1.9/V3.0: selfdev may produce a PR candidate but never self-merge/release."""
    reasons: list[str] = []
    if merged:
        reasons.append("selfdev_merge_forbidden")
    if author_id == merger_id:
        reasons.append("author_cannot_be_merger")
    return PolicyVerdict(allowed=len(reasons) == 0, reasons=reasons)
