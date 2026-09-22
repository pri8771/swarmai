# SwarmAI R27c-R1 repair — prepared, not handed off

State: **OWNER_APPROVAL_REQUIRED_FOR_FABLE_HANDOFF**. Codex authored isolated local repairs under the owner's latest instruction. These are author checks, not independent acceptance. ChatGPT remains acceptance authority; Fable remains integration owner. No third CP1 attempt, worker replacement or dispatch occurred.

- Native artifact: ART-V17-APPROVAL-BINDING / R27c-R1. R27c's existing SP3 transaction boundary is retained; no later packet is enabled. Target/ceiling remains genuinely live V1.7.
- Canonical instructions: `coordination/swarm-control@b2c788f1cd38e7940bd71967b61292ef2858e74c`, `CODEX_START.md`, `SESSION_START.md`, `EXECUTION_CONTROL.json`, `packets/R27c.md` and `reviews/ART-V17-APPROVAL-BINDING-R27C-LEAD-REVIEW.md` under `docs/coordination/`.
- Expected worker base: `cursor/v17-single-session@05fe7807db3509d68dd8a86a0616c9e8ffaa2307`, unchanged on refresh. Its separate local checkout and untracked failed attempt2 evidence were preserved.
- Local repair: `codex/swarm-r27c-repair-20260922@aa85f061afa50996c2b90732ecdb253d56c9bfcc`; clean isolated worktree, upstream unset, no push.

## Bounded repair

The lease module supplies a reader automatically wired by the consequential gateway for mission/task/attempt-linked durable actions. Mission, lease, attempt, task and worker authority are read under SHARE locks in the same admission transaction as approval consumption and execution CAS. Missing/partial/ambiguous authority, stale generation, cancellation, expiry and revocation fail closed. Stored authority bindings cannot be stripped or swapped at admission. Standalone envelopes with no mission/task/attempt context preserve their existing behavior; this is not a new operational worker-to-gateway integration or live lease-path qualification.

Each distinct grant used for an effect is consumed once and retained in the effect's existing payload ledger; the current approval binding and immutable per-attempt receipts identify the admitted grant. Returning to a previously consumed grant for the same effect does not double-consume it. Revocation/expiry still deny retry. The in-memory mirror rejects an already-executing effect before consuming a replacement grant. No schema migration or refund-on-failure was added.

Production surfaces: `src/swarm/db/lease_fencing.py`, `src/swarm/tools/{effects,v17_gateway}.py`; tests: `tests/integration/db/test_effect_{transactions,admission_fences}.py`.

## Exact-source checks

- Seven selected new regressions fail against the original `05fe780` source exported to a temporary directory; no worker checkout was reset.
- **30 focused PostgreSQL transaction/reservation/fence checks passed five consecutive runs**. Existing cross-process visibility, one-use races, immutable receipts and replay tests remain included.
- New gateway tests change durable authority after the local precheck and prove zero adapter calls/approval use. A concurrent cancellation is observed waiting on a real PostgreSQL lock until admission commits. Current authority still admits successfully.
- Replacement A→B denies B's second effect; A→B→A→B on the same proved-not-applied effect consumes each once. `not_applied` is a controlled test seam, not new real-world reconciliation authority.
- Full suite with isolated PostgreSQL, loopback fixture HTTP and installed lockfile console dependencies: **471 passed, 0 skipped**, exit 0. Ruff and mypy (169 source files) pass.

Evidence: [manifest](evidence/CODEX-REPAIR-20260922/manifest.json), [five runs and static checks](evidence/CODEX-REPAIR-20260922/swarm-final-checks.txt), [complete suite](evidence/CODEX-REPAIR-20260922/swarm-complete-checks.txt), [commands/exits](evidence/CODEX-REPAIR-20260922/swarm-final-checks.json), [source/environment](evidence/CODEX-REPAIR-20260922/swarm-repair-environment.json). PostgreSQL 16 was isolated on a Unix socket and is stopped. Fixture subprocesses ended; existing product service/heartbeat were untouched. These are engineering tests, not genuine product-path proof.

## Required review and held frontier

Original source remains **REWORK_FOUND**, matching the authorized R27c CHANGES REQUIRED. This authored candidate is **REVIEW_BLOCKED** pending independent review/ChatGPT verdict. R27d's narrow acceptance is preserved; R27e/R28a remain held. CP1 attempt2 remains failed/repair_required and must be packaged without editing or erasing the original evidence. Provider, sealed-reference, physical-host, independent-review, elapsed-time and real-world gates remain open.

After explicit owner approval only: present this exact diff/evidence to the existing Fable session and ChatGPT lead, refetch the actual worker branch, reconcile any competing edits without force/reset, get ACK, and repeat required checks on the integrated SHA. Do not merge the coordination branch's application snapshot. No new live/model/public action, spend, service or scheduler is authorized by this packet.

Existing five-minute stream was last read at 03:00:47Z; meaningful activity remained 02:08:48Z, and its attempt2 RUNNING wording conflicts with retained failed output. Publication proves the timer ran, not useful implementation progress. No takeover or replacement watcher was created.

Final remote readback: Swarm coordination advanced to `54549b7ba9a587e679653273adc2fe59b8b8f45b` (03:10:56Z), with only heartbeat/status changes since `b2c788f`. Implementation and substantive contract/review files are unchanged. All three worker bases and previously published Codex review branch tips remain unchanged; the three repair branch names are absent remotely. No new verdict, integration or repair ACK is inferred.
