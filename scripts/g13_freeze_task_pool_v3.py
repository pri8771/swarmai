#!/usr/bin/env python3
"""Generate and verify g13-pool-freeze-v3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarm.evals.task_pool_freeze_v3 import generate_freeze, repo_root, verify_freeze


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("generate", "verify", "stats"))
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    root = args.root or repo_root()
    if args.command == "generate":
        path = generate_freeze(root)
        print(f"generated {path}")
        result = verify_freeze(root)
        print(result.report())
        print(json.dumps(result.stats, indent=2, sort_keys=True))
        return 0 if result.ok else 1
    result = verify_freeze(root)
    print(result.report())
    print(json.dumps(result.stats, indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
