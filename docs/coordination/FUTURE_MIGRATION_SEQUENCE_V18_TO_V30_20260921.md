# Migration ownership and compatibility through V3.0

Closure-sweep proposal; exact revision identifiers after V1.7 are chosen against actual heads during implementation. One integration writer, one linear chain. No historical row becomes authority merely by receiving a default.

Observed source `f2b8d5f`: `9eb193b10f4e` -> `a15lease003a0001` -> `a16know003a0001` -> `a17effect004a0001`.

| Order / owner | Durable change | Compatibility and negative proof |
|---|---|---|
| M17-02 / R27a | action_receipts: receipt_sequence distinct from attempt_number, transition_key for append idempotency; action_effects execution_generation/executor/attempt/reason/consumption metadata | Multiple reconciliation receipts per attempt; conflicting same transition key rejected; stale executor cannot finalize; previous success with no receipt stays unreconciled. |
| M18-01 / 18-02 | authority-domain/epoch state and transition receipts; all shared lease/result/effect binding columns together | Pre-epoch NULL = historical only; concurrent activation one winner; no binding defaults that authorize restored state. 18-03/04 wire columns, do not create competing heads. |
| M18-02 / 18-07 only if existing event/artifact storage cannot represent recovery | RecoveryRun state/refs; backup binaries stay outside DB/Git | Restore read-only first; partial reconcile resumable; unknown effects preserved. 18-05 is a contract/manifest packet, not a competing migration. |
| M19-01 / 19-02 | extension install + project grant + generation + transition receipt | Immutable digest/version; install != enable; grants never imported as authority. |
| V2.0 / 20-02 | No new DB required by default: CandidateManifest in existing immutable artifact store | Source SHA separate from evidence commit; new review refs append, cannot mutate candidate identity. |
| M23-01 / 23-01 | project credits, persisted round/cursor, scheduler generation/decision identity | Restart does not mint credits; only current scheduler/epoch can dispatch. |
| M23-02 / 23-04 | DispatchIntent/component refs and lifecycle | Unique live dispatch identity; no new broker/worker budget ledger; unknown components hold capacity. |
| 23-09 packs | Extension kind and existing grant/lifecycle metadata | Reuse M19-01; a separate pack authority schema is forbidden without a demonstrated gap. |
| 23-10 portability | Artifact export/import manifests; existing receipt/event metadata preferred | Fresh target IDs; imported permissions/acceptance/leases stripped; duplicate import idempotency. |
| M30-01 / V30A-001 | objective lifecycle/version, TriggerReceipt, MissionProposal/link | Unique project/objective/version/occurrence; immutable versions; mutable revoke generation; normal mission admission remains owner. |
| M30-02 / V30B-001 | learning proposal, transition/evaluation/canary refs | No held-out plaintext in worker-accessible rows; freeze digests immutable; CAS transitions; reviewer identity separate. |
| V30C allocator | Existing scheduler policy/request/receipt fields | No allocator DB or second reservation ledger. |
| V30E private trust | Existing extension/publisher/revocation metadata | Digest-pinned trust; stale grant generations denied; no public distribution claim. |

R17b-1 must check durable mission/attempt mappings against existing tables before coding; do not assert that only one V1.7 migration can ever be needed without that check. Any discovered schema gap receives a named micro-packet and predecessor revision during final Fable closure. Scope changes remain proposed until independently reviewed.

For every actual migration: clean upgrade, upgrade from supported predecessor with real representative data, failure/restart, duplicate/stale constraint tests, current application read/write, rollback/restore procedure, secret scan and exactly one Alembic head. Expand/backfill/verify before any destructive removal; destructive compatibility closure needs explicit authority. A migration after candidate freeze invalidates affected evidence per protocol; it never fabricates old receipts or elapsed history.
