# Cursor review — SwarmAI two-host MVP

Reviewed 25 September 2026. **Disposition: changes requested; local engineering prototype, release acceptance blocked.**

## Reviewed candidate and boundaries

- PR: [#44](https://github.com/pri8771/swarmai/pull/44).
- Exact source: `180eb73a4b67103b3e38f4aaa550ac444307d60a`; verified remote `dev` and `cursor/two-host-mvp-b28d` both point here.
- Remote `main`: `08b910f981eff2ab66873a71055090f2c60f2a91`, unchanged by this lane.
- Local candidate: `/Users/pchordia/Downloads/swarm-ai-two-host-mvp`, clean at review start/end.
- Review ran against an isolated archive of that commit. No source fixes, deployments, provider calls, account changes, GitHub comments, Linear mutations, or merges were performed.
- Read-only checks verified the existing Mac API and PostgreSQL containers are running. The API on `127.0.0.1:18766` reports database up, providers_network=false, and zero configured accounts/routes. Health is not mission acceptance.
- R730 deployment, actual cross-host behavior, Cloudflare/DNS, and live model operation were not independently exercised.

This review covers the latest two-host PR, its dependent execution/acceptance paths, and current tracking/version records. It is not a new audit of every historical branch. New regressions and inherited blockers are identified separately below.

## Summary

Cursor delivered useful local packaging, HTTP client code, durable blob plumbing, UI reads, runtime discovery, and an offline evaluation harness. Thirty focused tests pass independently. However, the new proofs exercise paths that still trust worker-supplied answers, keep execution state in memory, and do not perform server-dispatched autonomous work. Several artifact and evaluation defects were reproduced. These changes are a foundation for the product, not a completed distributed swarm.

## Findings, in priority order

### R1 — P1: mission acceptance can be manufactured without execution

**Inherited API defect used as the new TH-02/TH-03 acceptance path.** The review API accepts caller-supplied `required_checks`; `review_mission_attempt` prefers them over the saved plan. Acceptance compares those values with caller-supplied output fields. No artifact, leased attempt, or protected verifier execution is required.

Independent reproduction: create a mission expecting count=99; submit count=1 and override expected count=1; HTTP 200, accepted=true, mission completed, zero enrolled workers, no produced artifact. The connector itself calculates both its expected checks and result and sends them to this API. Its negative test merely changes one of those fields.

Sources: [review API](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/api/routes_v1.py#L127), [check override and completion](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/api/store.py#L574), [new connector](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/workers/mac_connector.py#L213), [new proof script](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/scripts/th03_mac_connector.py#L111).

**Required fix:** freeze verifier specifications in trusted state, bind results to actual attempt/source/artifact identities, and execute protected checks outside worker authority. Reject arbitrary worker verdicts, expected-check replacement, stale generations, and missing artifacts. Return TH-02/03 acceptance to review-required until this passes.

### R2 — P1: HTTP worker execution is not the durable distributed path

**Inherited in-memory authority remains wired into the newly packaged service.** ProductStore creates WorkerRegistryService and in-memory event/idempotency/approval stores. Missions are JSON-backed. The separate PostgreSQL proof script exercises a service directly; it does not establish that the HTTP connector uses that service.

Independent restart reproduction using the same persisted server directory: workers go from 1 to 0; the old worker's heartbeat returns 404. This was an application reconstruction test, not a live-container restart. It matches the inspected wiring.

The connector is a one-shot fixture script: it creates a project and mission, computes a local extraction result, reviews it, and exits. It has no server task polling/claim loop, task lease renewal, attempt result protocol, cancellation loop, or reconnection/reconciliation. Its Compose command runs that script once. A health endpoint surviving client exit does not prove disconnect recovery.

Sources: [ProductStore state](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/api/store.py#L50), [registry state](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/workers/registry.py#L36), [worker HTTP routes](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/api/routes_v1.py#L492), [one-shot service](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/deploy/compose/mac-connector.yml#L25).

**Required fix:** connect the production API and connector to one transactional durable authority. Add continuous scoped dispatch, lease renewal, cancellation and replay reconciliation; exercise those over HTTP. Keep fixture demonstrations explicitly separate.

### R3 — P1: artifact metadata is lost across writers and retries

**New implementation defects.** Each ArtifactStore loads a private copy of `index.json` and rewrites the whole index without locking or merging. Two instances opened before either writes lose one of two records even with sequential writes. Shared `.partial` filenames also create a same-file race.

The API's idempotency cache is process-local. Replaying an identical artifact request with the same key after restart creates a different artifact ID. Mission artifact references are keyed by `kind`, so this replaces the prior `result` reference: the old artifact URL returns 404. PostgreSQL metadata writes are best-effort and exceptions are swallowed.

Sources: [index rewrite](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/workspace/artifacts.py#L139), [mission reference replacement](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/api/store.py#L287), [best-effort metadata](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/api/store.py#L368).

**Required fix:** transactional metadata and durable idempotency; preserve immutable artifact IDs/history; unique temporary files and safe publication; explicit reconciliation for blob/database failures. Verify multi-process writes and replay after a crash.

### R4 — P1: artifact content route bypasses deletion checks

**New route defect.** The new mission content reader resolves metadata from mission JSON and reads directly by hash. It never checks ArtifactStore's deletion tombstone. Independent reproduction: call the existing store deletion API, then read the mission artifact route; it still returns HTTP 200 and content.

Source: [read by hash](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/api/store.py#L340).

**Required fix:** authorize each read against authoritative artifact state, mission association and scope; enforce deletion and retention semantics. Preserve content deduplication without bypassing reference-level access decisions.

### R5 — P1: the evaluation grader can be spoofed; execution isolation is insufficient

**Inherited grader/sandbox problems newly relied on by TH-07.** The Python grader executes submitted code in its harness process and trusts the final JSON line on stdout. Submitting `print('{"ok": true}'); raise SystemExit(0)` receives `unit_pass`, without defining a solution or running tests.

The sandbox starts a normal host subprocess with a changed working directory and sanitized environment. A reviewer-created program successfully read a reviewer-created file outside its allowed directory. No real user files were accessed. Code inspection also shows the `network=False` flag does not create OS-level network isolation. It is unsafe to expose this path to model-generated code or claim protected independent verification.

Sources: [grader](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/evals/graders.py#L114), [subprocess sandbox](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/tools/sandbox_runner.py#L61).

**Required fix:** OS-enforced disposable execution, narrow mounts and network policy; verifier-controlled verdict generation and test-count validation; worker output cannot manufacture verdicts. Keep oracle runs as harness checks, not model-quality evidence.

### R6 — P1: native runtime is admitted despite missing mandatory controls

**New qualification defect.** NativeRuntimeAdapter reports available and kernel_mediation_proven=true while cancellation, tool permissions, model accounting, X/Y succession, and nested-delegation accounting remain unproven. qualification_report derives mission admission solely from the availability enum. CAS reopen is also presented as knowledge-transfer evidence, although it proves only blob persistence.

Sources: [native declaration](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/runtime/adapters/native.py#L72), [admission list](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/runtime/adapters/qualify.py#L34).

**Required fix:** distinguish discovery, narrowly qualified fixture capability, and full mission admission. Enforce required capability evidence in actual dispatch; bind qualification to source/runtime/configuration and validity. OpenCode and Hermes are currently discovery/reporting shells, not operational worker adapters.

### R7 — P1: required CI does not pass

**New changes introduce failures.** Hosted backend CI stops at Ruff with 7 errors. Independently running mypy finds 11 errors in `mac_connector.py` and `api/store.py`. Fixing lint alone will not make CI green. Console CI succeeds. The green `live-gated` job only prints a notice that live tests were not run.

Sources: [failed backend job](https://github.com/pri8771/swarmai/actions/runs/36158994754/job/108150551703), [CI definition](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/.github/workflows/ci.yml).

**Required fix:** repair lint/type errors and run the entire required pipeline at the final SHA. Add an ephemeral PostgreSQL integration job; existing CI skips those tests when no DB is configured. Do not weaken checks or count a notice as a live pass.

### R8 — P2: evaluation qualification is incomplete and rejects zero-spend grants

**New implementation limitations/defects.** LiveGrant rejects budget_usd=0 even for a deliberately free-only route. Live dispatch remains hard-disabled even after a positive-budget approved grant. Thus missing approval is not the only blocker: execution integration is unimplemented. The suite reuses 128 existing starter cases and maps S/M/L/XL size labels to difficulty; expert-level reasoning difficulty has not been established. It does not yet exercise the full proposed collaboration, learning and succession behaviors.

The report hash cannot be reconstructed from serialized output: `generated_at` changes on each `to_dict()` call, including between hashing and writing. Independent recomputation with the digest field reset to null fails.

Sources: [zero-budget rejection](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/evals/synthetic_harness.py#L72), [unimplemented live path](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/evals/synthetic_harness.py#L382), [timestamp](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/evals/synthetic_harness.py#L177), [hash/write sequence](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/src/swarm/evals/synthetic_harness.py#L564).

**Required fix:** allow an explicitly approved zero-dollar grant with verified free routes and independent call/token/time ceilings; no paid fallback. Freeze report timestamps, canonicalize once, and verify retained-file digests. Implement adapter dispatch offline against fake upstreams before seeking live authorization. Grade distinct task/behavior families and distinguish difficulty from input size.

### R9 — P2: deployment and tracking need reconciliation

- The Mac connector mounts the entire checkout read/write, including any ignored local credential files, and uses the server/operator bearer token for project/mission/review actions. Do not carry that fixture convenience into untrusted workers. Use task workspaces and per-worker scoped credentials.
- API and DB Compose services have no restart policy; only the optional tunnel does. Host reboot recovery and always-on behavior remain unqualified.
- The adopted START_HERE file was changed without refreshing its manifest hash. Three other document hashes match.
- Current state and PR text still cite `dev` at `14c62a77`; live remote verification shows `180eb73a`.
- TH-01–07 are marked implementation-complete, while P01–P19 remain planned. Full product completion cannot be inferred from seven TH checkmarks.
- Cursor recorded Linear `needsAuth` and did not claim successful mutations. This review's Linear connector can read, but project and issue searches for SwarmAI found no match in the accessible workspace. This does not establish absence in every account. Resolve the intended workspace/project before syncing; do not create duplicates or mark disputed evidence Done.
- This chat specified `swarm.splitsignal.com`; Cursor's records say an operator corrected it to `.ai`. The question is pending. Neither domain was changed during review.
- A separate `plan/swarmai-v2-redesign-20260925` branch exists at `8598e6ac`, marked plan complete / implementation not started with 97 packets. Its inference and context language differs from this lane. It is a planning input, not evidence of implementation or authorization to replace the current baseline. Reconcile scope explicitly rather than run two competing plans.

Sources: [connector mount](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/deploy/compose/mac-connector.yml#L25), [server Compose](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/deploy/compose/server.yml), [current lane state](https://github.com/pri8771/swarmai/blob/180eb73a4b67103b3e38f4aaa550ac444307d60a/docs/swarm-mvp/STATE.md), [separate redesign status](https://github.com/pri8771/swarmai/blob/8598e6ace22bb219583ba9398f94f42fb18e137c/docs/redesign/PLAN_STATUS.md).

## What is good and should be retained

- Separate two-host branch and preservation of main/other work.
- Container build, non-root application process after volume initialization, private DB port, loopback API default, and persistent named volumes.
- Explicit refusal to call OpenCode/Hermes fully qualified; no pretend live model benchmark.
- UI reads real API state and exposes artifacts/content hashes, rather than seeding an operational view with provider fixtures.
- Useful deterministic extraction, hash integrity and cold-open tests; negative fixture controls; calibration/holdout labels; no production route promotion from oracle scores.
- Evidence directories and a queued Linear reconciliation record are present. Correct the scope of their claims rather than discard them.

## Independently performed verification

| Check | Result |
|---|---|
| Fresh remote refs and PR status | dev and PR head = 180eb73a; main unchanged; PR open |
| Focused new/changed tests | 30 passed in 1.10 seconds |
| Ruff | 7 errors |
| mypy | 11 errors, 192 source files checked |
| Acceptance forgery | Reproduced completion without execution |
| API state reconstruction | Worker missing; heartbeat 404 |
| Artifact replay after reconstruction | New ID; old link 404 |
| Two ArtifactStore instances | One of two metadata references lost |
| Deleted artifact content | Still served with 200 |
| Forged coding-grader verdict | Incorrectly passes without solution |
| Sandbox external-file boundary | Reviewer-created outside marker readable |
| Zero-dollar grant | Rejected |
| Report hash | Not reproducible from serialization |
| Adopted plan manifest | START_HERE mismatch; remaining three match |
| Existing Mac service | API+DB containers up; API ready; zero configured accounts/routes |
| R730, public domain, live provider, real autonomous mission | Not verified in this review |

The 30 tests were: deployment profile tests, repo-root environment test, Mac connector unit tests, artifact durability tests, runtime-adapter tests and TH-07 harness tests. Passing them does not override the independent failures above.

Reproduction assets: [probe script](CURSOR_REVIEW_PROBES.py), [captured results](CURSOR_REVIEW_EVIDENCE.json). Run the script with the reviewed checkout as its first argument using that project's Python environment. It strips SWARM_* variables and creates temporary state; it does not contact live providers. Its successful exit means the diagnostic script ran, not that the product passed acceptance. Cursor should convert the demonstrated failures into protected regression tests.

## Version assessment

**Current source/build label: V1.0.0rc1. Current delivery state: local engineering prototype / release candidate with acceptance blocked.** Package metadata and the running health endpoint agree on the version string. README still says V0.9 hardening; historical coordination contains V1.7 and V3 targets. Those are inconsistent roadmap labels, not demonstrated release acceptance.

I would report **V1.0 RC, unaccepted** today. I would not call this an accepted V1.0, a working V1.7 distributed swarm, or completed V2/V3. The new autonomous-agent product packets are still planned.

Keep existing tags/history. The following is a **proposed cumulative release roadmap**, aligned where useful with the existing V1.0–V2.0 capability groups. A release requires integrated behavior and evidence, not just relevant files. Some later-version foundations already exist and should be reused. This review does not create release tags or mark milestones accepted.

## Milestones for every 0.1 increment through the integrated MVP

| Version | User-visible milestone | Release exit gate |
|---|---|---|
| **V1.0** | Trustworthy local foundation | R1–R9 blockers resolved or explicitly deferred outside supported scope; required CI green; one bounded deterministic mission has protected verification, durable IDs, replay-safe artifacts and restart recovery. Fixtures labelled. |
| **V1.1** | One genuinely useful autonomous worker | User submits a goal through API/mission UI; agent plans and executes bounded real tools through the kernel; protected verification accepts the actual artifact; cancellation and no-progress stop work. At least one authorized model-backed end-to-end run. |
| **V1.2** | Inference-router integration | Versioned external inference contract handles streaming, tools, actual route identity, context limits, usage, cancellation and quota failure. Free-only/no-paid-fallback enforced; at least one eligible real route qualified. Alternate compatible endpoints fit the interface without duplicating provider ownership. |
| **V1.3** | Trustworthy model/runtime evaluation | Protected graded task families, genuine holdout variants, model/runtime/config provenance, repeated bounded trials and task-specific suitability findings. Fake, oracle and live outcomes separate; no automatic routing promotion. |
| **V1.4** | A collaborating swarm | Human-defined seed personalities/runtime choices; agents share a collective goal, ask for help, exchange evidence and delegate bounded subtasks; no mandatory crews. Integration accepts combined results. Real model-backed collaboration, authority and no-progress negatives demonstrated. |
| **V1.5** | Actual R730 + Mac execution | Server-dispatched task executes on Mac with scoped credentials/workspace; R730 continues when Mac disappears; reconnect/reassignment reconciles work and rejects stale results. Two-machine evidence, not two processes on the Mac. |
| **V1.6** | Durable agent memory and continuity | Working context, reference cues and source-backed memory; corrections and scope isolation; X/Y trainee transfers with stable logical identity and atomic fenced takeover. Verified continuation through context replacement and process failure. |
| **V1.7** | Qualified tools and optional coding runtimes | Generic MCP read/write permissions, approvals, tool evidence and cancellation; OpenCode runs real coding work through the same kernel boundary. Hermes remains optional and separately qualified, never a requirement for native operation. |
| **V1.8** | Recoverable hosted service | Authenticated chosen public hostname, always-on R730 service, backups, clean-environment restore, upgrade/rollback, outage reconciliation, event-stream reconnect and operational visibility. No public database/runtime administration ports. |
| **V1.9** | Customizable agents that learn from evidence | SDK/UI parity for profiles, tools, interactions and templates; evaluated lesson adoption changes later behavior, with provenance, holdout evaluation and rollback. Infrastructure-management UI may remain deferred. |
| **V2.0** | Integrated MVP accepted for regular use | Representative end-to-end missions on deployed service exercise collaboration, router, tools, memory, succession, qualified runtimes and recovery; independent review plus operator acceptance; documented support matrix and measured reliability limits. |

Build dependencies may overlap. For example, safe tool execution is needed at V1.1 even though broad connector/runtime qualification is V1.7. V1.8 formalizes production recovery after basic persistence is already proven at V1.0. Do not postpone foundational safety until the milestone that broadens it.

**Next Cursor assignment: close the V1.0 foundation gates, then return for review.** R730/DNS/provider access does not block the demonstrated local repairs.
