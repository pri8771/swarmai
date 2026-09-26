# SW-MERGE-W0 — merge wave W0 session PRs into `cursor/sw-v23-integration-460c`

Copy this whole file into a fresh Cursor session (or give it to the executor agent) on the **swarmai** repository. It is self-contained.

| Field | Value |
|---|---|
| Session ID | `SW-MERGE-W0` |
| Repository | `pri8771/swarmai` (remote `origin`) |
| Target | `cursor/sw-v23-integration-460c` (this prompt is the **only** kind of session that pushes to it) |
| Work branch | `cursor/v23-merge-w0` (local only; append a forced suffix once if your environment requires one) |
| Handoff | `docs/v2.3/sessions/SW-MERGE-W0.md` (committed into `cursor/sw-v23-integration-460c` together with the merges) |
| Reviewer | Codex reviews the merged range (section 8). Merging does not mean accepted. |
| Never | merge into `dev` or `main`; force-push; rewrite history of `cursor/sw-v23-integration-460c`; edit any file other than the handoff |

Re-running this prompt is safe: branches already in the integration tree are detected and skipped. Run it again whenever a skipped session finishes.

## 1. Sessions of this wave (merge in this order)
| # | Session | Branch prefix | Kind |
|---|---|---|---|
| 1 | `SW-W0-S1` | `cursor/v23-w0-s1-tracking-policy` | required |
| 2 | `SW-W0-S2` | `cursor/v23-w0-s2-contracts-schema` | required |
| 3 | `SW-W0-S3` | `cursor/v23-w0-s3-security-hotfixes` | required |

