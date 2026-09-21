# SwarmAI full execution audit — 2026-09-21

Status: canonical lead audit after owner stopped/pushed all interactive lanes.

## Executive position

SwarmAI is not blocked by architecture. The architecture is ahead of implementation through V2.x/V3.0. The immediate problem is execution discipline and acceptance closure.

Strict accepted-behavior maturity is approximately V1.2. Implemented capability is approximately V1.5. Architecture/design readiness is well into V2.x.

The critical path is:
1. stable autonomous execution + heartbeat visibility;
2. one successful real V1.4 end-to-end mission;
3. G13 frozen task pool + model/reviewer qualification;
4. V1.5 durable result acceptance + worker service + multi-host evidence;
5. G12 dual-remote zero-charge inference evidence;
6. V1.6/V1.7 product implementation;
7. V1.8/V1.9/V2.0 integration + real acceptance campaigns.

## Source truth

- main: `b9141fa3150f853586dede0334a47b344571bc16` — historical release baseline, not current implementation authority.
- reviewed integration: `cursor/v2-integration@9ce727842446b98cfa55c28c7e70808f57f17d7b`; reviewed application lineage `ee5a06612aa2e4409fa8bbfd1969225c16887615`.
- runtime lane current tip: `cursor/v2-runtime-lane@11a7e1d51c4c4d630c7d83c1af65e380c32ad80f` (latest commits are coordination/status changes).
- product lane current tip: `cursor/v2-product-lane@a908a0e1ff023743892ecb10cfb7bd8df4b53d53` (latest commits are coordination/status changes).
- accepted autonomous-runner repair implementation: `0d71520de72338b3ae38dca00258a07c134e2b2a`; exact-tip CI-bearing descendant `39bba630306729b64ad4679346b1eb900f44ccaf`, CI 35609579398 success. This was human-started and is not autonomous self-launch proof.

## Coordination truth

The older 15m bootstrap successfully reached 3/3 for A and B and graduated to hourly. That evidence is preserved.

The owner intentionally reset heartbeat testing on 2026-09-21:
- Phase 1: 5m effective cadence, 3 consecutive scheduler receipts for A and B, valid gaps 3–8m.
- Phase 2: 15m effective cadence for 24 real hours.
- only after the 24h soak may cadence return to hourly.

Canonical state: `docs/coordination/HEARTBEAT_STATE.json`.

Human-readable live pages:
- `docs/coordination/LIVE_PROGRESS.md`
- `docs/coordination/status/HOST-MAC-DEV.md`
- `docs/coordination/status/HOST-WIN-DEV.md`

Every scheduler heartbeat now writes the host's live status page as well as its JSON ledger.

## What is genuinely verified

### V1.1
Required artifacts are verified:
- generic mission path;
- API/CLI/console same durable mission evidence;
- control evidence;
- real process restart/reopen;
- no automatic primary-checkout apply.

### V1.2
Verified:
- governed inference broker contract;
- real local Ollama inventory;
- actual brokered local inference on multiple models;
- route-disable -> permitted alternate;
- reservation/settlement/quota denial;
- zero-spend local path.

Not accepted:
- remote overlap remains blocked with 0 admitted remote routes.

### V1.3
Accepted/verified:
- frozen qualification protocol;
- provisional screening matrix (72 n=5 cells).

Not complete:
- task pool not frozen;
- zero qualified family/size cells;
- reviewer benchmark/qualification incomplete;
- overhead report not started.

### V1.4
Useful implementation exists:
- graph contract reviewable;
- logical 10/50/100 assignment evidence reviewable (offline only);
- LIVE-142 protocol accepted.

Not complete:
- first real end-to-end mission ran with actual local model inference and $0, but correctly failed because implementation text produced no material worktree diff;
- real-E2E repair/rerun required;
- G14 role manifest blocked on G13;
- live adaptive proof blocked on G12/G13;
- single/fixed/elastic comparison not run;
- LIVE-142 campaign not started.

