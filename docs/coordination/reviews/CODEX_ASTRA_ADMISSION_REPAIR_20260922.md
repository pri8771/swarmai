# R28d local admission atomicity repair — READY_FOR_LEAD_REVIEW

Exact source: **fb58a751d40f1828990d7a0d687ad30de6eb6103**, tree **4fd0b56f909c8026e4893540d587d93d5180c73b**, branch codex/swarm-r28d3-async-gateway-20260922, [draft PR27](https://github.com/pri8771/swarmai/pull/27). Source is clean and remote readback matches. This commit descends from previously rejected86f8e0c; historical failure and consumed live grant are unchanged.

Assignment: coordination/swarm-control@69d06a6e92abf856bf0496fe25ce9f813d41ef47, assignments/CODEX_R28D_ADMISSION_ATOMICITY_20260922.md. Independent recommendation is RECOMMEND_ACCEPT for this exact tree; formal lead acceptance remains pending. No whole-version or live acceptance is asserted.

## Trigger and repair

Root and independent review reproduced cancellation returning while a reserved effect's reader held old generation0; stale snapshot then admitted, wrote the local file and emitted a success receipt. The provider-owned optional admission guard now precedes all memory/DB store locks and lasts through committed admission return. RevocableFenceProvider.cancel uses the same RLock. Admission first drains/accounting as an admitted effect; cancellation first rejects without adapter/file/receipt/approval use. Guard releases before adapter pre-observation/execute/post-observation. Static/Lease guards are no-ops and durable lease authority/order is unchanged. No second unlocked fence check or shared scheduler/runtime was added.

New deterministic regressions cover both serialized winners using actual local file adapter with explicit approval, memory and owned PostgreSQL. Runtime async-bridge tests now create/drop the schema only under an explicitly supplied test database; production has no missing-schema fallback. One test double delegates the guard seam.

## Settled exact-tree verification

All settled checks froze staged tree4fd0b56 before execution; committed tree equals it exactly. Initial identity.log records the precommit HEAD intentionally; staged-tree.log and commit-readback.json bind tested contents to final source.

- Focused offline:13 passed,2 PostgreSQL skips.
- Full offline:431 passed,210 skips (database/live/UI prerequisites).
- Focused real PostgreSQL:23 passed.
- Full real PostgreSQL: **628 passed,13 skipped in28.89s**. Skips:11 live_local fixture checks explicitly disabled,2 UI checks with npm dependencies absent.
- mypy:174 source files clean. Ruff on all6 changed files clean. Full Ruff still reports one inherited I001 in unchanged src/swarm/api/store.py; no all-Ruff-green claim or unsolicited cleanup.
- Staged/working whitespace check clean; source clean after commit.
- Existing owned Unix-only PostgreSQL56421 verified as pchordia /tmp/swarm-pgcheck.QxqRvZ/data. Unique disposable DB dropped; public tables0 and database cleanup_remaining0. No server start/stop or other database alteration.
- Independent exact-tree bounded review found no unresolved blocking production issue; reviewer separately ran memory variants2pass.
- Hosted CI fails before runner steps: two source-triggered runs35759387329/35759392432, runner_id0/empty steps and payment/spending-limit annotation. CI is not green and no billing action was attempted.

## Retained causal failures and limits

Final regression copied onto a Git archive of exact86f8e0c produces1failed/1passed/2PGskipped: stale admission is the failure, not the initial harness error. Raw initial test hook typo (observe instead of observe_pre_state) and expectation correction are preserved separately. Intermediate PostgreSQL runs626passed/2failed/13skipped failed because the new test's default payload/path-derived key exceeded inherited VARCHAR192. A request-dictionary key is ignored by LocalSandboxAdapter; final test sets the normalized envelope key before approval, matching existing RepoWorker task/sequence binding. No production or schema workaround was introduced. The clean settled run is separate and does not relabel prior failed/mixed-tree runs.

Hashed evidence: ../evidence/CODEX-ASTRA-ADMISSION-20260922/ (settled, independent, red-before and failed intermediate runs). Raw log/XML whitespace is preserved; human-authored source/notes pass diff checks. Earlier adversarial finding packet remains CODEX_ASTRA_R28D_REWORK_20260922.md.

## Requested disposition and holds

Accept/rework exact fb58a751/tree4fd0b56 for released engineering scope. Explicitly disposition the inherited lint/CI infrastructure blockers. Any successor live execution needs a fresh exact-source assignment and separate owner grant; failed e9178259 evidence and consumed grant remain immutable. CP1 has no attempts remaining. No model/provider/mailbox/public/application action, live fixture service, scheduler change, spend, deploy, main merge or Fable dispatch occurred.

R30b is independent: its offline contract diagnostic is submitted at4f017c95ac472b976b564c1bd59693a941ffef1e. No R30b implementation release or live_local run is inferred from this repair. Owner wants V2.3 floor/V2.7 target; native V2.7 proposal is not accepted implementation authority.
