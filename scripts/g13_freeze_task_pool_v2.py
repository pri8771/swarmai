#!/usr/bin/env python3
"""G13 / ART-V13-TASK-POOL — verify or re-mint ``g13-pool-freeze-v2``.

Verification is the default and is what the lead should run:

    python scripts/g13_freeze_task_pool_v2.py --verify --stats

The ``--emit-*`` flags are the mint path for a *new* freeze version. They read
the shards on disk and rewrite the shard table, the hidden-reference id
commitment and ``SHA256SUMS`` from what they measure, so running them after the
corpus has changed will happily freeze the *new* corpus. That is what a
re-freeze is for, and it is also why they must never be used to "fix" a failing
verification.

Exit code 0 means every freeze condition passed. It does **not** mean counted
qualification may start: read ``counted_qualification_ready`` in the stats, which
the verifier computes rather than reads.

Nothing here calls a model, touches the network, or counts towards qualification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from swarm.evals.g13_sealed_reference import COMMITMENT_FILENAME
from swarm.evals.task_pool_freeze_v2 import (
    CHECKSUMS_NAME,
    FREEZE_DIR,
    SHARD_TABLE_NAME,
    canonical_corpus_records,
    render_checksums,
    render_commitment_file,
    render_shard_table,
    verify_checksums_v2,
    verify_pool_freeze_v2,
)

REPO = Path(__file__).resolve().parents[1]


def _write(target: Path, text: str) -> None:
    target.write_text(text, encoding="utf-8", newline="")
    print(f"wrote {target}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="verify or re-mint the G13 v2 pool freeze")
    parser.add_argument("--verify", action="store_true", help="verify the freeze (default)")
    parser.add_argument(
        "--emit-shard-table", action="store_true", help=f"rewrite {SHARD_TABLE_NAME}"
    )
    parser.add_argument(
        "--emit-commitment", action="store_true", help=f"rewrite {COMMITMENT_FILENAME}"
    )
    parser.add_argument("--emit-checksums", action="store_true", help=f"rewrite {CHECKSUMS_NAME}")
    parser.add_argument("--stats", action="store_true", help="print verifier statistics")
    parser.add_argument("--repo", type=Path, default=REPO, help="repository root")
    args = parser.parse_args(argv)

    root: Path = args.repo
    freeze_dir = root / FREEZE_DIR
    emitted = False

    if args.emit_shard_table:
        _write(freeze_dir / SHARD_TABLE_NAME, render_shard_table(root))
        emitted = True

    if args.emit_commitment:
        _write(
            freeze_dir / COMMITMENT_FILENAME,
            render_commitment_file(canonical_corpus_records(root)),
        )
        emitted = True

    if args.emit_checksums:
        _write(freeze_dir / CHECKSUMS_NAME, render_checksums(root))
        emitted = True

    if emitted and not (args.verify or args.stats):
        return 0

    freeze = verify_pool_freeze_v2(root)
    checksums = verify_checksums_v2(root)
    print(freeze.report())
    print(checksums.report())
    if args.stats:
        print(json.dumps(freeze.stats, indent=2, sort_keys=True))
    return 0 if freeze.ok and checksums.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
