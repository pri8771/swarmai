# Dependency graph through V3.0

Closure revision. JSON DAGs are executable truth; generated packet catalog includes every future node/edge. `basis` is provenance, not a completion edge. Entry gates block execution; claim gates block claims. Split/remediation aggregate completion includes every child.

```mermaid
flowchart TD
  Ops[OPS-CI-01] --> Billing[Actions availability gate]
  D[R27a -> R27b -> R27c] --> Review[Independent transaction review]
  Review --> A[R27d -> R27e]
  A --> CrashReview[Independent crash review]
  CrashReview --> B[R28a -> R28b]
  CP3[R17a] --> Leased[R17b-1 -> R17b-2]
  B --> Leased
  B --> Reg[R28c -> R29a]
  B --> Sandbox[R28s isolation]
  Leased --> Wire[R28d mission effects]
  Reg --> Wire
  Sandbox --> Wire
  Leased --> Worker[R17c-1 -> R17c-2]
  Wire --> Knowledge[R25a -> R25b CP4]
  Fixture[R30a] --> HTTP[R30b and R31a -> R31b]
  Reg --> HTTP
  HTTP --> Neg[R32a]
  Wire --> CP5[R33a -> R33b CP5 local]
  Neg --> CP5
  Worker --> GH[R33c-1 typed GitHub]
  GH --> Real[R33c-2 CP5 real-world]
  CP5 --> Real
  CP5 --> CP6[R34a -> R34b claim matrix]
  Worker --> CP6
  Knowledge --> CP6
  Defect[R02a -> R02b CP1] --> CP6
  CP6 --> V18[18-00 reviewed base -> V1.8 recovery]
  V18 --> V19[V1.9 install/extensions/selfdev]
  V19 --> V20[V2.0 immutable candidate]
  V20 --> Clock[20-08b/c 168h campaign]
  V20 --> V23[V2.3 fair multi-project operations]
  V23 --> V3[V3 objectives/learning/allocator/selfdev/packs/audit]
  V3 --> CP30[V30X freeze -> real elapsed CP30 -> independent audit]
```

Mermaid is a program summary, not every implementation edge. Exact branches: `19-01` uses R28d/R27d without waiting on an unrelated external issue; `20-01` can integrate after 18-08 and installed extension/upgrade/selfdev code while 18-09/19-08 live proof remains mandatory for review. `23-09/10` also require the V2.0 checked baseline. R34b may report external-pending; it cannot award a working claim without R33c-2. All V30A nodes, including learning-version integration A007, feed CP30 directly or transitively.

Independent gated chains: R06->R07->R08 qualification, R09->R10 remote overlap, R07+R10->R11->R12 24h campaign, R18 physical host proof. Missing lower-version acceptance never disappears when later implementation advances. Reviewholds and environment gates are JSON records with evidence_refs; a bare status or assumed availability cannot satisfy them.

Run `tools/validate_plan.py --ready` for the reviewed-adoption candidate-ready V1.7 set. It checks both ordinary dependency cycles and split/remediation completion cycles. Use the generated catalog for V1.8+ contracts; do not dispatch coarse V18/V23 group aliases as executable packets.
