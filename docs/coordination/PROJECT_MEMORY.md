# SwarmAI compact project memory

Curated 2026-09-20 after LEAD-20260920-016. `ARTIFACT_REGISTRY.json` is canonical; this is a short derived orientation only. Read registry/state and unread message pointer before deeper files.

## Authority and operating model

Owner authorized implementation through V1.4 inclusive. ChatGPT leads artifact design, decomposition, research, statistics and independent review; Cursor is implementation workhorse and should receive most SP1-SP3 code/test/evidence work. Versions are accepted artifact sets, not task counts. Main merge/release/public deployment/new spend/destructive actions/V1.5+ source implementation remain unauthorized. Future architecture/contracts may be advanced by lead in isolation.

No operational demo data, fake readiness, known-answer substitution, mock-success fallback, quota bypass or invented live evidence. Isolated tests never satisfy live gates. Credentials/private identities/browser state stay outside Git.

## Current source

Main `b9141fa…`. Draft PR #14 `cursor/v1.4-live-integration-11e2` @ `03d85540e36c36fa3a5c92a3082be9959d93f66d`. Application tree last materially changed at `d9da26c…`; later candidate changes are evidence/docs. Actions `35545174895` is green for offline+console. DB integration is honestly skipped without `SWARM_DATABASE_URL`; live-gated CI is notice-only, not live evidence.

## Artifact truth

**V1.0 repair:** candidate/security/evidence/runtime artifacts are verified. `ART-V10-WORKER-HEARTBEAT` is blocked because Cursor CLI `status/whoami` remain Not logged in; scheduler probes are not authenticated worker receipts.

**V1.1:** mission path, actual Chromium console/API/CLI same-ID evidence, wrong-output/unsupported/cancel controls and explicit apply boundary are verified. Restart artifact was demoted to drafting: current evidence recreates app/store objects but does not stop/start the actual service process. W-111C SP1 ready.

**V1.2:** provider-eligibility ledger is verified as truthful and currently yields **0 admissible remote routes**. Independent source review found `ProductStore.execute_mission()` creates a `RepoWorker` without broker/project ID, allowing direct local inference fallback; broker contract is drafting and W-122A SP2 is ready. Dual-remote overlap remains blocked. Lead created `ART-V12-REMOTE-ADMISSION-RESEARCH.md`; public docs only narrow OpenRouter/Groq/Gemini candidates and never admit an account route by themselves.

**V1.3:** frozen qualification protocol accepted. Screening matrix verified: 72 provisional n=5 cells, three local models, S/M/L/XL, six families, no qualification claim. Qualification task/scorer/prompt/tool/model identity manifest is not frozen; W-131C1 SP2 ready. No qualified cells. First candidate batches after freeze: planning/XL gemma3:4b; coding/XL qwen3.5:4b; reasoning/L qwen3.5:9b. Reviewer screening is weak; W-131C2 SP3 calibration-only benchmark repair/freeze ready.

**V1.4:** graph/load artifacts are offline preparation only. Qualified role manifest, real dual-remote adaptive proof, mode comparison and LIVE-142 remain blocked/not started.

## Worker calibration

Reviewed artifact-oriented packets: W-111A SP2 accepted first review; W-111B SP2 changes-required only for process restart and split to W-111C; W-121A SP2 accepted as truthful blocked-state evidence; W-131A SP1 accepted. Buckets have fewer than five completed packets, so performance estimates remain unstable.

Ready Cursor queue: W-111C SP1, W-122A SP2, W-131C1 SP2, W-131C2 SP3. W-131B/W-121B/G14/live campaign remain dependency-blocked.

## Future artifact progress

Lead drafted substantive V1.5 distributed-worker architecture and `ART-V15-WORKER_PROTOCOL.md` covering enrollment, generation fencing, heartbeat, durable lease CAS, renewal/expiry, result envelopes, acceptance fencing and duplicate-effect recovery. This is design only; no V1.5 code authorization.

## Human action

Only immediate human step for G10 is completing a live `cursor agent login` while its CLI waiter remains active, then confirming `cursor agent status` and `cursor agent whoami` authenticate. Do not clear the probe skip before that.
