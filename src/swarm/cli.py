"""CLI entrypoints for local development."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import uvicorn

from swarm.db.engine import create_db_engine, database_url, ping
from swarm.providers.catalog import list_providers
from swarm.tools.sandbox_runner import self_test as sandbox_self_test


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def cmd_serve(host: str, port: int) -> None:
    uvicorn.run("swarm.api.app:app", host=host, port=port, reload=False)


def cmd_db_migrate() -> None:
    root = _repo_root()
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=root,
        check=False,
    )
    raise SystemExit(result.returncode)


def cmd_db_validate() -> None:
    engine = create_db_engine()
    ping(engine)
    print(f"ok database={database_url().split('@')[-1]}")


def cmd_providers_list(*, mode: str) -> None:
    rows = list_providers(mode=mode)
    print(json.dumps({"mode": mode, "providers": rows}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="swarm", description="SwarmAI local CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run the local API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    db = sub.add_parser("db", help="Database operations")
    db_sub = db.add_subparsers(dest="db_command", required=True)
    db_sub.add_parser("migrate", help="Apply Alembic migrations to head")
    db_sub.add_parser("validate", help="Ping configured database")

    providers = sub.add_parser("providers", help="Provider catalog operations")
    providers_sub = providers.add_subparsers(dest="providers_command", required=True)
    plist = providers_sub.add_parser("list", help="List providers")
    plist.add_argument(
        "--mode",
        default="mock",
        choices=["mock", "live"],
        help="mock=offline catalog view; live still does not call providers here",
    )

    sandbox = sub.add_parser("sandbox", help="Sandbox operations")
    sandbox_sub = sandbox.add_subparsers(dest="sandbox_command", required=True)
    st = sandbox_sub.add_parser("self-test", help="Run sandbox self-test")
    st.add_argument("--network", default="off", choices=["off"])

    args = parser.parse_args()
    if args.command == "serve":
        cmd_serve(args.host, args.port)
    elif args.command == "db" and args.db_command == "migrate":
        cmd_db_migrate()
    elif args.command == "db" and args.db_command == "validate":
        cmd_db_validate()
    elif args.command == "providers" and args.providers_command == "list":
        cmd_providers_list(mode=args.mode)
    elif args.command == "sandbox" and args.sandbox_command == "self-test":
        print(json.dumps(sandbox_self_test(network=args.network), indent=2))


if __name__ == "__main__":
    main()
