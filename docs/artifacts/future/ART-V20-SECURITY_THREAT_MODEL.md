# ART-V20-SECURITY-REVIEW — integrated threat model

Status: drafting
Target: V2.0
Owner: ChatGPT lead

## Trust boundaries

1. Operator/user -> control plane
2. Control plane -> worker hosts
3. Control plane -> inference providers
4. Control plane -> tool/integration adapters
5. Control plane -> artifact storage
6. Control plane -> knowledge store
7. Primary site -> recovery site
8. Core -> extensions/capability packs
9. Swarm self-development -> repository/worktree/release authority

## High-priority threats

### Cross-project leakage
Paths:
- worker registry/list/heartbeat;
- knowledge retrieval/ranking;
- artifacts/history/cache;
- approvals/action receipts;
- extension state/export.

Required controls:
- project scope before lookup/ranking;
- durable ownership;
- scoped idempotency/cache keys;
- negative two-project tests.

### Stale worker / duplicate effects
- expired lease result accepted after reassignment;
- old generation heartbeat/result;
- worker acts after cancellation;
- external outcome unknown then blindly retried.

Controls:
- durable lease/source/cancel generations;
- acceptance fence;
- effect key/idempotency;
- reconciliation state;
- at-most-one accepted Swarm effect receipt.

### Provider spend/route bypass
- direct model call bypasses broker;
- unknown price treated free;
- free route auto-falls back paid;
- stale quota evidence.

Controls:
- all operational inference through broker;
- exact admitted route;
- fail-closed price/quota;
- no paid fallback;
- usage reconciliation.

### Tool approval confusion
- approved payload changed;
- destination changed;
- generic approval reused;
- expired approval;
- retry duplicates side effect.

Controls:
- ActionEnvelope hash;
- exact/constrained ApprovalGrant;
- effect key;
- revalidate immediately before execution.

### Knowledge poisoning
- hypothesis becomes accepted fact;
- stale fact dominates newer source;
- deleted item remains in vector/summary cache;
- cross-project nearest-neighbor leakage.

Controls:
- knowledge classes/state;
- provenance/version;
- supersession/tombstones;
- permission-before-ranking;
- retrieval receipts.

### Recovery split brain
- old site and restored site both writable;
- stale site accepts worker/tool result.

Controls:
- site epoch authority;
- recovery mode read-only;
- epoch bound to acceptance/effect path.

### Malicious/buggy extension
- claims capabilities/permissions;
- imports incompatible code;
- hides network/filesystem use.

Controls:
- explicit manifest/compatibility;
- operator enable;
- permissions independent of manifest claim;
- isolate failure;
- extension cannot self-qualify.

### Self-development privilege escalation
- selfdev changes policy/evaluators;
- modifies hidden answers;
- self-merges/releases;
- accesses credentials.

Controls:
- isolated workspace;
- path/policy validation;
- independent reviewer;
- no release authority;
- protected evaluator/credential paths.

## V2 security evidence set

- two-project security suite;
- worker stale/cancel/race suite;
- broker bypass negative;
- tool approval mutation/duplicate suite;
- knowledge leak/deletion suite;
- stale recovery epoch suite;
- incompatible/malicious extension suite;
- selfdev privilege-expansion rejection.

Security review is not accepted until these tests run on the integrated candidate.
