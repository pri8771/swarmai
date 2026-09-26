**Goal.** This is the Wave-4 **serialization point**. Run it only after `SW-MERGE-W3` reports every required session merged into `cursor/sw-v23-integration-460c`. It does four things:
1. Fixes **F-14**: a single `CURRENT_SCHEMA_REVISION` constant replaces the three stale `"a18tov30schema0001"` literals, and a test pins it to the Alembic head.
2. Fixes **F-16**: `POST /v1/release/candidate-freeze` becomes admin-only. Today any authenticated principal can run `git` and write a candidate manifest.
3. Adds `scripts/v23_acceptance_campaign.py`, runs it, and commits the sanitized evidence.
4. Rewrites the status and agent docs to state **exactly** what is true: implementation-complete candidate, **not accepted**, with the external gates listed as pending or blocked.

The code below was compiled and run on the fully integrated scratch tree (`dev @ 8e1c0fde` plus all 23 other sessions):
- The full `uv run pytest` gives 763 passed, 1 skipped on the scratch tree. On the executed integration branch (after SW-FIX-ALEMBIC, `604f7ace`) it gives `778 passed, 1 skipped` with a private database; before that fix it had 4 Alembic failures (see Step 6).
- The campaign gives `deterministic: pass` (10/10). On a VM without router, Docker or LiveGrant it reports `live_router_free_route: blocked:router_not_configured` and `compose_smoke_v20_e10: blocked_env_no_docker`.
- ruff and mypy: clean.

### Step 1 — `src/swarm/release/candidate.py` (one insertion)
Directly below the line `from swarm.contracts.common import new_id, utc_now` (and its blank line), insert:
```python
# Must equal the Alembic head; tests/release/test_schema_revision.py enforces it.
CURRENT_SCHEMA_REVISION = "a23opsplatform0001"
```
Then check the head. If this prints anything other than `a23opsplatform0001 (head)`, use the printed revision id as the constant value instead:
```bash
uv run alembic heads
```
There must be **exactly one** head. Two heads means a second migration slipped in; STOP (S4, section 10).

### Step 2 — `src/swarm/cli.py` (three exact edits, nothing else)
**2a.** Find this block (the recovery backup command):
```python
        from swarm.recovery import BackupService
```
and replace it with:
```python
        from swarm.recovery import BackupService
        from swarm.release.candidate import CURRENT_SCHEMA_REVISION
```
**2b.** In the same command, replace `            schema_revision="a18tov30schema0001",` with `            schema_revision=CURRENT_SCHEMA_REVISION,`.

**2c.** In the `release candidate-freeze` branch:
- replace `        from swarm.release.candidate import CandidateFreezer` with `        from swarm.release.candidate import CURRENT_SCHEMA_REVISION, CandidateFreezer`;
- replace `            source_sha=sha, schema_revision="a18tov30schema0001"` with `            source_sha=sha, schema_revision=CURRENT_SCHEMA_REVISION`.

### Step 3 — `src/swarm/api/routes_v1.py` (function `freeze_candidate` only)
Replace:
```python
    principal: Principal = Depends(get_principal),
) -> dict[str, Any]:
    _ = principal
    import subprocess
    from pathlib import Path

    from swarm.release.candidate import CandidateFreezer
```
with:
```python
    principal: Principal = Depends(get_principal),
) -> dict[str, Any]:
    if "admin" not in principal.roles:
        raise ApiError("forbidden_admin", "admin role required", status_code=403)
    import subprocess
    from pathlib import Path

    from swarm.release.candidate import CURRENT_SCHEMA_REVISION, CandidateFreezer
```
and replace `.freeze(source_sha=sha, schema_revision="a18tov30schema0001")` with `.freeze(source_sha=sha, schema_revision=CURRENT_SCHEMA_REVISION)`.

Then run:
```bash
grep -rn "a18tov30schema0001" src/swarm/cli.py src/swarm/api/routes_v1.py   # must print nothing
```

### Step 4 — `tests/release/test_schema_revision.py` (create, exactly)
```python
{{FILE:tests/release/test_schema_revision.py}}
```

### Step 5 — `scripts/v23_acceptance_campaign.py` (create, exactly)
```python
{{FILE:scripts/v23_acceptance_campaign.py}}
```

### Step 6 — run checks, then the campaign
```bash
git clean -fdX -- var/
uv run ruff check . && uv run mypy src/swarm
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w4_s1   # private DB (section 6 creates it)
uv run pytest -q                                     # whole suite; record passed/skipped counts
(cd apps/console && npx vitest run && npx oxlint src) # console
uv run python scripts/v23_acceptance_campaign.py; echo "exit=$?"
git checkout -- schemas/v1 docs/evidence/fix-004 var 2>/dev/null || true   # undo test rewrites (F-11)
git status --short                                   # only your owned files may appear
```
- Do **not** set `SWARM_ROUTER_BASE_URL`, `SWARM_ROUTER_MODEL`, `SPLITSIGNAL_BASE_URL` or `SPLITSIGNAL_MODEL`, and do not create a LiveGrant, to "make the gate green". If the environment already injects `SPLITSIGNAL_*` secrets, leave them; the gate then honestly reads `blocked:<LiveGrant reason>`. The campaign must report the environment as it really is.
- The whole-repo `uv run pytest -q` must pass on a tree that contains SW-FIX-ALEMBIC. If the Alembic schema tests (`test_single_alembic_head_after_upgrade`, `test_alembic_upgrade_empty_db`, `test_alembic_upgrade_preserves_populated_legacy_rows`, `test_upgrade_downgrade_upgrade`) fail with empty table sets, something in the run removed `SWARM_DATABASE_URL` from the process environment (historically the V20-S11 probe) and Alembic migrated the default `swarm` database. Record the failing tests; the authoritative checks remain the section 6 offline list and `pytest tests/integration -m integration` run separately. Do not STOP for this alone.
- If the campaign exits 1, a probe failed. Do not edit probes. Record the failing `results[].status` and STOP (S3, section 10).

