"""Offline release-candidate verification — truthful labeling only."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now

REQUIRED_DOCS = (
    "README.md",
    "docs/handoff/CURRENT.md",
    "docs/runbooks/DEPLOYMENT.md",
    "docs/reviews/P20_INDEPENDENT_REVIEW.md",
    "docs/release/RELEASE_CANDIDATE.md",
    "docs/operator/START.md",
    ".env.example",
)

FORBIDDEN_TRACKED = (
    ".env",
    "secrets.json",
    "credentials.json",
)


@dataclass
class VerifyItem:
    item_id: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"item_id": self.item_id, "ok": self.ok, "detail": self.detail}


@dataclass
class ReleaseVerifyReport:
    run_id: str
    label: str
    items: list[VerifyItem] = field(default_factory=list)
    matrix: dict[str, str] = field(default_factory=dict)
    mock_vs_live: str = "offline_release_candidate"
    passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "label": self.label,
            "passed": self.passed,
            "items": [i.to_dict() for i in self.items],
            "matrix": self.matrix,
            "mock_vs_live": self.mock_vs_live,
            "generated_at": utc_now().isoformat(),
            "note": (
                "offline-verified release candidate — not cloud-operating; "
                "live accounts still required for P15/P16 qualification claims"
            ),
        }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def verify_release(repo_root: Path | None = None) -> ReleaseVerifyReport:
    root = repo_root or _repo_root()
    items: list[VerifyItem] = []

    for rel in REQUIRED_DOCS:
        path = root / rel
        items.append(
            VerifyItem(
                f"doc:{rel}",
                path.is_file(),
                "present" if path.is_file() else "missing",
            )
        )

    # No secrets in tree as tracked files (best-effort path existence check).
    for name in FORBIDDEN_TRACKED:
        path = root / name
        items.append(
            VerifyItem(
                f"secret_absent:{name}",
                not path.exists(),
                "absent" if not path.exists() else "FOUND_DO_NOT_SHIP",
            )
        )

    # Manifest + lock
    items.append(
        VerifyItem(
            "uv_lock",
            (root / "uv.lock").is_file(),
            "pinned dependencies present",
        )
    )
    items.append(
        VerifyItem(
            "release_manifest",
            (root / "release" / "manifest.json").is_file(),
            "release/manifest.json",
        )
    )

    # Deploy recovery sample
    backup = root / "deploy" / "backup" / "sample-backup-manifest.json"
    items.append(
        VerifyItem("recovery_sample", backup.is_file(), str(backup.relative_to(root)))
    )

    # Console exists for operator UI path
    console = root / "apps" / "console" / "package.json"
    items.append(VerifyItem("console_app", console.is_file(), "apps/console"))

    # Honest status matrix (not fake connected)
    matrix = {
        "implemented": "P01-P21 offline modules",
        "offline_tested": "yes",
        "live_tested": "no",
        "qualified": "no — mock profiles only",
        "deployed": "no — local artifacts only",
        "unverified": "provider live canaries, multi-route qualification, cloud host",
    }
    # Ensure we never claim connected without evidence file.
    connected_claim = root / "var" / "FAKE_CONNECTED"
    items.append(
        VerifyItem(
            "no_fake_connected_status",
            not connected_claim.exists(),
            "no FAKE_CONNECTED marker",
        )
    )

    passed = all(i.ok for i in items)
    label = (
        "offline-verified-release-candidate"
        if passed
        else "release-verify-failed"
    )
    return ReleaseVerifyReport(
        run_id=new_id("rel_"),
        label=label,
        items=items,
        matrix=matrix,
        passed=passed,
    )


def write_verify_report(report: ReleaseVerifyReport, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{report.run_id}.json"
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n")
    return path
