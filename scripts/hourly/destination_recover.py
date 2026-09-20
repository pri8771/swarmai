#!/usr/bin/env python3
"""Capture / resume protected destination URLs (sanitized; no secrets)."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

STORE = Path.home() / "Library/Application Support/SwarmAI/platform-access/destinations.json"

# Only allow resuming known HTTPS provider/dashboard hosts.
ALLOW_HOSTS = {
    "openrouter.ai",
    "console.groq.com",
    "aistudio.google.com",
    "dash.cloudflare.com",
    "huggingface.co",
    "build.nvidia.com",
    "console.mistral.ai",
    "dashboard.cohere.com",
    "console.anthropic.com",
    "platform.openai.com",
    "api.together.xyz",
    "together.ai",
    "fireworks.ai",
    "deepinfra.com",
    "replicate.com",
    "github.com",
    "cursor.com",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()  # noqa: UP017


def load() -> dict:
    if not STORE.exists():
        return {"destinations": []}
    return json.loads(STORE.read_text())


def save(data: dict) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, indent=2) + "\n")
    STORE.chmod(0o600)


def sanitize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        raise SystemExit("only https destinations allowed")
    host = (parsed.hostname or "").lower()
    if host not in ALLOW_HOSTS and not any(
        host.endswith("." + h) for h in ALLOW_HOSTS
    ):
        raise SystemExit(f"host not on allowlist: {host}")
    # Drop query/fragment that may contain signed tokens.
    return f"https://{host}{parsed.path or '/'}"


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("--platform-id", required=True)
    cap.add_argument("--url", required=True)
    cap.add_argument("--note", default="")
    res = sub.add_parser("mark-resumed")
    res.add_argument("--id", required=True)
    res.add_argument("--status", default="destination_opened")
    sub.add_parser("list")
    args = p.parse_args()
    data = load()
    if args.cmd == "capture":
        safe = sanitize_url(args.url)
        entry = {
            "id": f"dest_{int(datetime.now(timezone.utc).timestamp())}",  # noqa: UP017
            "platform_id": args.platform_id,
            "safe_url": safe,
            "note": re.sub(r"\s+", " ", args.note)[:200],
            "captured_at": utc_now(),
            "status": "captured",
        }
        data["destinations"].append(entry)
        save(data)
        print(json.dumps(entry, indent=2))
        return 0
    if args.cmd == "mark-resumed":
        for entry in data["destinations"]:
            if entry.get("id") == args.id:
                entry["status"] = args.status
                entry["resumed_at"] = utc_now()
                save(data)
                print(json.dumps(entry, indent=2))
                return 0
        raise SystemExit("destination id not found")
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
