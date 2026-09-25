#!/usr/bin/env python3
"""Portable protocol proof runner (P4).

Modes:
  inprocess — deterministic coordinator/worker protocol (default; CI-safe)
  compose-validate — validate deploy/compose/portable-protocol.yml structure
  worker-container — entrypoint used inside the worker service (health + identity)

Does not require named R730. Docker compose twin is optional evidence.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from swarm.contracts.common import new_id  # noqa: E402
from swarm.product.portable_config import (  # noqa: E402
    PortableInstallPaths,
    PublicEndpointConfig,
    WorkerIdentitySpec,
    default_support_matrix,
)
from swarm.product.portable_protocol import PortableProtocolHarness  # noqa: E402


def _endpoint_from_env() -> PublicEndpointConfig:
    env = dict(os.environ)
    has_host = bool(env.get("SWARM_PUBLIC_HOSTNAME"))
    has_api = bool(env.get("SWARM_API_BASE_URL") or env.get("SWARM_SERVER_URL"))
    if not (has_host or has_api):
        env.setdefault("SWARM_PUBLIC_HOSTNAME", "coordinator.example.test")
        env.setdefault("SWARM_API_BASE_URL", "http://coordinator.example.test:8765")
    return PublicEndpointConfig.from_env(env)


def run_inprocess(workspace: Path) -> dict:
    endpoint = _endpoint_from_env()
    paths = PortableInstallPaths(
        install_root=str(workspace / "install"),
        workspace_root=str(workspace / "ws"),
        data_root=str(workspace / "data"),
    )
    Path(paths.install_root).mkdir(parents=True, exist_ok=True)
    Path(paths.workspace_root).mkdir(parents=True, exist_ok=True)
    harness = PortableProtocolHarness(
        endpoint=endpoint,
        install_paths=paths,
        support=default_support_matrix(),
        workspace=Path(paths.workspace_root),
    )
    worker = WorkerIdentitySpec(
        worker_id=new_id("wk_"),
        node_identity="node-portable-a",
        platform="linux",
        architecture="amd64",
        capabilities=["chat", "tools.execute"],
        verified_capabilities=["chat", "tools.execute"],
        runtimes=["native"],
        workspace_grants=[str(paths.workspace_root)],
        role="worker",
    )
    token = new_id("wt_")

    async def _run() -> dict:
        happy = await harness.run_happy_path(worker=worker, token=token)
        unsupported = await harness.run_reject_unsupported(
            worker=WorkerIdentitySpec(
                worker_id=new_id("wk_"),
                node_identity="node-bad",
                platform="windows",
                architecture="arm64",
                capabilities=["chat"],
                verified_capabilities=["chat"],
            ),
            token=new_id("wt_"),
        )
        revoked = await harness.run_revocation(
            worker=WorkerIdentitySpec(
                worker_id=new_id("wk_"),
                node_identity="node-rev",
                platform="linux",
                architecture="arm64",
                capabilities=["chat"],
                verified_capabilities=["chat"],
            ),
            token=new_id("wt_"),
        )
        isolation = await harness.run_isolation(
            worker_a=WorkerIdentitySpec(
                worker_id=new_id("wk_"),
                node_identity="node-a",
                platform="linux",
                architecture="amd64",
                capabilities=["chat"],
                verified_capabilities=["chat"],
            ),
            token_a=new_id("wt_"),
            worker_b=WorkerIdentitySpec(
                worker_id=new_id("wk_"),
                node_identity="node-b",
                platform="linux",
                architecture="amd64",
                capabilities=["chat"],
                verified_capabilities=["chat"],
            ),
            token_b=new_id("wt_"),
        )
        recovery = harness.run_recovery_persist(out_dir=workspace / "portability")
        reports = [happy, unsupported, revoked, isolation, recovery]
        return {
            "mode": "inprocess",
            "ok": all(r.ok for r in reports),
            "named_r730_required": False,
            "reports": [r.to_dict() for r in reports],
        }

    return asyncio.run(_run())


def validate_compose(repo_root: Path) -> dict:
    path = repo_root / "deploy" / "compose" / "portable-protocol.yml"
    text = path.read_text(encoding="utf-8")
    checks = {
        "file_exists": path.is_file(),
        "has_coordinator": "\n  coordinator:" in text,
        "has_worker": "\n  worker:" in text,
        "has_db": "\n  db:" in text,
        # Service / project names must stay generic (no lab-host service keys).
        "no_lab_host_service": all(
            needle not in text.lower()
            for needle in (
                "\n  r730:",
                "name: r730",
                "name: swarm-r730",
                "mac-connector",
                "mac_connector",
            )
        ),
        "db_unpublished": True,  # verified by slice below
        "loopback_publish": "127.0.0.1:" in text,
        "generic_hostname": "coordinator.example.test" in text,
    }
    # DB service must not publish host ports.
    db_idx = text.index("\n  db:")
    tail = text[db_idx:]
    end = len(tail)
    for marker in ("\nnetworks:", "\nvolumes:"):
        at = tail.find(marker)
        if at != -1:
            end = min(end, at)
    chunk = tail[:end]
    checks["db_unpublished"] = "ports:" not in chunk
    ok = all(checks.values())
    return {"mode": "compose-validate", "ok": ok, "path": str(path), "checks": checks}


def worker_container_probe() -> dict:
    """Inside worker container: prove identity env + coordinator reachability."""
    server = (
        os.environ.get("SWARM_SERVER_URL") or os.environ.get("SWARM_API_BASE_URL") or ""
    ).rstrip("/")
    hostname = os.environ.get("SWARM_PUBLIC_HOSTNAME") or ""
    role = os.environ.get("SWARM_ROLE") or ""
    detail: dict = {
        "role": role,
        "public_hostname": hostname,
        "server_url": server,
        "named_r730_required": False,
    }
    if role != "worker":
        return {"mode": "worker-container", "ok": False, "error": "role_not_worker", **detail}
    if not server:
        return {"mode": "worker-container", "ok": False, "error": "missing_server_url", **detail}
    live = f"{server}/health/live"
    try:
        with urllib.request.urlopen(live, timeout=5) as resp:  # noqa: S310 — operator URL from env
            body = resp.read().decode("utf-8", errors="replace")
            detail["health_status"] = resp.status
            detail["health_body_prefix"] = body[:200]
            ok = 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "mode": "worker-container",
            "ok": False,
            "error": f"coordinator_unreachable:{exc}",
            **detail,
        }
    return {"mode": "worker-container", "ok": ok, **detail}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SwarmAI portable protocol proof (P4)")
    parser.add_argument(
        "--mode",
        choices=("inprocess", "compose-validate", "worker-container"),
        default="inprocess",
    )
    parser.add_argument("--workspace", type=Path, default=None)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.mode == "inprocess":
        ws = args.workspace or Path(os.environ.get("TMPDIR") or "/tmp") / "swarm-portable-proof"
        ws.mkdir(parents=True, exist_ok=True)
        result = run_inprocess(ws)
    elif args.mode == "compose-validate":
        result = validate_compose(args.repo_root)
    else:
        result = worker_container_probe()

    text = json.dumps(result, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
