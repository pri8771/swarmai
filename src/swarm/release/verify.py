"""Offline release-candidate verification — truthful labeling only."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now

REQUIRED_DOCS = (
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/handoff/CURRENT.md",
    "docs/runbooks/DEPLOYMENT.md",
    "docs/reviews/P20_INDEPENDENT_REVIEW.md",
    "docs/release/RELEASE_CANDIDATE.md",
    "docs/RELEASE_CANDIDATE_STATUS.md",
    "docs/release/KNOWN_LIMITATIONS.md",
    "docs/release/V1_RELEASE_CHECKLIST.md",
    "docs/operator/START.md",
    "docs/user/GUIDE.md",
    "docs/security/HARDENING.md",
    "docs/user/TROUBLESHOOTING.md",
    "docs/user/ZERO_SPEND.md",
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
                "offline-verified release candidate — not public launch; "
                "local .env may exist when gitignored; tracked secrets must be absent"
            ),
        }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _git_tracked(repo: Path) -> set[str]:
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return set()
    if proc.returncode != 0:
        return set()
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def verify_release(repo_root: Path | None = None) -> ReleaseVerifyReport:
    root = repo_root or _repo_root()
    items: list[VerifyItem] = []
    tracked = _git_tracked(root)

    for rel in REQUIRED_DOCS:
        path = root / rel
        items.append(
            VerifyItem(
                f"doc:{rel}",
                path.is_file(),
                "present" if path.is_file() else "missing",
            )
        )

    # Secrets must not be git-tracked (local gitignored .env is OK).
    for name in FORBIDDEN_TRACKED:
        is_tracked = name in tracked
        items.append(
            VerifyItem(
                f"secret_untracked:{name}",
                not is_tracked,
                "untracked" if not is_tracked else "TRACKED_DO_NOT_SHIP",
            )
        )

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

    backup = root / "deploy" / "backup" / "sample-backup-manifest.json"
    items.append(
        VerifyItem("recovery_sample", backup.is_file(), str(backup.relative_to(root)))
    )

    console = root / "apps" / "console" / "package.json"
    items.append(VerifyItem("console_app", console.is_file(), "apps/console"))

    for profile in ("mock", "standalone"):
        compose = root / "deploy" / "compose" / f"{profile}.yml"
        items.append(
            VerifyItem(
                f"compose:{profile}",
                compose.is_file(),
                str(compose.relative_to(root)) if compose.is_file() else "missing",
            )
        )

    matrix = {
        "implemented": "V0.1–V0.8 product modules (missions, routing, scale, memory, tools, selfdev, reliability, product UX)",
        "offline_tested": "yes",
        "live_local_tested": "partial — Ollama/provider probes + journey proofs under zero-spend",
        "cloud_live_tested": "no",
        "qualified_statistical": "no — provisional profiles only",
        "deployed": "no — local artifacts only",
        "public_launch": "no",
        "unverified": "paid cloud providers, multi-route statistical qualification, public hosting",
    }
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
    (out_dir / "latest_verify.json").write_text(
        json.dumps(report.to_dict(), indent=2) + "\n"
    )
    return path
