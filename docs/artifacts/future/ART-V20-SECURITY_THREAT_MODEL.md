# ART-V20-SECURITY-REVIEW — integrated V2 threat model

Status: drafting
Target: V2.0
Owner: ChatGPT lead

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
- site authority/epoch.

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

## Required invariants

### Tenant/project
Authorization occurs before:
- cache/history/artifact lookup;
- worker/approval view;
- knowledge retrieval/ranking;
- export;
- tool execution.

No existence/count/routing-preference leak across projects.

### Worker
- raw durable membership credentials forbidden;
- generation/lease/cancellation/source fences;
- stale result retained but not accepted;
- worker capability claim does not expand authority;
- browser/session workers are separate trust class.

### Inference
- every operational model call governed by broker;
- auth/health/price/quota/qualification distinct;
- unknown charge => no remote admission;
- retries/accounting cannot bypass reservations.

### Tools/effects
- exact project/actor/operation/destination/payload/effect approval binding;
- durable effect idempotency/reconciliation;
- unknown external outcome is not success and not blind retry.

### Knowledge
- permission filter before ranking;
- provenance/version/tombstone;
- model-generated hypothesis not accepted fact by default;
- derived summary loses visibility when dependencies are revoked/deleted.

### Recovery
- only current site epoch accepts new consequential effects;
- backup excludes raw ephemeral credentials where possible;
- restored site begins fenced/recovery mode;
- old site cannot resume writes after new epoch.

### Extensions
- manifest validated before import;
- permission requests do not self-grant;
- incompatible version fails closed;
- disable/uninstall cannot corrupt core state.

### Self-development
- isolated workspace;
- no hidden answer/known patch;
- cannot modify approval/release/credential authority;
- cannot self-merge/release.

## Adversarial test families

- cross-project IDs/idempotency keys/knowledge queries;
- stale worker generation/lease/result;
- cancellation/result race;
- provider quota/charge uncertainty;
- approval payload/destination swap;
- lost response after external effect;
- malicious extension manifest/import;
- restored stale site writes;
- poisoned knowledge/supersession/deletion;
- selfdev privilege-expansion diff;
- support-bundle secret scan.

## V2 security artifact acceptance

Lead review must link every invariant to:
- source enforcement point;
- regression/negative test;
- live/integration evidence where necessary;
- support limitation if not supported.

No security claim from document intent alone.
