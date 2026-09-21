# Fable final planning closure sweep — through V3.0

Work in `pri8771/swarmai`, on **`fable/v3-planning`**. This is the final architecture/planning sweep after the user's requested closure pass. Finish an executable plan; do not start competing implementation. Cursor remains the sole implementation worker and heartbeat producer.

## Start and authority

1. Read root `CLAUDE.md`; fetch origin and inspect branch/cleanliness. Continue the current planning branch tip without force push. Do not merge it anywhere.
2. Recover relevant past memory for intent only. On `origin/coordination/swarm-control`, read SESSION_START, current heartbeat/status, active packet/queue, ARTIFACT_REGISTRY and the latest **independent** lead review. Read `reviews/FABLE_V3_PLANNING_INDEPENDENT_LEAD_REVIEW_20260921.md`; the older similarly named worker-authored review is not approval authority.
3. Verify current implementation ref from the router, actual source/history and any movement since the snapshot in `MASTER_PLAN_V17_TO_V30_20260921.md` section 0. Do not use heartbeat freshness as implementation progress.
4. Read section 0 of that master plan, `REAL_WORLD_ACCEPTANCE_POLICY.md`, the three machine-readable DAGs and packet conventions. Read additional source/contracts only for the specific audit boundary.

## Exact assignment

Close the checklist in master-plan section **0.8**. The prior sweep supplies 71 detailed future packet contracts plus V1.7 specs; improve those in place. Do not write another roadmap, duplicate backlog, third-sweep prompt or generic “future work” list.

Audit and repair, in this order:

1. **Near-term execution safety:** recomputed payload/destination binding before successful replay; authenticated actor; active lease identity/status/expiry/revision/generation; atomic one-shot approval; receipt sequence distinct from execution attempt; generation-fenced finalize; cancellation linearization; late thread/process/remote completion; unknown-outcome retry restrictions; irreversible operator rearm.
2. **Real product path:** API/CLI -> mission -> durable worker -> broker -> scoped knowledge -> action gateway -> independent results. Every operational write must use durable current authority. No memory/static fence fallback. Sandbox arbitrary test code; protect host credentials. GitHub is the narrow typed R33c adapter, not unrestricted privileged subprocess.
3. **Cross-version closure:** one scheduler and DB; externally fenced restore; migration/backfill compatibility; extension/pack permission intersections; fair-share reservation/settlement and restart; objective dedupe/normal admission; governed learning/rollback; protected selfdev; tenant-scoped audit. Fix missing concrete interfaces/ownership now.
4. **Packet executability:** inspect every future contract in the generated catalog/JSON, not just its title. Each needs artifact, executable dependencies, upstream interfaces, 1–3 owned production surfaces, exact behavior, negative cases, evidence, exit and rollback. Split overly broad packets with stable aggregate IDs; make the next ~20 especially precise. Resolve proposed paths against brownfield code. Avoid new packages/tables when existing services suffice.
5. **Claims/gates:** validate dependency completion vs audit basis; source completion vs review hold; implementation gates vs real-world/elapsed gates. Real external/physical evidence is mandatory for “working”; 24h LIVE-142 and 168h V2 reliability are actual clocks. Prepare/start campaigns at earliest protocol-valid time, keep frozen deployment unchanged while later code proceeds.
6. **End-state coverage:** every required artifact through V3.0 maps to implementation, wiring, tests, live evidence, independent review and acceptance disposition. No external dependency may be quietly waived or idle independent work. Unknown provider usage stays unknown. No held-out answer exposure.

## Stop expanding scope

Freeze safe implementation defaults for reversible architecture choices. Retain genuine environment/operator inputs as explicit gates with owner/action/evidence and blocked claims. Do not invent hardware, credentials, fencing proof, paid services, performance results, support rows, test passes or learning thresholds. If source has changed, adjust only affected contracts. This sweep should finish planning; future execution may produce narrow defect-driven amendments, not require another broad architecture pass.

Use cheap read-only helpers for indexing/consistency if available. Keep architecture/security/final synthesis with Fable. Do not spawn a second implementation worker. Keep enough capacity for validation, commits and handoff.

## Validation and delivery

Run from the planning checkout:

```sh
python3 docs/coordination/tools/validate_plan.py --render
python3 docs/coordination/tools/validate_plan.py --ready
python3 -m unittest discover -s docs/coordination/tools -p 'test_validate_plan.py' -v
git diff --check
```

Strengthen validator tests when repairing graph/gate logic. These are plan checks; do not report them as product validation. Keep catalog generated from packet JSON and human critical paths synchronized.

Record closure evidence against each master checklist item. Commit all planning/consolidation changes to `fable/v3-planning`, push normally, verify remote SHA. Do not edit Cursor's implementation branch, heartbeat/status, canonical registry acceptance or canonical coordination. Do not author your own lead review, use `lead:` commit prefixes, merge/promote, self-verify or self-accept. Prior independent approval of the baseline does not approve this new revision.

## Return only a concise handoff

- branch + exact pushed SHA;
- `PLAN_COMPLETE_REVIEW_PENDING` if checklist closed, otherwise exact unresolved architecture issue;
- materially changed contracts / validation results;
- critical path through V1.7, V2.3 and V3.0;
- first five executable packets after independent adoption;
- named external/elapsed inputs still outstanding;
- worker model/effort recommendation;
- **READY_FOR_LEAD_REVIEW**.

Do not claim SwarmAI V3 is implemented or accepted because its plan is complete.
