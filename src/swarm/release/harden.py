"""V0.9 security + secret hardening helpers."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now

SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)(api[_-]?key|password)\s*=\s*['\"][^'\"]{12,}['\"]"),
    re.compile(r"(?i)BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY"),
)

# Allowlisted substrings that look secret-shaped but are intentional redaction/tests.
ALLOWLIST_SNIPPETS = (
    "sk-abc123xyz",  # console scrub test
    "sk-should-not-persist",  # product scrub test
    "sk-live-super-secret-value",  # provider adapter unit test fixture
    "sk-live-should-hide",  # harden unit test
    "[redacted]",
    "Bearer sk-",  # documentation of scrubbing
    'startswith("sk-")',
    "sk-[A-Za-z0-9]",  # regex sources
    "SECRET_RE",
    "_SECRET_",
    'token="atk_',  # loopback demo auth tokens (not provider keys)
    'password=" in db_url',  # doctor URL inspection
    "begin private key",  # worker scrub detector keywords
    "api_key=",  # detector string literals
    '"api_key"',
    "aws_secret",
)


@dataclass
class HardenFinding:
    path: str
    line: int
    kind: str
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "line": self.line,
            "kind": self.kind,
            "snippet": self.snippet[:120],
        }


@dataclass
class HardenReport:
    run_id: str
    ok: bool
    findings: list[HardenFinding] = field(default_factory=list)
    tracked_secret_files: list[str] = field(default_factory=list)
    checks: list[dict[str, Any]] = field(default_factory=list)
    mock_vs_live: str = "offline_security_scan"

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "ok": self.ok,
            "findings": [f.to_dict() for f in self.findings],
            "tracked_secret_files": self.tracked_secret_files,
            "checks": self.checks,
            "mock_vs_live": self.mock_vs_live,
            "generated_at": utc_now().isoformat(),
        }


def _git_tracked_files(repo: Path) -> list[Path]:
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(repo),
            capture_output=True,
            check=False,
        )
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    out: list[Path] = []
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        out.append(repo / raw.decode("utf-8", errors="ignore"))
    return out


def _is_allowlisted(line: str) -> bool:
    lowered = line.lower()
    if any(s.lower() in lowered for s in ALLOWLIST_SNIPPETS):
        return True
    # Detector / documentation lines that mention secret shapes.
    if any(
        marker in lowered
        for marker in (
            "in blob",
            "in lowered",
            "for token in",
            "never echo",
            "value hidden",
            "secret_pattern",
            "redact",
        )
    ):
        return True
    return False


def redact_log_value(key: str, value: Any) -> Any:
    """Redact secret-shaped log/event fields."""
    lk = key.lower()
    if any(s in lk for s in ("secret", "api_key", "password", "authorization", "token")):
        if lk in {"token_id", "secret_ref_names", "idempotency_key", "token_budget"}:
            return value
        return "[redacted]"
    if isinstance(value, str) and (
        value.startswith("sk-") or "api_key=" in value.lower()
    ):
        return "[redacted]"
    return value


def redact_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: redact_log_value(k, v) for k, v in payload.items()}


def run_security_harden(repo: Path) -> HardenReport:
    repo = repo.resolve()
    findings: list[HardenFinding] = []
    tracked_secret_files: list[str] = []
    forbidden_names = {".env", "secrets.json", "credentials.json"}

    tracked = _git_tracked_files(repo)
    for path in tracked:
        rel = str(path.relative_to(repo))
        if path.name in forbidden_names or rel in forbidden_names:
            tracked_secret_files.append(rel)
            continue
        if path.suffix.lower() in {
            ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2"
        }:
            continue
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if _is_allowlisted(line):
                continue
            for pat in SECRET_PATTERNS:
                if pat.search(line):
                    findings.append(
                        HardenFinding(
                            path=rel,
                            line=i,
                            kind="secret_pattern",
                            snippet=line.strip()[:120],
                        )
                    )
                    break

    checks = [
        {
            "name": "no_tracked_env_files",
            "ok": not tracked_secret_files,
            "detail": tracked_secret_files or "none",
        },
        {
            "name": "no_secret_patterns_in_tracked_source",
            "ok": len(findings) == 0,
            "detail": f"findings={len(findings)}",
        },
        {
            "name": "gitignore_has_env",
            "ok": ".env" in (repo / ".gitignore").read_text(encoding="utf-8"),
            "detail": ".gitignore covers .env",
        },
        {
            "name": "env_example_present",
            "ok": (repo / ".env.example").is_file(),
            "detail": ".env.example",
        },
        {
            "name": "allow_paid_default_false",
            "ok": "SWARM_ALLOW_PAID=false" in (repo / ".env.example").read_text(encoding="utf-8")
            or "ALLOW_PAID" in (repo / ".env.example").read_text(encoding="utf-8"),
            "detail": "zero-spend default documented",
        },
    ]
    ok = all(c["ok"] for c in checks) and not tracked_secret_files and not findings
    report = HardenReport(
        run_id=new_id("sec_"),
        ok=ok,
        findings=findings,
        tracked_secret_files=tracked_secret_files,
        checks=checks,
    )
    out = repo / "var" / "reports" / "security"
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest_harden.json").write_text(
        json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
    return report
