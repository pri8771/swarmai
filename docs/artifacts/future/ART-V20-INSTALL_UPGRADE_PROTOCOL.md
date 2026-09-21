# ART-V20-INSTALL-JOURNEY / UPGRADE-ROLLBACK protocol

Status: drafting
Target: V2.0
Owner: ChatGPT lead

This protocol defines evidence requirements. It does not itself prove a clean install, upgrade, rollback, restore time, or supported predecessor matrix.

## Evidence identity

Every counted install/upgrade/rollback campaign must bind before execution to:
- exact candidate source SHA and dependency/lock state;
- exact database schema head and migration graph;
- deployment/configuration schema version;
- supported predecessor source/schema being exercised;
- extension/capability-pack manifest versions, if any;
- broker/provider route manifest with cost/admission state;
- host/OS/runtime versions needed to reproduce the run;
- one immutable campaign ID.

Do not splice steps or elapsed measurements from incompatible candidate identities. Failed attempts remain preserved as failed evidence.

## Clean-install requirements

Start from:
- empty checkout/environment;
- no prior `var/`, database, artifacts, caches, or generated identity;
- no user credentials copied from a developer machine;
- no demo project/token/provider activity;
- no pre-existing database volume whose state could mask migration/bootstrap defects.

Steps must be scripted/documented:
1. install dependencies/build artifacts;
2. create/generate install-local identity and required local secrets;
3. configure database without a known/default password;
4. migrate a genuinely empty database to head;
5. start API + console;
6. verify health/ready;
7. observe honest empty/unconfigured state;
8. create a real local project;
9. optionally configure a permitted zero-charge local route;
10. execute one supported broker-governed local mission;
11. verify a material result, not only a success status flag;
12. restart/reopen and verify the same durable project/mission/artifact identities;
13. export a secret-safe support bundle.

Fail if missing required secrets/config cause silent mock mode, fixture seeding, admission bypass, or known-answer substitution.

## Pre-upgrade freeze

Before the first mutation, record an immutable pre-upgrade manifest containing:
- predecessor source SHA, package version, schema revision and migration head(s);
- candidate source SHA and target schema revision;
- database engine/version and deployment topology;
- project/mission/artifact counts plus stable IDs selected for post-upgrade verification;
- knowledge/provenance/tombstone state required by the supported predecessor, when present;
- installed extension/capability-pack names and versions, without secrets;
- active worker/lease/attempt counts and site epoch when those features are present;
- configuration digest produced from a secret-redacted canonical representation;
- backup artifact identifier, byte size and cryptographic digest;
- backup creation command/result and restore-test status.

The manifest must never contain credential values, browser state, tokens, private keys, or raw environment dumps.

## Quiesce and backup boundary

A counted upgrade must establish a clear write cutoff:
1. stop admitting new missions/actions;
2. drain or fence in-flight workers according to the candidate worker protocol;
3. record unresolved leases/attempts instead of silently discarding them;
4. obtain a consistent database backup after the cutoff;
5. keep the backup immutable for the campaign;
6. verify the backup can be restored into a clean target before destructive migration is relied upon.

No accepted write may be backdated across the cutoff. A stale worker result arriving after upgrade/restore must be rejected unless current generation/source/lease/site authority explicitly permits it.

## Upgrade procedure

For each predecessor declared supported by `ART-V20-SUPPORT-MATRIX`:
1. start from that real predecessor schema/data fixture produced by product behavior or a migration-specific regression fixture, never a fabricated success receipt;
2. stop/drain writes and create the frozen pre-upgrade manifest;
3. install the exact candidate code/dependencies;
4. run the real migration path to the candidate head;
5. verify migration head uniqueness/ordering and required schema invariants;
6. run integrity checks before enabling normal writes;
7. start candidate services in protected/fail-closed mode;
8. reopen the frozen project/mission/artifact identities and compare durable invariants;
9. verify permissions/provenance/tool-approval/worker authority boundaries that exist in that predecessor;
10. run one newly created post-upgrade zero-spend smoke mission through the governed broker path;
11. only then enable normal writes for the campaign.

A green fresh-install test is not upgrade evidence. Each claimed predecessor requires its own exact-path result or an explicit unsupported entry in the support matrix.

## Rollback strategy classes

### Class A — code-only rollback

