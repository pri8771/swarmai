# SwarmAI lead work queue — approved through V1.4

Updated 2026-09-20 by LEAD-20260920-010. Owner authorization remains V1.0 repair -> V1.4 inclusive. Evidence/independent review gate acceptance; main merge/release/public exposure/additional spend remain unauthorized. Stop feature work at V1.4.

Remote main: `b9141fa3150f853586dede0334a47b344571bc16`. Draft PR #14 current tip reviewed: `f75c6cb5bb8e0d2d2d2c0c6e4061fe2909f11efc`. Actions `35539853498` is current-tip green for offline+console checks, but **G10 is not accepted** because source review found operational mock contamination, worker/approval ownership gaps, and insufficient release-evidence binding. Cursor agent CLI remains Not logged in; do not clear `SWARM_HOURLY_SKIP_CURSOR_PROBE`.

## Execution discipline

Use `cursor/v1.4-live-integration-11e2` plus bounded worktrees. One owner integrates shared API/store/schema/lockfile changes. Preserve unrelated work. Status progression remains queued -> assigned -> in_progress -> implemented -> tests_verified -> live_verified where required -> lead_reviewed. Passing CI is necessary, not sufficient. Unknown/blocked is better than fake success.

## G10 / V1.0 repair

### FIX-001 — comprehensive CI and honest baseline

Status: `tests_verified_current_tip` for CI scope. PR #14 tip `f75c6cb…`; Actions `35539853498`.

Verified by lead: console `npm ci`/lint/Vitest/build success; Ruff success; mypy **139 source files** success; install/package check success; Alembic head `9eb193b10f4e`; broad offline pytest **245 passed, 2 skipped**. CI integration tests are explicitly blocked/skipped because `SWARM_DATABASE_URL` is absent; this is not a pass. Prior local PostgreSQL integration evidence is worker-reported, not re-executed by lead.

Next: rerun these same current-tip checks after the G10 source fixes below. Do not regress coverage.

### FIX-002 — authentication, project boundaries, scoped ownership

Status: `partial_changes_required`. Core mission/history authorization and scoped idempotency are materially improved; all inspected operational idempotency callers now use actor/project/operation/digest after authorization. Remaining release blockers:

1. Persist project ownership for workers and approvals.
2. `GET /v1/workers` must filter by caller project(s) or admin authority; no global cross-project metadata view.
3. `GET /v1/approvals` must filter by ownership; resolve/detail operations must authorize against the approval's durable owning project, not simply the caller's first project.
4. Worker heartbeat/detail/control paths must bind to worker project ownership plus membership token as appropriate.
5. Add two-project fail-before/pass-after tests proving no body/metadata leakage or cross-project resolve/heartbeat.
6. Operational bootstrap token must not silently receive hard-coded `{proj_demo, proj_other}` membership. Require explicit install-local principal/project mapping or generated/persisted install identity. Fixed demo IDs remain fixture-only.

Accept: all above regressions pass; known demo credentials remain fixture-only/loopback-only; no secret leakage.

### FIX-003 — evidence-backed release/readiness

Status: `partial_changes_required`. Provider registry fail-closed behavior is materially improved and should be preserved. Release verifier is not yet contract-complete.

Current defect: `_validate_evidence_file()` can pass an evidence record with no source SHA; the current release test explicitly expects a no-SHA record to pass. Tighten evidence schema so a behavioral pass requires:

- exact candidate SHA present and equal to current candidate;
- command inventory plus actual successful exit/result;
- explicit evidence mode;
- generated/observed timestamp and defined freshness window/policy;
- relevant config/dataset/model/tool version identifiers for the evidence type;
- stale, missing, mismatched, failed or unbound evidence => fail/unknown.

Add negative tests for missing SHA, wrong SHA, failed exit, stale timestamp, wrong mode and missing required config identity. Do not satisfy this by adding another boolean.

### FIX-004 — platform sessions and actual hourly worker

Status: `partial_scheduler_verified_worker_auth_blocked`. Repeated scheduler check-ins exist, but unattended Cursor spawning is not verified because `cursor agent status` and `cursor agent whoami` report **Not logged in** and the scheduler intentionally skips the agent probe.

Code work continues. Human action only when convenient for this lane: complete the active browser auth/passkey/MFA/consent from a fresh `cursor agent login`; then verify `status` + `whoami` before clearing the skip. No paid cloud automation.

### FIX-005 — remove operational demo/mock dependence