## 2. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (M1)
git fetch origin
git checkout -B cursor/v23-merge-w0 origin/cursor/sw-v23-integration-460c
BASE=$(git rev-parse HEAD); echo "BASE=$BASE"
uv sync && git clean -fdX -- var/
```

## 3. Merge each session, in the order of section 1
For each row, run this block with `P` set to the branch prefix and `ID` to the session ID:
```bash
P=<branch prefix>; ID=<session id>
L=$(echo "$ID" | tr 'A-Z' 'a-z')      # executor naming: cursor/<lowercase id>-<suffix>
git cat-file -e "HEAD:docs/v2.3/sessions/$ID.md" 2>/dev/null && echo HANDOFF_IN || echo HANDOFF_OUT
N=$(git ls-remote --heads origin "$P*" "cursor/$L-*" | wc -l); echo "$ID branches=$N"
B=$(git ls-remote --heads origin "$P*" "cursor/$L-*" | awk '{print $2}' | sed 's#refs/heads/##')
```
- `HANDOFF_IN`: the session was already merged into the integration branch (possibly under another branch name). Record `$ID: already merged` and go to the next row.
- `branches=0`: the session has not pushed. Record `$ID: not pushed` and go to the next row.
- `branches` greater than 1: if the extra names differ only by a re-run suffix `-r2`, `-r3` …, set `B` to the one with the highest number and continue with the `branches=1` steps; otherwise record `$ID: ambiguous branches <names>` and go to the next row.
- `branches=1`: run
```bash
git merge-base --is-ancestor "origin/$B" HEAD && echo ALREADY_IN || echo NEW
git show "origin/$B:docs/v2.3/sessions/$ID.md" | sed -n '/^## Status/,+1p'
```
  - `ALREADY_IN`: record `$ID: already merged` and go to the next row.
  - the Status line contains `BLOCKED`, or the handoff file does not exist: record `$ID: not ready (<status line>)` and go to the next row.
  - otherwise: `git merge --no-ff --no-edit "origin/$B" -m "merge($ID): into integration (Codex review pending)"`. On a conflict: `git merge --abort`, record `$ID: conflict <files>`, and go to the next row.

### 3a. The plan branch (every wave; a no-op once it is merged)
After section 3, check that the plan commit is in the tree:
```bash
git ls-remote --exit-code origin refs/heads/cursor/v23-plan-460c >/dev/null && git fetch origin cursor/v23-plan-460c && (git merge-base --is-ancestor origin/cursor/v23-plan-460c HEAD && echo PLAN_IN || echo PLAN_OUT) || echo PLAN_MISSING
```
- `PLAN_IN` or `PLAN_MISSING`: record it and continue.
- `PLAN_OUT`: `git merge --no-ff --no-edit origin/cursor/v23-plan-460c -m "merge(plan): cursor/v23-plan-460c into integration (Codex review pending)"`. On a conflict: `git merge --abort`, then `git merge --no-ff --no-edit -X ours origin/cursor/v23-plan-460c -m "merge(plan): cursor/v23-plan-460c into integration, integration side kept on conflicting hunks (Codex review pending)"`. The integration side wins because the sessions own those files. Record `plan: merged with -X ours; conflicting files: <git diff --name-only HEAD^1 HEAD>` in the handoff. If this second merge also fails, run `git merge --abort` and STOP (M3).

## 4. Verify the merged tree
```bash
git clean -fdX -- var/
uv sync
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # exactly ONE head
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_merge_w0 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_merge_w0
uv run pytest tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives tests/onboarding tests/product tests/providers tests/recovery tests/regressions tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers tests/workspace tests/e2e tests/acceptance tests/portability -q --ignore=tests/integration
uv run pytest tests/integration -q -m integration
git checkout -- schemas/v1 docs/evidence/fix-004 var
```
If Postgres is missing, install it with the block in section 7 first; if `pg_isready -h 127.0.0.1` still fails after 2 runs of that block, record `integration: SKIPPED (<reason>)`.

If any command fails: run `git reset --hard $BASE` (local work branch only; nothing was pushed), then repeat section 3 **one session at a time**, running section 4 after each merge. Keep every merge that passes. When a merge makes section 4 fail, run `git reset --hard HEAD~1`, record `$ID: fails verify (<first failing test>)`, and continue with the next row. This is the only retry; do not edit code.

## 5. Handoff and push
Write `docs/v2.3/sessions/SW-MERGE-W0.md` with: BASE, the new head, one line per session (merged / already merged / not pushed / not ready / conflict / fails verify), every section 4 result line, and the section 8 packet. Then:
```bash
git add docs/v2.3/sessions/SW-MERGE-W0.md && git commit -m "docs(v2.3): SW-MERGE-W0 handoff"
git push origin HEAD:cursor/sw-v23-integration-460c
git ls-remote origin refs/heads/cursor/sw-v23-integration-460c   # must equal git rev-parse HEAD
```
If the push is rejected because `cursor/sw-v23-integration-460c` moved: `git fetch origin cursor/sw-v23-integration-460c && git merge --no-edit origin/cursor/sw-v23-integration-460c`, run section 4 again, and push once more. If it is rejected again, STOP (M4).

## 6. Wave-complete rule
The next wave may start only when every **required** session of this wave is `merged` or `already merged` in `cursor/sw-v23-integration-460c`. Otherwise report the missing sessions; their owners re-run their prompts, then run this prompt again.

## 7. PostgreSQL
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 4. Section 4 creates a database private to this merge run.

## 8. Codex review packet (put it in the handoff)
```markdown
### Codex review packet — SW-MERGE-W0
- Range: `git log --oneline $BASE..<new head>` on `cursor/sw-v23-integration-460c`; diff `git diff $BASE...<new head>`
- Session PRs merged: <list with PR URLs>
- Review focus: cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"); plus cross-session integration (shared contracts, one Alembic head).
- Verdict requested per session PR and for the range: `RECOMMEND_ACCEPT <sha>` or `REQUEST_CHANGES`.
```

## 9. STOP conditions
- **M1** the working tree is dirty at start (do nothing else; report).
- **M3** the W0 plan-branch merge conflicts.
- **M4** the push to `cursor/sw-v23-integration-460c` is rejected twice.
On STOP: do not push; end with a final message giving the condition, the reason, and the per-session lines collected so far.
