# ART-V20-SECURITY-REVIEW — integrated V2 threat model

Status: drafting
Target: V2.0
Owner: ChatGPT lead

## Purpose

Define the security invariants and independent review protocol for the V2.0 integrated candidate. This document is design/review authority only; it is not security evidence by itself. A claim is valid only when bound to exact source, an enforcement point, a negative/regression test, and live/integration evidence where the behavior crosses a process or external boundary.

## Assets

- project/mission/task data;
- provider/tool/browser credentials and secret references;
- worker membership/identity;
- approvals and consequential effect rights;
- accepted artifacts/results;
- reusable knowledge/provenance;
- provider quotas/cost budgets;
- backup/export bundles;
- extension code/config;
- site authority/epoch;
- release/install/support artifacts and their provenance.

## Trust boundaries

1. operator <-> control plane
2. control plane <-> worker host
3. control plane/worker <-> inference provider
4. mission <-> tool/integration
5. project <-> project
6. knowledge store <-> retrieval context
7. extension <-> core
8. active site <-> recovered/stale site
9. self-development workspace <-> product source/release authority
10. installer/support bundle <-> host filesystem/secrets
11. evaluation worker/model <-> sealed grader/reference material

## Required invariants

### Tenant/project
Authorization occurs before:
- cache/history/artifact lookup;
- worker/approval view;
- knowledge retrieval/ranking;
- export;
- tool execution.

No existence/count/routing-preference leak across projects. Idempotency/replay keys are scoped to the same project/actor/operation authority as the protected mutation.

### Worker
- raw durable membership credentials forbidden;
- generation/lease/cancellation/source fences;
- stale result retained but not accepted;
- worker capability claim does not expand authority;
- browser/session workers are separate trust class;
- renew/expiry/result acceptance revalidate current durable authority, not just claim-time authority.

### Inference
- every operational model call governed by broker;
- auth/health/price/quota/qualification distinct;
- unknown charge => no remote admission;
- retries/accounting cannot bypass reservations;
- fallback cannot escape project-scoped broker/accounting;
- configured provider metadata is never treated as proof of current account eligibility.

### Tools/effects
- exact project/actor/operation/destination/payload/effect approval binding;
- durable effect idempotency/reconciliation;
- unknown external outcome is not success and not blind retry;
- approval grant cannot be reused across payload/destination/actor/project changes;
- adapters cannot self-expand permissions.

### Knowledge
- permission filter before ranking;
- provenance/version/tombstone;
- model-generated hypothesis not accepted fact by default;
- derived summary loses visibility when dependencies are revoked/deleted;
- superseded records cannot silently outrank current authority.

### Evaluation
- counted held-out worker-visible inputs contain no answer/reference/grader material;
- hidden references are sealed and resolved only after response capture;
- calibration and held-out pools are contamination-checked and identity-bound;
- thresholds/protocol identities are frozen before counted evaluation;
- worker/model cannot write acceptance state or grader truth.

### Recovery
- only current site epoch accepts new consequential effects;
- backup excludes raw ephemeral credentials where possible;
- restored site begins fenced/recovery mode;
- old site cannot resume writes after new epoch;
- restore does not resurrect cancelled/superseded leases/tasks/effects.

### Extensions
- manifest validated before import;
- permission requests do not self-grant;
- incompatible version fails closed;
- disable/uninstall cannot corrupt core state;
- extension install/update cannot overwrite protected core authority surfaces without explicit supported migration path.

### Self-development
- isolated workspace;
- no hidden answer/known patch;
- cannot modify approval/release/credential authority;
- cannot self-merge/release;
- generated patch is accepted only after independent tests/review and material-diff validation.

### Install/support
- generated secret-bearing files are owner-restricted;
- support bundle has a deny-by-default secret scanner and explicit allowlist metadata;
- clean install fails closed on absent required secrets/config rather than using demo identities/data;
- upgrade/rollback preserves authority/version boundaries and cannot silently downgrade security-critical schema semantics.

## Threat matrix / required negative families

| Threat | Expected denial/fence | Evidence class |
| --- | --- | --- |
| cross-project object/idempotency lookup | authorize before lookup; indistinguishable deny | API/store regression + integration |
| stale worker generation/lease | reject renew/result; retain stale receipt | durable DB regression + restart integration |
| cancel/source/revision race | stale/cancelled result never accepted | DB race regression |
| provider unknown-cost route | admission blocked before call | broker/admission evidence |
| fallback bypass | alternate route still brokered/accounted | live-local broker evidence |
| approval payload/destination swap | grant mismatch deny | tool gateway negative |
| lost response after external effect | reconcile/unknown state, no blind duplicate | adapter integration |
| hidden-answer leakage to eval worker | verifier fails freeze | evaluation verifier negative |
| poisoned/superseded knowledge | permission/provenance/supersession fence | memory regression |
| restored stale site write | epoch fence | restore/outage drill |
| malicious extension manifest | import/install deny before activation | extension negative |
| selfdev privilege-expansion patch | policy/review deny | selfdev negative |
| secret-bearing config permissions | restrictive mode required | install/bootstrap test |
| support bundle secret leakage | bundle build fails | secret-scan regression |

## Review worksheet required for V2 candidate

For every invariant, the final review must record:
- exact candidate SHA;
- exact enforcement module/function or migration/schema boundary;
- exact negative test path + command + result;
- whether a process restart, DB integration, browser/tool, provider, or restore drill is required;
- observed evidence SHA/path when required;
- supported limitation if the feature is intentionally unsupported;
- open finding severity: blocker / high / medium / low / informational.

A finding is closed only by source/evidence review, not by worker self-report or a green unrelated CI job.

## Security acceptance protocol

1. Freeze the candidate SHA and support matrix under review.
2. Enumerate every supported authority boundary above and map it to source + tests.
3. Run targeted negatives first; preserve failures.
4. Run the broad offline/static/type/package/migration suite on the exact candidate.
5. Run DB/process/recovery/tool/inference integration evidence only where the invariant requires it.
6. Secret-scan repository artifacts, generated install config, support bundles and evidence outputs. Never print real secret values.
7. Re-review all fixes on the new exact candidate SHA; prior evidence is reusable only when the relevant source/config lineage is unchanged and the protocol permits reuse.
8. Block `ART-V20-SECURITY-REVIEW` acceptance on any unresolved blocker/high finding in a supported V2.0 path.

## Candidate packetization guidance

Routine implementation/test gaps discovered by this review should be assigned to Cursor as bounded SP1-SP3 packets. Keep Session A ownership for shared API/store/routes/schemas/CLI/migrations/runtime/recovery changes; keep Session B ownership for memory/tools/extensions/product-specific implementation. Lead retains threat classification, acceptance design and independent review.

## V2 security artifact acceptance

`ART-V20-SECURITY-REVIEW` may advance to verified only when the lead has an exact-candidate worksheet covering every supported invariant and no unresolved blocker/high finding remains. It becomes accepted only when the V2.0 milestone acceptance graph permits it; document intent alone never satisfies the artifact.
