"""Offline release-candidate verification — truthful labeling only."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
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

# Evidence older than this is stale and must fail (FIX-003 freshness rule).
EVIDENCE_MAX_AGE = timedelta(days=7)


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
                "packaging/presence verify — not public launch; "
                "offline/live tested only when evidence files exist; "
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


def _parse_evidence_timestamp(data: dict[str, Any]) -> datetime | None:
    raw = (
        data.get("generated_at")
        or data.get("observed_at")
        or data.get("timestamp")
        or data.get("created_at")
    )
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(float(raw), tz=UTC)
    text = str(raw).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _exit_or_result_ok(data: dict[str, Any]) -> tuple[bool, str]:
    """Require successful exit/result — status boolean alone is insufficient."""
    if "exit_code" in data:
        try:
            code = int(data["exit_code"])
        except (TypeError, ValueError):
            return False, "exit_code_unreadable"
        if code != 0:
            return False, f"exit_code_nonzero:{code}"
        return True, "exit_code_0"
    result = data.get("result")
    if isinstance(result, dict):
        rstatus = str(result.get("status") or result.get("outcome") or "").lower()
        if rstatus in {"pass", "passed", "ok", "green", "success", "succeeded"}:
            return True, f"result_status:{rstatus}"
        if rstatus:
            return False, f"result_status_not_pass:{rstatus}"
        if result.get("ok") is True or result.get("passed") is True:
            return True, "result_ok_true"
        if result.get("ok") is False or result.get("passed") is False:
            return False, "result_ok_false"
    if isinstance(result, str) and result.lower() in {
        "pass",
        "passed",
        "ok",
        "green",
        "success",
    }:
        return True, f"result:{result}"
    # No invent: missing exit/result fails (status field alone cannot bypass).
    return False, "missing_exit_or_result"


def _validate_evidence_file(
    path: Path,
    *,
    expected_kind: str,
    candidate_sha: str | None,
    now: datetime | None = None,
    max_age: timedelta = EVIDENCE_MAX_AGE,
) -> VerifyItem:
    """Strict evidence binding — presence alone is not a pass (FIX-003).

    Required:
    - candidate_sha present and exact match to tip (when tip known)
    - command inventory
    - successful exit_code or result
    - mode compatible with expected_kind
    - generated/observed timestamp within freshness window
    - status pass (cannot bypass other fields)
    """
    item_id = f"{expected_kind}_evidence"
    if not path.is_file():
        return VerifyItem(item_id, False, "missing — not a pass")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return VerifyItem(item_id, False, f"unreadable_or_invalid_json:{exc}")
    if not isinstance(data, dict):
        return VerifyItem(item_id, False, "evidence_not_object")

    # Explicit failure markers always fail.
    if data.get("stale") is True or data.get("failed") is True:
        return VerifyItem(item_id, False, "stale_or_failed_marker")

    status = str(data.get("status") or "").lower()
    if status not in {"pass", "passed", "ok", "green"}:
        return VerifyItem(item_id, False, f"status_not_pass:{status or 'missing'}")

    command = data.get("command") or data.get("commands")
    if not command:
        return VerifyItem(item_id, False, "missing_command_inventory")

    # Candidate SHA is mandatory — omitting it must fail.
    sha = data.get("candidate_sha") or data.get("git_sha") or data.get("sha")
    if not sha:
        return VerifyItem(item_id, False, "missing_candidate_sha")
    if not candidate_sha:
        return VerifyItem(item_id, False, "tip_sha_unknown_cannot_bind")
    if str(sha) != str(candidate_sha):
        return VerifyItem(
            item_id, False, f"sha_mismatch:evidence={sha} tip={candidate_sha}"
        )

    exit_ok, exit_detail = _exit_or_result_ok(data)
    if not exit_ok:
        return VerifyItem(item_id, False, exit_detail)

    mode = str(data.get("mode") or data.get("mock_vs_live") or "").strip()
    if not mode:
        return VerifyItem(item_id, False, "missing_mode")
    live_mode = "live" in mode.lower() and "offline" not in mode.lower()
    if expected_kind == "offline_ci":
        if live_mode or "live" in mode.lower():
            return VerifyItem(item_id, False, f"mode_mismatch:{mode}")
        if "offline" not in mode.lower() and "ci" not in mode.lower():
            return VerifyItem(item_id, False, f"mode_not_offline:{mode}")
    if expected_kind == "live_local":
        if "live" not in mode.lower():
            return VerifyItem(item_id, False, f"mode_not_live:{mode}")

    observed = _parse_evidence_timestamp(data)
    if observed is None:
        return VerifyItem(item_id, False, "missing_generated_at_or_observed_at")
    clock = now or utc_now()
    age = clock - observed
    if age > max_age:
        return VerifyItem(item_id, False, f"stale_evidence:age={age}")
    if age < timedelta(0) and abs(age) > timedelta(minutes=5):
        return VerifyItem(item_id, False, "evidence_timestamp_in_future")

    return VerifyItem(item_id, True, str(path.name))


def _git_head(repo: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip() or None


def verify_release(repo_root: Path | None = None) -> ReleaseVerifyReport:
    root = repo_root or _repo_root()
    items: list[VerifyItem] = []
    tracked = _git_tracked(root)
    tip_sha = _git_head(root)

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

    # Evidence files require semantic validation (status/command/mode/sha/freshness).
    ci_evidence = root / "var" / "evidence" / "offline_ci_pass.json"
    live_evidence = root / "var" / "evidence" / "live_local_pass.json"
    offline_item = _validate_evidence_file(
        ci_evidence, expected_kind="offline_ci", candidate_sha=tip_sha
    )
    live_item = _validate_evidence_file(
        live_evidence, expected_kind="live_local", candidate_sha=tip_sha
    )
    # Normalize item ids expected by existing tests.
    offline_item = VerifyItem(
        "offline_ci_evidence", offline_item.ok, offline_item.detail
    )
    live_item = VerifyItem(
        "live_local_evidence", live_item.ok, live_item.detail
    )
    items.append(offline_item)
    items.append(live_item)

    if offline_item.ok:
        offline_tested = "yes — validated offline_ci_pass.json"
    else:
        offline_tested = (
            "unknown — packaging/presence check only; "
            f"offline evidence {offline_item.detail}"
        )
    if live_item.ok:
        live_local = "yes — validated live_local_pass.json"
    else:
        live_local = f"unknown/not evidenced ({live_item.detail})"

    matrix = {
        "implemented": (
            "V0.1–V0.8 product modules (missions, routing, scale, memory, "
            "tools, selfdev, reliability, product UX)"
        ),
        "packaging_presence": "checked — docs/lockfile/compose/console paths",
        "offline_tested": offline_tested,
        "live_local_tested": live_local,
        "cloud_live_tested": "no",
        "qualified_statistical": "no — provisional profiles only",
        "deployed": "no — local artifacts only",
        "public_launch": "no",
        "candidate_sha": tip_sha or "unknown",
        "unverified": "paid cloud providers, multi-route statistical qualification, public hosting",
        "note": (
            "file presence is packaging evidence only; "
            "behavioral acceptance requires validated CI/live artifacts"
        ),
    }
    connected_claim = root / "var" / "FAKE_CONNECTED"
    items.append(
        VerifyItem(
            "no_fake_connected_status",
            not connected_claim.exists(),
            "no FAKE_CONNECTED marker",
        )
    )

    packaging_ok = all(
        i.ok
        for i in items
        if i.item_id
        not in {"offline_ci_evidence", "live_local_evidence"}
    )
    # Behavioral "passed" requires packaging AND validated offline evidence.
    passed = packaging_ok and offline_item.ok
    if passed and live_item.ok:
        label = "offline-and-live-evidence-validated"
    elif passed:
        label = "offline-evidence-validated-packaging-ok"
    elif packaging_ok:
        label = "packaging-presence-ok-offline-evidence-missing"
    else:
        label = "release-verify-failed"
    # Keep legacy label substring for tests that match "offline-evidence-present"
    if passed and "validated" in label:
        label = label.replace("validated", "present-validated")
    return ReleaseVerifyReport(
        run_id=new_id("rel_"),
        label=label,
        items=items,
        matrix=matrix,
        passed=passed,
        mock_vs_live="packaging_check_not_behavioral_proof",
    )


def write_verify_report(report: ReleaseVerifyReport, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{report.run_id}.json"
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n")
    (out_dir / "latest_verify.json").write_text(
        json.dumps(report.to_dict(), indent=2) + "\n"
    )
    return path
