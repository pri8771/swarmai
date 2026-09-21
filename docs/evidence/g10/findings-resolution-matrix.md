# G10 findings resolution matrix (AUD-01…11 → tip evidence)

**Candidate tip:** `aa6865a74249e046bfe697532accb00390bb5873`  
**Pinned audit:** `docs/coordination/AUDIT_V1_2026-09-20.md` (coordination branch; immutable)  
**Worker view only — not lead acceptance**

| AUD | Title | Resolution (worker) | Evidence | Residual |
|-----|-------|---------------------|----------|----------|
| AUD-01 | CI / discovery incomplete | Offline+console CI green on tip | Actions `35538395519` | DB integration skipped without DSN (honest) |
| AUD-02 | Evidence-file presence as pass | Semantic validation of status/command/mode/sha/stale | `src/swarm/release/verify.py`; release tests | — |
| AUD-03/04 | Auth / isolation / idempotency | Scoped actor\|project\|op\|digest; auth before cache; bootstrap≠demo | `routes_v1.py`, `app.py`; fix002 tests | Keep loopback-private until lead review |
| AUD-05 | Known-answer GOOD_FIX | Operational path forbids GOOD_FIX | `worker.py`; `test_no_known_answer_fallback.py` | — |
| AUD-06 | Parser as normal mission | Fixture-only via `--fixture-parser-dogfood` | `worker.py`, `cli.py`, `test_parser_dogfood_fixture.py` | Generic task-provided path still thin (needs target_file) |
| AUD-07 | Scale force-progress | Bypass removed earlier | scale runtime | Load tests remain fingerprint-oriented |
| AUD-08 | Provider readiness fail-open | Fail-closed cost/health/qual/coding | `capability_registry.py`; provider tests | Exact-route price still `price_unverified` until measured |
| AUD-09 | Recovery label honesty | Labels improved; not full kill-worker proof | memory/reliability docs+tests | Full process-kill recovery still open |
| AUD-10 | Multiple mission paths | API/CLI durable MissionStore; console live mode | RUN-111 evidence | Lead must confirm one path suffices |
| AUD-11 | Stale login / handoff | PLATFORM_ACCESS + FIX-004; CLI still Not logged in | fix-004 evidence; login-verify-pending-013 | Operator fresh CLI login required |

## LEAD-009 mapping

| LEAD-009 | AUD | Tip |
|----------|-----|-----|
| #1 mypy broker | AUD-01 | `2335471` |
| #2 scoped idempotency | AUD-03/04 | `2335471` |
| #3 bootstrap split | AUD-03/04 | `2335471` |
| #4 release evidence | AUD-02 | `2335471` |
| #5 provider fail-closed | AUD-08 | `108145ea` |
| #6 parser fixture-only | AUD-05/06/10 | `108145ea` |
