# B-OPS-AUTO-SYNC-01 — propagate reviewed autonomous-runner repair to product lane

- Artifact: ART-OPS-AUTONOMOUS-WORKERS
- Session: Cursor B / HOST-WIN-DEV / cursor/v2-product-lane
- Story points: SP1
- Dependency: lead-reviewed Mac repair implementation 0d71520de72338b3ae38dca00258a07c134e2b2a and exact-tip 39bba630306729b64ad4679346b1eb900f44ccaf.

## Goal

Bring the product lane onto the same lint-clean/fail-closed autonomous-runner implementation before B resumes product/eval work.

## Required

1. Preserve B-owned/session/heartbeat files and Windows installer changes.
2. Import only the shared coordination-source/test/workflow deltas from:
   - 0d71520de72338b3ae38dca00258a07c134e2b2a
   - 39bba630306729b64ad4679346b1eb900f44ccaf
3. Resolve platform-specific conflicts conservatively; Windows heartbeat installer remains Windows-specific.
4. Run:
   - uv run ruff check scripts/coordination tests/coordination
   - focused tests/coordination
   - available exact-tip offline CI/baseline
5. Push exact source/evidence to cursor/v2-product-lane.
6. Do not self-accept ART-OPS-AUTONOMOUS-WORKERS; autonomous self-launch evidence is still separate.

## Boundaries

No main merge, public deploy, force push, paid fallback, runtime V15 import, or G13 task-pool duplication.