### Step 7 — `docs/v2.3/EXIT_CHECKLIST.md` (create)
Start from the template below. Fill in every `<…>` placeholder from `docs/evidence/v23/acceptance_campaign.json` and `git rev-parse HEAD`. If an item's evidence test is missing or failing on your tree, change its status to `not done` and say why. **Never** mark item 16 done. If the V20-E10 gate is `fail`, write `not done — gate fail` with the failing step and the follow-up owner; if it is `pass`, say where it ran (dev VM or operator host). For `<splitsignal adapter status>`: run `git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/providers/splitsignal_client.py && echo MERGED || echo NOT_MERGED`; write `done (fake SplitSignal); live pending SW-X2-S1 (SP4)` if MERGED, else `pending: SW-X1-S1 not merged (gate SP1)`.
```markdown
{{FILE:docs/v2.3/EXIT_CHECKLIST.md}}
```

### Step 8 — status and agent docs (edit in place; keep each file's existing structure)
- **`docs/v2.3/STATUS.md`** — replace the whole body with:
  - title: `# SwarmAI V2.3 Status — implementation-complete candidate (NOT accepted)`;
  - tip SHA and schema head;
  - one line per gate, copied from `acceptance_campaign.json` `gates`;
  - a link to `EXIT_CHECKLIST.md`;
  - a "Not claimed" list copied from the checklist.
  - Remove the old unsupported "implementation-complete (local)" claim (F-09).
- **`docs/v2.0/STATUS.md`** — update `Tip`, `Schema head` (the new constant) and the last "Not claimed" bullet: E03–E06 and E08–E10 are now implemented with evidence; E07's live run and E11 stay open.
- **`docs/agents/CURRENT.md`**:
  - front-matter `verified_at` becomes now (UTC);
  - `pause:` and `v20_work:` take whatever SW-W0-S1 recorded the owner decided (do not invent);
  - the `refs` table gets a new `origin/cursor/sw-v23-integration-460c` row with the SHA/subject of your base (keep the `origin/dev` row unchanged) and `alembic_head` = the constant;
  - in `version_flags`, add rows `v23_impl_complete_candidate | true` and `v23_accepted | false`;
  - keep every `versions_accepted.*` as `false`.
- **`docs/agents/context.json`** — mirror the same values under `refs`, `version_flags` and `remaining_eng`. It must stay valid JSON: `python3 -m json.tool docs/agents/context.json >/dev/null`.
- **`docs/agents/RESUME.md`** — the next step becomes "Codex review of the V2.3 candidate range on `cursor/sw-v23-integration-460c`; SW-X2-S1 (SplitSignal live smoke, SP4–SP6); owner merges `cursor/sw-v23-integration-460c` into `dev`; owner decision on the V23-A11 multi-process gate (SW-PREAPPROVAL-A5)".
- **`docs/agents/V20_TODO.md`** — tick E03–E06 and E08–E10 with PR links. E07 is "implemented; live run via SplitSignal is SW-X2-S1 (<live_router_free_route gate value>)"; E11 is deferred.
- **`CHANGELOG.md`** — add a new top section, `## [Unreleased] — V2.3 implementation-complete candidate (<date>)`, with Added / Fixed (F-01, F-13, F-14, F-16) / Evidence / Notes. Notes: "Not accepted. Multi-process gate pending owner approval. Zero spend." Do not edit older sections.
- **`README.md`** — replace the stale "V0.9 hardening" label (F-12) with "V2.3 implementation-complete candidate (not accepted)". Add a two-line "V2.3 operator commands" pointer to `swarm v23 --help` and `scripts/v23_acceptance_campaign.py`.

Wording rules for every doc:
- Use exactly one of these words per claim: *proposed, implemented, tested, independently reviewed, live verified*.
- "Accepted" appears only in the negative.
- Unknown cost is written "unknown", never "$0". The campaign's `spend_usd: 0.0` is justified by "no provider calls".

### Step 9 — final verification
```bash
uv run pytest tests/release tests/acceptance -q
python3 -m json.tool docs/agents/context.json >/dev/null && echo JSON_OK
grep -rniE "v2\.3[^|]*accepted" docs/v2.3 docs/agents CHANGELOG.md README.md | grep -viE "not accepted|accepted: *false|v23_accepted \| false|never|no version" || echo NO_FALSE_ACCEPT_CLAIMS
```
