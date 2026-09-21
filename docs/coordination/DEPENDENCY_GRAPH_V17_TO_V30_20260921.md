# SwarmAI dependency graph — V1.7 through V3.0

Date: 2026-09-21
Status: PLANNING ONLY

## V1.7 remainder — hard dependencies (Fable planning pass; machine-readable in `V17_RECOVERY_PACKET_QUEUE.json`)

```
OPS-CI-01                      (none)            -> gate EXT-ACTIONS-BILLING may then be cleared
R27a -> R27b -> R27c -> R27d
                 R27c -> R27e -> R28a -> R28b -> R28c -> R29a -> R28d
R30a (none)
R30a + R29a + R28a -> R30b
R30a + R29a + R28a -> R31a ;  R31a + R27e -> R31b
R28c + R30b + R31b -> R32a
R28d + R30b + R31b + R32a -> R33a -> R33b            [CP5]
R17 -> R17a                                           [CP3]
R01 -> R02a -> R02b                                   [CP1, then lead review]
R28d -> R25a -> R25b                                  [CP4]
R17a + R28d -> R17b -> R17c
R33b + R25a + R17b -> R34a ;  R34a + R02b + R25b + R17a -> R34b   [CP6]
```

Externally gated side chains (never block the chain above): `R06 → R07 → R08`, `R09 → R10`, `R07 + R10 → R11 → R12 (24 h wall clock)`, `R18`.

Cross-version edges: `R34 → 18-00`, `R33 → 19-01`/`19-07`, `R25 → 23-10`, `R15 → V18-01`, `R05 → V30B-001`, `R07 → V30B-003`. A `split` node resolves when all of its `split_into` packets resolve.

Earliest wall-clock starts: `WC-LIVE142-24H` is gated only by operator/lead action on `EXT-G12-REMOTE-ROUTES` and `EXT-G13-*`; `WC-V20-RELIABILITY-168H` starts at `20-08b`, directly after `20-03`, with `20-04`–`20-07` running during the clock; `20-08a`, `18-00a` and `19-00` are contract freezes the lead can do today.

## Hard dependency graph

```
V1.5 durable result/effect fencing
   + V1.7 unified tool/effect boundary
                |
                v
       V1.8 SiteEpoch authority
          /          \
         v            v
 worker/result      action/effect
 epoch binding      epoch binding
         \            /
          v          v
       backup/restore/reconcile
                |
                v
           V1.9 install
                |
        +-------+--------+
        |                |
        v                v
 extension runtime   controlled selfdev
        \                /
         +------v-------+
              V2.0
       integrated candidate
                |
    +-----------+------------+
    |           |            |
    v           v            v
 security   performance   reliability
    \           |            /
     +----------v-----------+
              V2.3
  durable multi-mission scheduler
      /       |       |       \
     v        v       v        v
cap packs portability observability fleet
      \       |       |       /
       +------v-------v------+
              V3.0
     persistent objectives
              |
              v
       governed learning
         /          \
        v            v
 resource allocator self-development
        \            /
         +-----v-----+
     capability ecosystem
              |
              v
     fleet tenancy/audit
```

## Artifact-level dependencies

### V1.8
- ART-V18-SITE-EPOCH depends on durable worker/result state and effect receipts.
- ART-V18-BACKUP-RESTORE depends on SiteEpoch and deployment manifest.
- ART-V18-SPLIT-BRAIN-SAFETY depends on SiteEpoch bindings at dispatch/result/effect boundaries.
- ART-V18-OUTAGE-DRILL depends on backup/restore and split-brain safety.

### V1.9
- ART-V19-EXTENSION-CONTRACT depends on V1.7 ToolGateway/action contracts.
- ART-V19-INSTALL-UPGRADE depends on stable schema/migrations + extension boundary.
- ART-V19-EXTERNAL-INSTALLS depends on install/upgrade implementation.
- ART-V19-SELFDEV-PR-EVIDENCE depends on V1.7 action boundary + V1.9 extension/selfdev runtime.

### V2.0
- ART-V20-INTEGRATED-CANDIDATE depends on reviewed lower-version source.
- SUPPORT/INSTALL/UPGRADE/SECURITY/PERFORMANCE depend on frozen integrated candidate.
- reliability campaign depends on frozen candidate + frozen protocol.
- release review depends on all evidence and actual elapsed windows.

### V2.3
- MULTIMISSION-OPS depends on V2.0 durable mission/worker/provider/tool authority.
- CAPABILITY-PACKS depends on V1.9 extension lifecycle.
- PORTABILITY depends on V1.6 knowledge + V1.9 extensions + stable schemas.
- OBSERVABILITY depends on integrated event/receipt surfaces.
- FLEET-POLICY depends on V1.5 workers + V1.8 SiteEpoch + V2.3 scheduler.

### V3.0
- OBJECTIVE-CONTRACT depends on V2.3 scheduler/admission.
- LEARNING-GOVERNANCE depends on mature eval/evidence pipeline and accepted objective boundaries.
- RESOURCE-ALLOCATOR depends on V2.3 scheduler/fleet.
- CONTROLLED-SELFDEV depends on V1.9 selfdev + V3 learning governance.
- CAPABILITY-ECOSYSTEM depends on V2.3 capability packs + V1.9 extension trust.
- FLEET-TENANCY-AUDIT depends on V2.3 fleet/observability + V3 objective/learning receipts.

## Work that can be prepared early

Even before implementation dependencies are ready, ChatGPT can prepare:
- schemas;
- state machines;
- negative tests;
- evidence JSON formats;
- CLI/API contract sketches;
- migration ownership;
- threat-model cases;
- benchmark scenarios;
- canary/rollback rules;
- exact module ownership.

## Work that must not be faked early

Cannot be pre-produced:
- actual migration success on future schema;
- real backup/restore evidence;
- real split-brain/outage evidence;
- fresh install evidence;
- provider/account-specific evidence;
- multi-host/fleet evidence;
- elapsed reliability windows;
- canary results;
- learning benefit claims;
- real schedule wall-clock evidence.

## Earliest-start rule

A future implementation packet is dependency-ready when:
1. all contracts it consumes are frozen enough to code against;
2. required lower-layer authority semantics exist;
3. executing it will not force speculative duplicate architecture;
4. the worker can test its core invariants locally.

If live evidence is blocked but implementation is ready, implement the harness and mark live evidence pending rather than blocking unrelated code.
