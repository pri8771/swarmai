"""CLI entrypoints for local development."""

from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(prog="swarm", description="SwarmAI local CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run the local API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    args = parser.parse_args()
    if args.command == "serve":
        uvicorn.run("swarm.api.app:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