Status: `partial_changes_required`. GOOD_FIX operational substitution is removed, parser dogfood is opt-in, and the scale force-progress bypass is no longer found in current searched source. However normal product surfaces still contain mock/fixture runtime behavior and this violates the current real-data policy.

Required repair:

1. `ProductStore` normal mode must not default to `execution_mode="mock"`.
2. `/v1/capacity` must not build/explain a mock broker. Return actual observed broker state, or honest empty/unknown/unsupported state until wired.
3. `/v1/providers` and `/v1/routes` must not present mock/fixture data as operational state. Catalog-only entries may be shown only as explicitly cataloged/unverified; connected/available state must come from actual observations.
4. Normal console live loading must NOT spread `MOCK_SNAPSHOT` into routes/workers/profiles/etc. Build a true empty live snapshot and populate only real endpoint results.
5. Default operational console must not silently choose mock mode. Mock fixture mode may exist only as an explicit dev/test surface.
6. Remove **Recover with mock fixtures** from operational error handling; errors remain errors with retry/diagnostic actions.
7. Expand/Contract UI must call the operational graph API/runtime when implemented; local fixture mutations cannot masquerade as a real swarm action.
8. Remove or fixture-gate `/v1/missions/{mission_id}/side-effects/demo` so it is not shipped in the normal router.
9. Add regression tests asserting a clean operational install/console contains no fixture routes/workers/profiles/missions and no mock fallback on API failure.

Accept: operational install is genuinely empty/unconfigured/unknown where appropriate, and test fixtures remain isolated.

## G11 / V1.1 — RUN-111 unified generic mission

Status: `in_progress_not_accepted`. Current evidence shows durable identity/restart/review controls and default parser dogfood is no longer selected. Residual acceptance remains exactly what the G11 evidence index states: three unfamiliar tasks fully executed across two families via console+API+CLI on the same IDs.

Additional lead finding: normal `MissionRuntime` still copies accepted worktree files into the primary checkout. Replace automatic promotion with an explicit apply/approval boundary or return diff/artifacts for review. No mission acceptance should silently modify an unrelated primary worktree.

Do not call G11 accepted until G10 source repairs are integrated and current-tip green.

## G12 / V1.2 — INF-121 concurrent governed inference

Status: `in_progress_local_only_not_accepted`. Local broker/fallback preparation does not satisfy the gate. Required: overlapping real calls through at least two independently authorized remote providers in one mission plus an actually available local route, with exact route identity, zero-charge eligibility, admission and reconciliation evidence. No paid fallback.

## G13 / V1.3 — EVAL-131 empirical qualification

Status: `provisional_screening_not_qualified`. Latest worker evidence tip `484647c…`: S/M/L/XL × six families × gemma3:4b+qwen3.5:4b plus third model qwen3.5:9b on S+M at n=5 = **60 provisional cells**; qualification_claimed=false. Useful screening only.

Still required before qualification: preregistered acceptance/uncertainty criterion, overhead accounting, and sufficient samples to satisfy the criterion. Preserve weak/failed cells; do not promote observed 1.0/0.8 rates from n=5 into qualified profiles.

Per LEAD-010: pause further screening volume while G10 FIX-005/002/003 repairs are open.

## G14 / V1.4 — SWARM-141 adaptive organization

Status: `offline_prep_not_accepted`. Existing 10/50/100 logical load and graph artifacts are preparation only. Required live proof remains: multiple planning/review configurations contribute, evidence causes real graph expansion, convergence causes contraction/merge/cancel, useful work overlaps, and admission is enforced.

## LIVE-142 — final V1.4 acceptance

Status: `not_started`. Requires integrated G10-G14 plus the contract campaign: all applicable checks, 12 preregistered positive missions, six negative scenarios, real provider overlap/local fallback, real graph adaptation, restart/reopen, and an observed 24-hour protected live window. Keep every attempt. No time acceleration or cherry-picking.

## Immediate next action for Cursor

ACK `LEAD-20260920-010` (posted in CURSOR-017). Optional G13 L/XL + third-model $0 screening gap closed provisionally at tip `484647ce1156a3227d60bb8d990cfd2a6f949bf6` (CI `35541311971` success); still not qualified. Next: repair FIX-005 operational mock contamination, FIX-002 worker/approval ownership + bootstrap scoping, and FIX-003 strict evidence binding; then remove G11 automatic primary-checkout promotion. Push one integrated candidate, rerun full current-tip CI/security/evidence regressions, and post exact SHA/run IDs/results. Do not clear `SWARM_HOURLY_SKIP_CURSOR_PROBE` until CLI status verifies. No merge/spend/launch.
