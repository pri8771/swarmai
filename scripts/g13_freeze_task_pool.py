#!/usr/bin/env python3
"""G13 / ART-V13-TASK-POOL — regenerate or verify the frozen task pool.

Verification is the default and is what the lead should run:

    python scripts/g13_freeze_task_pool.py --verify --stats

Regeneration is only for minting a new freeze version. It rewrites the record
digest sidecar and the ``SHA256SUMS`` cover file from the pool that is on disk,
so running it after the pool has changed will happily freeze the *new* pool.
That is the point of a re-freeze, and it is also why it must never be run to
"fix" a failing verification.

Nothing here calls a model, touches the network, or counts towards
qualification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarm.evals.task_pool_freeze import (
    CHECKSUMS_NAME,
    FREEZE_DIR,
    RECORD_DIGESTS_NAME,
    load_manifest,
    manifest_path,
    render_checksums,
    render_record_digests,
    verify_checksums,
    verify_pool_freeze,
)

REPO = Path(__file__).resolve().parents[1]


def _pool_path(root: Path) -> Path:
    manifest = load_manifest(manifest_path(root))
    source = manifest["pool_source"]
    return root / str(source["path"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="verify or re-mint the G13 pool freeze")
    parser.add_argument("--verify", action="store_true", help="verify the freeze (default)")
    parser.add_argument(
        "--emit-digests", action="store_true", help="rewrite the record digest sidecar"
    )
    parser.add_argument("--emit-checksums", action="store_true", help="rewrite SHA256SUMS")
    parser.add_argument("--stats", action="store_true", help="print verifier statistics")
    parser.add_argument("--repo", type=Path, default=REPO, help="repository root")
    args = parser.parse_args(argv)

    root: Path = args.repo
    emitted = False

    if args.emit_digests:
        target = root / FREEZE_DIR / RECORD_DIGESTS_NAME
        target.write_text(render_record_digests(_pool_path(root)), encoding="utf-8", newline="")
        print(f"wrote {target}")
        emitted = True

    if args.emit_checksums:
        target = root / FREEZE_DIR / CHECKSUMS_NAME
        target.write_text(render_checksums(root), encoding="utf-8", newline="")
        print(f"wrote {target}")
        emitted = True

    if emitted and not (args.verify or args.stats):
        return 0

    freeze = verify_pool_freeze(root)
    checksums = verify_checksums(root)
    print(freeze.report())
    print(checksums.report())
    if args.stats:
        print(json.dumps(freeze.stats, indent=2, sort_keys=True))
    return 0 if freeze.ok and checksums.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
