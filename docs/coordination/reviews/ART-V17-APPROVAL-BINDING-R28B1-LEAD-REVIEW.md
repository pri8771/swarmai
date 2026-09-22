# ART-V17-APPROVAL-BINDING — R28b-1 independent lead review

Date: 2026-09-22
Reviewer: ChatGPT engineering/product lead / formal acceptance authority
Decision: **BOUNDED SLICE ACCEPTED — R28b-1 (native rules 1–3)**
Reviewed exact source: `codex/swarm-r28b1-classification-20260922@2ebaa5a0cd64b2de665202c5cf9db0dd4f0a1510`
Tree: `9081b2b799c05435facd9ff29baae71e69226f54`
Base: accepted R28a `b204fda738221787325ce8fd0b8db58e6e29b573`
PR: #22
Parent artifact: `ART-V17-APPROVAL-BINDING` remains **drafting**
Live/checkpoint acceptance: **NOT GRANTED**

## Exact-SHA verdict

The released R28b-1 slice correctly closes the three caller-controlled authority/classification gaps assigned in native R28b rules 1–3.

### Declared operations

`OperationDecl` is part of the adapter contract and the three current adapters declare their supported operations. The gateway resolves the requested operation before authorization/admission and rejects an absent declaration with `operation_not_declared`.

The retained red-before PostgreSQL reproduction showed an undeclared operation previously reached the adapter and persisted success. The repaired negative test verifies denial before adapter action.

### Effective classification

The gateway derives effective side-effect class and risk as the maximum of the caller claim and manifest declaration. All subsequent R28a durability, policy/approval, admission and reconciliation behavior receives that effective envelope rather than the caller's weaker claim.

The memory reproducer established that `none/low` could previously bypass a consequential operation. The repaired tests cover both durability denial and real-PostgreSQL approval denial when the caller underclassifies.

New receipts persist the effective side-effect and risk values. Legacy receipt fields remain nullable, so the migration does not invent historical classification.

### Explicit fence fields

`ActionEnvelope.lease_generation` and `cancellation_generation` no longer receive valid-looking 1/0 defaults. Adapter normalizers preserve omission as `None`.

For effective consequential/irreversible operations, mission/task/attempt identity plus both generations are required before action/admission. Missing authority fails `fence_missing`.

The retained red-before PostgreSQL reproduction showed omitted mission authority could previously be normalized into invented generations and succeed. The repaired tests cover each missing field before adapter action.

## Evidence considered

Native exact-source evidence at `ef4d05be3b97de0bc4880f14b7e8597b3a851761` reports:
- **559 full tests passed, 0 skipped**;
- 16 new classification/fence contract checks;
- 50 gateway negative/failure checks;
- 22 transaction/reservation checks;
- actual PostgreSQL crash/race/replay/approval coverage retained;
- Ruff clean;
- mypy clean across 170 source files.

The evidence explicitly records and supersedes an early fake-durability diagnostic for the two authority boundaries with actual PostgreSQL reproductions.

This lead review independently inspected the exact one-commit diff, contracts, gateway implementation, native packet and new regression tests. It did not independently rerun the 559-test suite.

Hosted CI remains a separate account-start gate; no hosted-green claim is made.

## R28b-2 diagnostic

The supplemental read-only diagnostic at coordination evidence `7ae09f7` is consistent with the native rule-6 gap: at this accepted R28b-1 source, `envelope.actor` is still caller-controlled and no authenticated `ActorContext` is bound before reservation. The diagnostic stops synthetically at reservation and is not a defect in the intentionally bounded R28b-1 slice.

It is the reproduced baseline for the next released slice.

## Scope boundary

This accepts only R28b-1 rules 1–3 at exact SHA `2ebaa5a0cd64b2de665202c5cf9db0dd4f0a1510`.

It does **not**:
- accept parent `ART-V17-APPROVAL-BINDING`;
- claim R28b rules 4–6 are implemented;
- grant CP/live/product acceptance;
- change any account/host/elapsed/hosted-CI gate;
- authorize a provider/model/public action, third CP1 attempt, spend, merge, deployment, scheduler change or Fable routing.

## Scheduling decision

**R28b-2 — native rules 4–6 is RELEASED TO CODEX**, based exactly on this accepted R28b-1 SHA.

The assignment must preserve the native provider contracts and check order: FenceState/FenceProvider/LeaseFenceProvider + ActorContext/PolicyProvider; read_current_fence remains owned by db/lease_fencing; gateway binds authenticated context and current policy/scopes/fences before reservation and passes the provider's transaction reader to begin_execution.

R28c remains held pending independent exact-SHA R28b-2 review.
