> **Latest owner assignment — 2026-09-22:** GPT-6 Sol in a new Codex task is the next SwarmAI implementation owner; target accepted LIVE V1.7. Read `docs/coordination/OWNER_RACE_V17_20260922.md` and `docs/coordination/GPT6_SOL_SWARM_V17_RACE_20260922.md` first. State: ASSIGNED_WAITING_FOR_WORKER, not launched. This supersedes older worker/pause routing below only; existing evidence, review holds and action grants are unchanged. No new scheduler or watcher.

# Owner decisions and goal post reset to V1.7 — SwarmAI — 2026-09-22 (~18:45Z)

Recorded by Claude from the owner's direct messages in the current Claude session. **This records owner direction only. It is not a lead verdict, a release or a version acceptance.** The native ChatGPT Swarm lead must reconcile `EXECUTION_CONTROL.json`, the packet queue and the registry, and keeps acceptance authority.

## Owner messages (verbatim)

- To the two questions ("fix the one-line lint in `src/swarm/api/store.py` as its own change?" and "is public-repo Actions the intended CI route; R33c would now create a public issue"): **"1. yes, 2 yes."**
- **"If we havent reached 1.7 for any, then change the goal post for 1.7"**

## Decisions

1. **Target: V1.7.** Swarm has not reached V1.7, so V2.0, V2.3 and V2.7 are deferred. `goal_version`, `authorized_versions`, `requested_target_version` and `stop_after` should become V1.7. Stop at accepted V1.7.
2. **Lint packet: released by the owner and done.**
   - Source: `codex/swarm-ruff-store-imports-20260922@349c732c335d83eaa431d30ea7f2b52b8d4431a3`, tree `129ada5a`, draft PR29, base `6dbf8c4`.
   - Change: import order only. The `store.py` blob `76d7ddba` is identical on 6dbf8c4, fb58a751 and P0 `11bd4b52`.
   - Hosted CI `35767004625` and `35766998821` fully green: Ruff, mypy, packaging, Alembic heads, offline pytest 400/73, console lint/test/build. Hosted CI skips PG integration because SWARM_DATABASE_URL is unset.
   - Local: full owned PG 616 passed / 13 skipped, cleanup 0; offline 421/208; mypy 174.
   - Awaiting lead verdict.
3. **CI:** public-repo Actions is the owner-confirmed zero-cost route (EXT-ACTIONS-BILLING disposition). There is no billing change.
4. **R33c:** the owner OK'd the now-public `pri8771/swarmai` as the test target in principle. It still needs its lead release and an exact per-action grant at execution time. Nothing has been executed.

## Where Swarm is (native evidence, adversarially checked)

- **Official:** no version at or above V1.0 is formally accepted. V1.1 is the highest fully verified set (lead registry `swarm-control@8fb35b4:docs/coordination/ARTIFACT_REGISTRY.json`). The registry `updated_at` of 2026-09-21T17:08Z predates every 09-22 acceptance.
- **Engineering:** partway through V1.7. The latest lead-accepted source is `fb58a751` (1d85f4b).
  - Accepted slices: R27c/d/e, R28a, R28b-1/-2, R28c, R28d repair, R29a, R30a, R02a guard, R02c `1c9ff44`, and R17a (harness evidence only).
- **Native V1.7 milestone** (VERSION_ARTIFACT_MATRIX) includes the V1.0-repair through V1.6 artifact sets and CP0–CP6.
- **Pending on the lead:** PR28 R30b-P0 `11bd4b52` (READY_FOR_LEAD_REVIEW, packet e72de3a) and PR29 lint `349c732c`.

## V1.7 blockers

### Lead verdicts, releases and reconciliation

1. **Control:** EXECUTION_CONTROL still reads PAUSED_BY_OWNER with every hold true. `r30b_p0_status` is stale. There is no record of the resume, the V1.7 target or the lint packet.
2. **Verdicts:** PR28 P0 and PR29 lint.
3. **Composition order for one V1.7 tip:** `fb58a751` + P0 `11bd4b52` + lint `349c732c` + **R02c `1c9ff44`**. R02c touches `mission/worker.py`, which was rewritten between 05fe780 and 6dbf8c4, and its composition is untested. After that, run PG composition on one tip. P0 + fb58a751 alone passes offline 437/211/0 (reviewer scratch).
4. **Queue reconciliation:**
   - R02a and R17a are accepted but listed "ready". That blocks R02b and R17b, and through them R34b.
   - OPS-CI-01 is implemented at `ab958d7` but unreviewed.
   - R00 (CP0 package) is review_pending.
5. **Implemented but unreviewed:** R27a `0505c24`, R27b `d3a7b56`, MISSION-CANCEL-01 `2237eff`, and the CP3 rerun `cp3-20260922T020141Z` (e53da73, 9/9 with product cancel).
6. **Releasable now:** **R31a** (every dependency satisfied). Next come R25a (after R28d is reconciled), R25b, R17b/c, R31b, R32a and R33a/b.
7. **Lead-owned gates:** EXT-G13-SEALED-DIGEST; the G13 platform-neutral ruling (alternative to the Windows host); the EXT-V10-WORKER-HEARTBEAT ruling.
8. **Registry promotion and reviews:**
   - Promote V1.0-repair (4) and V1.1 (5) from verified to accepted.
   - V1.3: promote SCREENING-MATRIX; review REVIEWER-QUALIFICATION (R05).
   - V1.4: review GRAPH-CONTRACT and LOAD-10-50-100.
   - V1.5: review WORKER-PROTOCOL (V2A-003c) and LEASE-FENCING.

### Owner grants (aliases/paths only)

| ID | Needed |
|---|---|
| CP1 (V1.4 real mission) | New preregistration plus explicit attempt-limit disposition. 2/2 attempts are used and 0 remain |
| CP2 G12 | Aliases and quota facts for ≥2 zero-charge remote providers (0 admitted); bounded routes and caps |
| CP2 G13 | HOST-WIN-DEV access, or accept a lead platform-neutral ruling |
| R28d successor | One local/private live_local mission: named host, model, route and throwaway target; call/token/time caps; expiry; $0. The previous run was consumed by the failed `r28d-live-local-20260922-01` |
| CP3 | An owned second physical host with PG, Git and Python reachable. None exists |
| CP4 / CP5 | Knowledge-scope path; exact local/API/browser-session targets |
| R33c | Exact per-action grant (public target OK'd in principle) |
| R34a | One real $0 mission with broker, lease, knowledge and action receipts (needs a model grant) |

### Elapsed time

WC-LIVE142-24H, the V1.4 24h campaign, requires G10–G14 plus R11, and R11 is blocked by G12/G13. Elapsed time is never backfilled.

### Engineering (only after release)

- R30b HttpApiAdapter (after P0).
- R31a/R31b session adapter and recovery.
- R32a negative matrix N17-01..26.
- R33a/R33b CP5 run.
- R34a/R34b CP6. CP6 must bind migrations and the full deterministic checks, including PG, which hosted CI skips.
- R25a/b knowledge (V1.6) and R17b/c (V1.5).
- V1.4: ROLE-MANIFEST, LIVE-ADAPTIVE-PROOF (R11), MODE-COMPARISON, FINAL-REPORT.
- V1.3: OVERHEAD-REPORT (R08).

**Smallest first moves:**
- Lead: record V1.7 and resume in control; verdicts on PR28/PR29; release R31a and the composition order.
- Owner: G12 provider aliases (the longest lever, since it starts the V1.4 24h clock) and the CP1 attempt disposition.
