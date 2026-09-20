# SwarmAI version artifact matrix

Derived human view of `ARTIFACT_REGISTRY.json`. The registry is canonical. Updated 2026-09-20T23:51:30Z.

Legend: `A` accepted · `V` verified · `R` reviewable · `D` drafting · `B` blocked · `P` planned.

## Current authorized tranche

| Version | Artifact | State | Current truth / next transition |
|---|---|---:|---|
| V1.0 repair | ART-V10-CANDIDATE | V | PR #14 exact tip `03d85540…`; Actions 35545174895 green for offline+console; DB integration skipped honestly; live CI gate not executed. |
|  | ART-V10-SECURITY | V | Source/regressions lead-verified; retain. |
|  | ART-V10-EVIDENCE-CONTRACT | V | Evidence binding/readiness truth lead-verified; reuse. |
|  | ART-V10-RUNTIME-TRUTH | V | Operational no-mock/no-known-answer boundary lead-verified. |
|  | ART-V10-WORKER-HEARTBEAT | **B** | Scheduler probe exists but CLI `status/whoami` still Not logged in. Human login -> W-041B manual authenticated receipt -> W-041C two genuine hourly receipts. |
| V1.1 | ART-V11-MISSION-PATH | **V** | Generic durable extract/triage/plan execution and same durable store independently reviewed. |
|  | ART-V11-MULTISURFACE-EVIDENCE | **V** | Actual Chromium console UI create; API/CLI same ID; three unfamiliar tasks across extract/triage. |
|  | ART-V11-CONTROL-EVIDENCE | **V** | Unsupported task, deliberate wrong output and cancellation evidence independently verified. |
|  | ART-V11-RESTART-EVIDENCE | **D** | Current proof recreates `create_app`/MissionStore but does not stop/start the actual service process. W-111C is ready. |
|  | ART-V11-APPLY-BOUNDARY | V | Explicit reviewed apply boundary retained. |
| V1.2 | ART-V12-BROKER-CONTRACT | **D** | MissionRuntime is brokered, but `ProductStore.execute_mission` still creates `RepoWorker` without broker/project ID and can fall back to direct `local_chat`. W-122A ready. |
|  | ART-V12-PROVIDER-ELIGIBILITY | **V** | W-121A ledger truthfully proves **0 admissible remotes** and local routes available. |
|  | ART-V12-REMOTE-ADMISSION-RESEARCH | D | Lead public-doc checklist narrows OpenRouter/Groq/Gemini checks; account-specific evidence still required. |
|  | ART-V12-REMOTE-OVERLAP | **B** | Needs W-122A plus two current exact zero-additional-spend remote routes. |
|  | ART-V12-LOCAL-FALLBACK | R | Local evidence exists; re-review/rebind after broker bypass closes. |
|  | ART-V12-ADMISSION-RECONCILIATION | R | Local reservation evidence exists; re-review after broker integration and extend during remote proof. |
| V1.3 | ART-V13-QUAL-PROTOCOL | **A** | Frozen protocol v1.0; no post-hoc threshold changes. |
|  | ART-V13-TASK-POOL | **D** | Qualification/calibration pool IDs/hashes and scorer/prompt/tool/model manifest must be frozen before W-131B. W-131C1 ready. |
|  | ART-V13-SCREENING-MATRIX | **V** | 72 provisional n=5 cells across three local models × S/M/L/XL × six families; no qualification claim. |
|  | ART-V13-QUALIFIED-MATRIX | D | No n>=15 qualified cell. After task-pool freeze, first lead-selected batches: planning/XL `gemma3:4b`; coding/XL `qwen3.5:4b`; reasoning/L `qwen3.5:9b`. |
|  | ART-V13-OVERHEAD-REPORT | P | Collect during real qualification. |
|  | ART-V13-REVIEWER-QUALIFICATION | D | Existing reviewer screening weak; W-131C2 calibration/freeze ready. |
| V1.4 | ART-V14-GRAPH-CONTRACT | R | Offline graph contract only; review after broker boundary closes. |
|  | ART-V14-ROLE-MANIFEST | B | Depends on qualified product + reviewer routes. |
|  | ART-V14-LIVE-ADAPTIVE-PROOF | B | Depends on G12 remote overlap and G13 qualified roles. |
|  | ART-V14-LOAD-10-50-100 | R | Offline logical-assignment load evidence only; not real model concurrency. |
|  | ART-V14-MODE-COMPARISON | P | After live adaptive proof. |
|  | ART-LIVE142-PROTOCOL | **A** | Frozen final campaign protocol. |
|  | ART-LIVE142-CAMPAIGN | B | G10-G14 dependencies incomplete. |
|  | ART-LIVE142-FINAL-REPORT | P | Lead-owned after campaign. |

### Current version-level truth

- **V1.0 repair is not accepted**: worker heartbeat artifact remains blocked by Cursor CLI authentication.
- **V1.1 is not accepted**: four required artifacts are verified, but actual process restart/reopen remains drafting.
- **V1.2 is not accepted**: broker boundary has a concrete operational bypass and there are zero admissible remote routes.
- **V1.3 is not accepted**: screening is complete/provisional; held-out qualification has not begun under a frozen qualification pool.
- **V1.4 is not accepted**: qualified roles, remote overlap, live adaptive proof, comparison and final campaign remain absent.

## Ready Cursor work

At least four dependency-ready bounded packets now exist:

1. **W-111C / SP1** -> `ART-V11-RESTART-EVIDENCE`: actual service-process stop/start + same mission reopen from another surface.
2. **W-122A / SP2** -> `ART-V12-BROKER-CONTRACT`: broker `ProductStore.execute_mission` and prove no direct inference bypass.
3. **W-131C1 / SP2** -> `ART-V13-TASK-POOL`: freeze qualification task/scorer/prompt/tool/model identities and separate calibration from held-out data.
4. **W-131C2 / SP3** -> `ART-V13-REVIEWER-QUALIFICATION`: calibration-only benchmark/scorer repair, then freeze new reviewer benchmark; no held-out qualification before freeze.

W-131B becomes ready only after W-131C1 review. W-121B remains blocked until two remotes are independently admissible and the broker boundary is reviewable.

## Future artifact progress — no future code authorization

| Version | Lead artifacts advanced | State |
|---|---|---:|
| V1.5 | ART-V15-ARCH | D |
|  | **ART-V15-WORKER-PROTOCOL** | **D — enrollment/generation/heartbeat/lease/result/acceptance-fence protocol drafted** |
|  | ART-V15-LEASE-FENCING | P |
|  | ART-V15-MULTIHOST-EVIDENCE | P / implementation not authorized |
|  | ART-V15-RECOVERY-EVIDENCE | P / implementation not authorized |
| V1.6 | ART-V16-KNOWLEDGE-CONTRACT | D |
| V1.7 | ART-V17-TOOL-CONTRACT | D |
| V1.8 | ART-V18-RECOVERY-ARCH | D |
| V1.9 | ART-V19-BETA-ACCEPTANCE | D |

Future design artifacts are isolated from PR #14. They do not authorize V1.5+ source work, merge, deployment, spend or release.