Allowed only when the candidate declares and proves that the database/configuration schema remains backward-compatible with the predecessor binary. Test the exact old binary against the post-upgrade schema before claiming this class.

### Class B — migration downgrade

Allowed only for migrations explicitly documented as lossless/reversible for the exercised data shape. Run the actual downgrade and then predecessor integrity tests. Do not infer reversibility merely because an Alembic `downgrade()` function exists.

### Class C — backup restore

Default for data-changing or backward-incompatible migrations:
1. stop candidate writes;
2. restore the immutable pre-upgrade backup into a clean database target;
3. restore the compatible predecessor configuration/code;
4. verify the frozen durable IDs/counts/invariants;
5. fence candidate-era workers/leases/results and any newer site epoch;
6. start predecessor services fail-closed first;
7. run a fresh predecessor smoke operation only after integrity checks pass.

Never point an old binary at a known-incompatible newer schema as a shortcut.

## Crash/partial-failure negatives

Required negative exercises for applicable paths:
- migration fails before any schema mutation;
- migration fails after at least one schema mutation/transaction boundary;
- process termination during migration or bootstrap;
- backup file missing, corrupt, truncated, or digest-mismatched;
- restore target already contains incompatible state;
- partially migrated database attempts writable startup;
- old binary starts against unsupported newer schema;
- stale pre-upgrade worker result arrives after upgrade/restore;
- stale site epoch attempts authority after restore;
- extension/capability pack is incompatible with candidate or predecessor;
- generated config is missing or has an unsafe known default;
- support bundle includes a synthetic canary secret and must detect/redact/reject it.

The expected behavior is fail closed with a diagnosable operator error. Do not repair a negative by silently discarding user data or enabling a compatibility/mock path.

## Data-integrity checks

Before and after upgrade/rollback, compare all applicable stable invariants:
- project/mission/task/artifact identity and ownership;
- accepted-result cardinality and no duplicate accepted effects;
- worker generation/lease/attempt/result authority;
- knowledge provenance/version/supersession/tombstone relationships;
- tool approval/action receipt payload bindings;
- extension/capability configuration;
- site epoch/recovery authority;
- schema revision and migration head;
- secret-redacted configuration compatibility.

Exact row counts alone are insufficient when semantics can change. At least one representative object per supported durable subsystem must be reopened through its product-facing read path.

## Required measurements

Record, without inventing thresholds:
- backup duration and bytes;
- migration duration;
- protected-start duration;
- integrity-check duration;
- restore/rollback duration;
- final database size;
- warnings/errors and operator interventions.

These are observed measurements only until an acceptance threshold is preregistered elsewhere.

## Evidence bundle

Each campaign must preserve an immutable bundle with:
- campaign manifest and exact SHAs;
- predecessor/support-matrix entry;
- commands and exit codes;
- migration heads before/after;
- backup/restore artifact digests (not secrets);
- integrity comparison output;
- restart/reopen evidence;
- negative-test outcomes;
- fresh post-upgrade and post-rollback smoke receipts;
- support-bundle secret scan result;
- all failed attempts/retries relevant to the campaign.

Evidence must distinguish `fixture/regression`, `local-live`, and `distributed-live` modes. A fixture result cannot satisfy a live/operator journey gate.

## Acceptance boundary

`ART-V20-UPGRADE-ROLLBACK` may become reviewable only when:
- every predecessor claimed supported has an executed upgrade path on the exact candidate;
- required rollback class for each claimed predecessor is executed successfully;
- no unresolved blocker-class data-integrity, stale-authority, secret, or writable-partial-state defect remains;
- all applicable negatives fail closed;
- evidence is immutable and independently reviewable;
- support-matrix claims match the executed evidence exactly.

A candidate can remain implementation-complete while this artifact is still drafting/blocked on executable evidence. Do not promote it because a protocol exists.

## Ownership

Session A:
- database/migration/backup/startup/runtime pieces;
- worker/lease/site-epoch fencing during upgrade and restore;
- shared CLI/API/migration integration.

Session B:
- install/operator-journey modules that do not touch A-owned shared surfaces;
- extension compatibility and support-bundle behavior/tests;
- evidence helpers under B-owned paths.

ChatGPT lead:
- preregister predecessor/support claims and acceptance criteria;
- independently review source/evidence and artifact transition;
- ensure failed attempts and unsupported matrix entries remain honest.
