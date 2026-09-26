# SW-W0-S1 handoff
- Branch: `cursor/sw-w0-s1-460c`   Base SHA: `8e1c0fdec24c131e7612d88076220945230f4c3b`   Head SHA (code): `dc2f15cf5c16226a1f5b9e753da219eb1ea5a621`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W0-S1.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- Created `config/v23/scheduler_policy.v1.json` (policy `v23-wdrr-1`) and `benchmarks/v23_acceptance/scenarios.freeze.json` (`frozen_at` set to commit time, `version_claim_policy: never_mark_accepted_from_harness`).
- Replaced `docs/v2.3/STATUS.md` with the honest 16-item truth table (scaffold / missing / pending); nothing claimed accepted.
- `docs/v3.0/STATUS.md`: heading no longer claims implementation-complete; added the "blocked on V2.3; scaffolds" sentence. Other content kept.
- `CHANGELOG.md`: new `## Unreleased` with the two entries; the old heading's V2.3/V3.0 implementation-complete claim replaced by "V2.3/V3.0: scaffolds only — see docs/v2.3/STATUS.md".
- `docs/agents/*`: tip `dd7726eb…` → `8e1c0fdec24c131e7612d88076220945230f4c3b` (subject "Merge pull request #69 …"), `pause: false`, `v20_work: V23_ENGINEERING_ACTIVE`, `verified_at` now; `v23` block (`accepted: false`) in `context.json` and a `## v23` table in `CURRENT.md`; RESUME active-work line; README index; V20_TODO owner hints E03–E11. `hard_limits` unchanged.
- Created `docs/v2.3/PLAN.md` (verbatim coordinator plan) and `docs/v2.3/sessions/README.md`.
## Verification
Checks run by `/agent/wt/check.sh` on commit `dc2f15cf5c16226a1f5b9e753da219eb1ea5a621` (Postgres 127.0.0.1:5432 available):
```
ruff: [1;32mAll checks passed![0m
mypy: Success: no issues found in 236 source files
alembic heads: a20pursuitpersist0001 (head) 
offline CI: 510 passed, 3 skipped in 28.53s
integration (Postgres): 69 passed in 17.63s
tree: 60b17ce79e67c73dcb755b0e815cd2d4933208ff dirty=0
```

## Acceptance
- [x] Both JSON files exist and parse; `policy_version` is `v23-wdrr-1`; `version_claim_policy` is `never_mark_accepted_from_harness`.
- [x] No file in the repo still says V2.3 or V3.0 is "implementation-complete" (`git grep -n -i "implementation-complete" -- docs CHANGELOG.md README.md` shows only historical/quoted lines or the new "not claimed" wording).
- [x] `docs/agents/*` show the Setup SHA, `pause: false`, and a v23 block with `accepted: false`.
- [x] `docs/v2.3/PLAN.md` and `docs/v2.3/sessions/README.md` exist.
- [x] No Python, test, workflow or lock file changed.
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [x] `uv run alembic heads` prints exactly one head.
- [x] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [x] Integration run passed, or SKIPPED with reason in the handoff.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no real network calls, no `accepted`/`complete` claims.
## Decisions
- Pause lift recorded per the owner's V2.3 request (B-01), engineering only; HL-01..HL-07 unchanged.
- Short SHAs inside the historical `fast_track_merged_order` tables were left as they are (they are merge SHAs, not the tip).
- Historical evidence files (`docs/evidence/V3_EXIT_REQUIREMENT_AUDIT.md`, `docs/evidence/v30/LEAD_ACCEPT_PACKAGE.md`, `docs/v1.8|v1.9|v2.0/STATUS.md`, checklist headings) still contain the phrase "implementation-complete"; they are dated records / checklist titles outside this session's files and do not claim V2.3/V3.0 completion on the current tip.
- Tests were run against a private Postgres database `swarm_sw460c` (same server) to avoid collisions with concurrent agents on the shared `swarm` DB.
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
