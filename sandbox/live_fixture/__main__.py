"""`python -m sandbox.live_fixture --port 0` — bind loopback, print one JSON line, serve."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys

import uvicorn

from sandbox.live_fixture.app import create_app


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    # Bind first so the printed port is real; uvicorn takes over the socket.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", args.port))
    sock.listen(128)
    port = sock.getsockname()[1]
    print(json.dumps({"url": f"http://127.0.0.1:{port}", "pid": os.getpid()}), flush=True)
    config = uvicorn.Config(create_app(), log_level="warning", access_log=False)
    server = uvicorn.Server(config)
    server.run(sockets=[sock])
    return 0


if __name__ == "__main__":
    sys.exit(main())