### V1.5
Accepted bounded implementation packets:
- durable schema/token/migration foundation repair;
- claim/renew/expire fencing including terminal/revision/source/cancellation fences;
- deployment secret-file hardening repair;
- DBOS spike with partial-reuse recommendation only.

Still required:
- durable result acceptance (V2A-003c);
- durable worker service/client;
- real multi-host worker evidence;
- recovery evidence.

## G13 external worker audit

Remote infrastructure is transport only. SwarmAI remains authoritative.

worker-pc produced useful evidence but is not suitable as final G13 gate owner because its Claude execution sandbox repeatedly blocks Python/pytest/ruff/mypy.

Latest useful branch:
- `worker/swarmai-v13-task-pool-freeze-06@f7800332594d67c8b872b3597abd59f35987a2a0`.

Key finding:
- current pool has 15 records per required cell but only 5 genuinely independent semantic archetypes per cell;
- the other records are scenario substitutions/cumulative clause variants;
- counted qualification would overstate independent sample depth.

Therefore:
- ART-V13-TASK-POOL remains drafting;
- counted W-131B qualification is prohibited;
- final G13 implementation/testing ownership returns to Windows B, which can execute Python/tests locally;
- worker-pc becomes verification/audit/support, not gate owner.

## Primary operational defects / blockers

1. Autonomous execution is not yet proven on either local lane.
   - runner source repair is accepted;
   - a repo assignment must still self-launch a real packet and push attributable work without human prompting.

2. Real V1.4 mission path still fails generic materialization.
   - actual inference works;
   - implementation output -> worktree diff path needs repair and real rerun.

3. G13 task pool has inadequate semantic independence.
   - 5 archetypes/cell vs required 15.
   - must re-mint/freeze with executable validation.

4. G12 remote overlap has 0 admitted remote routes.
   - keys/auth metadata exist;
   - exact account/tier/model/quota/zero-charge eligibility is not yet independently proven.

5. V1.5 result acceptance is incomplete.

6. Reviewed integration contains only the previously reviewed V2A-001/V2A-002 baseline; later accepted runtime slices are not yet integrated.

7. V2.0 acceptance evidence is intentionally incomplete:
   - integrated candidate incomplete;
   - install/upgrade/security/performance remain drafting;
   - 7-day reliability campaign not started.

## What should be stopped

- no additional general-purpose Cursor lanes;
- no duplicate ownership of G13 task pool between B and worker-pc;
- no future-planning Cursor lane (lead architecture is already ahead);
- no remote-worker task that cannot produce reviewable evidence for the artifact;
- no code merged merely because descendant CI is green;
- no heartbeat activity counted as implementation progress.

## New fixed topology

### Lane A — Mac / Cursor
Owns runtime + real acceptance:
- V14 real-E2E materialization repair/rerun;
- V15 result acceptance;
- durable worker service/client;
- recovery/integration ownership.

### Lane B — Windows / Cursor
Owns product + evaluation:
- autonomous-runner sync;
- reviewed integration sync;
- final G13 task-pool remint/freeze with executable tests;
- reviewer benchmark/qualification;
- V16 knowledge/provenance;
- V17 tools/approval binding.

### Lane C — worker-pc / Claude via remote-workers
Owns independent support:
- read-only code review/audit;
- benchmark/evidence inspection;
- bounded branch fixes only where execution restrictions do not prevent verification;
- independent review of A/B submissions;
- never owns final acceptance of a gate requiring Python/test execution it cannot run.

### Lead — ChatGPT
Owns:
- canonical registry;
- architecture/contracts;
- independent review;
- assignment and priority;
- integration decisions;
- heartbeat phase transitions;
- live dashboard;
- worker-pc dispatch;
- acceptance decisions.

## Definition of forward progress

A heartbeat update is liveness/status, not completion.

A packet is reviewable only with:
- exact source SHA;
- exact changed files;
- exact checks/tests and outcomes;
- truthful blockers;
- evidence binding;
- no self-acceptance.

A milestone advances only when the required artifact set advances.
