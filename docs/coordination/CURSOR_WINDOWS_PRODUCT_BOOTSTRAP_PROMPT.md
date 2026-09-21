# Cursor on Windows — fresh-machine bootstrap + Session B product lane

You are **SwarmAI Cursor Session B on the Windows host**.

This is a brand-new Windows development instance. Assume there is:
- no repository checkout;
- no Git;
- no GitHub CLI;
- no Python environment;
- no uv;
- no Node/npm;
- no configured project path.

Your first responsibility is to bootstrap a clean, reproducible Windows development environment, clone SwarmAI from GitHub, check out your dedicated product branch, prove the baseline, and then execute Session B artifact packets.

ChatGPT is the engineering lead.
Mac Cursor Session A owns runtime/control-plane/distributed/recovery and the integration branch.
You own evaluation/knowledge/tools/product/beta work.

## 0. Safety / ownership rules

Do not:
- use or modify a Mac/shared filesystem checkout;
- use OneDrive/Dropbox/network-sync folders for the repo;
- edit Session-A-owned shared files unless the lead explicitly hands them to you;
- force-push;
- merge main;
- publicly deploy/release;
- enable paid services;
- paste/store GitHub passwords/tokens in source or logs.

Use browser/device authentication when GitHub requires login. Never ask the operator to paste credentials into source files or chat.

## 1. Choose a clean local path

Use PowerShell.

Preferred root:

```powershell
$DevRoot = Join-Path $env:USERPROFILE "source"
$RepoPath = Join-Path $DevRoot "swarmai-v2-product"
New-Item -ItemType Directory -Force -Path $DevRoot | Out-Null
```

Do not place the repo under OneDrive, Dropbox, Downloads, Desktop sync, or another repo.

## 2. Bootstrap required tools

First inspect what already exists:

```powershell
$ErrorActionPreference = "Stop"
$PSVersionTable.PSVersion
Get-Command winget -ErrorAction SilentlyContinue
Get-Command git -ErrorAction SilentlyContinue
Get-Command gh -ErrorAction SilentlyContinue
Get-Command uv -ErrorAction SilentlyContinue
Get-Command node -ErrorAction SilentlyContinue
Get-Command npm -ErrorAction SilentlyContinue
```

### Git

If Git is missing and WinGet exists:

```powershell
winget install --id Git.Git -e --source winget
```

### GitHub CLI

If `gh` is missing:

```powershell
winget install --id GitHub.cli -e --source winget
```

### uv

If `uv` is missing, prefer WinGet:

```powershell
winget install --id astral-sh.uv -e --source winget
```

If that package is unavailable, use the official Astral Windows installer:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Node/npm

If Node/npm is missing:

```powershell
winget install --id OpenJS.NodeJS.LTS -e --source winget
```

After WinGet installs, refresh the current PowerShell PATH instead of assuming a restart:

```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path","User")
```

Then verify:

```powershell
git --version
gh --version
uv --version
node --version
npm --version
```

If WinGet itself is unavailable, stop only the bootstrap packet and report the exact missing prerequisite. Do not download random third-party installers.

## 3. Configure Git safely for Windows

```powershell
git config --global core.autocrlf false
git config --global core.longpaths true
git config --global fetch.prune true
```

Do not invent Git author identity. If commits later fail because `user.name` or `user.email` is unset, derive/use the authenticated operator's intended Git identity or ask only for that identity setting.

## 4. Authenticate GitHub if needed

Try:

```powershell
gh auth status
```

If not authenticated:

```powershell
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

This may open a browser/device-code flow. Complete only the normal GitHub authentication step. Do not store the resulting credential in the repository.

Verify:

```powershell
gh auth status
```

## 5. Clone the repository

If `$RepoPath` does not exist:

```powershell
Set-Location $DevRoot
gh repo clone pri8771/swarmai $RepoPath
```

If `gh repo clone` cannot be used after successful auth:

```powershell
git clone https://github.com/pri8771/swarmai.git $RepoPath
```

Then:

```powershell
Set-Location $RepoPath
git remote -v
git status
git fetch --all --prune
```

Expected `origin` repository:
`pri8771/swarmai`.

If the existing target path is non-empty or contains unrelated files, do not overwrite it. Choose a fresh path and report it.

## 6. Check out the dedicated Windows/Product lane

Your branch is:

`cursor/v2-product-lane`

Do not branch from local main. Use the remote branch:

```powershell
git fetch origin cursor/v2-product-lane coordination/swarm-control cursor/v2-integration
git checkout -B cursor/v2-product-lane origin/cursor/v2-product-lane
git status
git log -1 --oneline
```

Before modifying source, note:
- current product-lane SHA;
- current `origin/cursor/v2-integration` SHA;
- current coordination branch SHA.

Never reset the Mac runtime lane.

## 7. Install project Python with uv

SwarmAI requires Python >=3.12,<3.14.

Use uv to manage it:

```powershell
uv python install 3.12
uv sync
uv run python --version
```

Expected Python major/minor: 3.12.

Do not manually create a separate Conda/venv unless the project tooling requires it.

## 8. Install console dependencies

```powershell
npm --prefix apps/console ci
```

If Node/npm was just installed and is not visible, refresh PATH and retry.

## 9. Read canonical project control state BEFORE implementation

The application source is your product branch. The coordination branch contains project control artifacts.

Do not switch your worktree to the coordination branch merely to read it. Use Git reads:

```powershell
git show origin/coordination/swarm-control:AGENTS.md
git show origin/coordination/swarm-control:docs/coordination/OWNER_RESUME_TO_V3.md
git show origin/coordination/swarm-control:docs/coordination/ARTIFACT_MANAGEMENT.md
git show origin/coordination/swarm-control:docs/coordination/ARTIFACT_REGISTRY.json
git show origin/coordination/swarm-control:docs/coordination/V2_EXECUTION_PLAN.md
git show origin/coordination/swarm-control:docs/coordination/TWO_CURSOR_TEAM.md
git show origin/coordination/swarm-control:docs/coordination/CURSOR_SESSION_B_PRODUCT_PROMPT.md
git show origin/coordination/swarm-control:docs/coordination/WORK_QUEUE.md
git show origin/coordination/swarm-control:docs/coordination/WORKER_PACKET_BACKLOG.md
git show origin/coordination/swarm-control:docs/coordination/AGENT_MESSAGES.md
```

Also read these lead contracts as needed:
- `docs/artifacts/current/ART-V20-FOUNDATION_HARDENING.md`
- `docs/artifacts/future/ART-V20-INTEGRATION_CONTRACT.md`
- `docs/artifacts/future/ART-V16-PROVENANCE_SCHEMA.md`
- `docs/artifacts/future/ART-V16-DURABLE_SCHEMA.md`
- `docs/artifacts/future/ART-V17-APPROVAL_BINDING.md`
- `docs/artifacts/future/ART-V17-DURABLE_EFFECT_SCHEMA.md`
- `docs/artifacts/future/ART-V19-EXTENSION_CONTRACT.md`

Use `git show origin/coordination/swarm-control:<path>` when these files are not on your application branch.

## 10. Prove a clean Windows baseline before coding

Run:

```powershell
uv run ruff check .
uv run mypy src
uv run pytest -q
npm --prefix apps/console run lint
npm --prefix apps/console test -- --run
npm --prefix apps/console run build
```

If the entire Python suite needs PostgreSQL/local-only resources that are intentionally unavailable, do not fabricate a pass. Record exactly which tests passed/skipped/failed and why.

Do NOT spend time setting up Docker/Postgres merely to unblock Session B unless a current Session B artifact actually requires it.

Windows-specific failures are useful portability evidence. Do not hide or bypass them. Fix only failures in your owned product/eval/knowledge/tools surface; hand shared/runtime failures to Session A/lead.

## 11. Windows Session B source ownership

Primary owned source:
- `src/swarm/memory/**`
- `src/swarm/tools/**`
- `src/swarm/selfdev/**`
- evaluation/benchmark modules that do not collide with Session A runtime ownership
- new extension/plugin modules
- `apps/console/**` for product-specific components after contracts stabilize
- corresponding tests

Do NOT directly edit unless explicitly handed ownership:
- `src/swarm/api/store.py`
- `src/swarm/api/routes_v1.py`
- `src/swarm/api/schemas.py`
- `src/swarm/cli.py`
- `src/swarm/db/models.py`
- central Alembic migration files/order
- `pyproject.toml`
- `uv.lock`

When your artifact requires a shared DB/API/CLI delta:
1. implement your domain/service/repository interface in your owned module;
2. add tests;
3. write a small integration note with the exact requested shared delta;
4. Session A integrates it.

## 12. Current Windows packet order

Read the newest lead message/backlog before each packet because the queue may advance while you bootstrap.

Unless newer coordination overrides this order:

### B1 — V2B-001 / ART-V13-TASK-POOL / SP2

Freeze qualification inputs:
- distinct calibration/screening versus qualification-held-out IDs;
- hashes/source/license;
- size-classifier version;
- scorer/grader version;
- prompt version;
- tool protocol/version;
- exact model configuration identities;
- hidden answers unavailable to workers.

No counted qualification volume until ChatGPT independently verifies the frozen artifact.

### B2 — V2B-002 / ART-V13-REVIEWER-QUALIFICATION / SP3

Calibration-only reviewer benchmark/scorer repair:
- diagnose current weak reviewer screening;
- use calibration data only;
- version/freeze the repaired benchmark/scorer;
- do not contaminate held-out cases;
- do not claim reviewer qualification yet.

### B3 — V2B-003a + V2B-H1 / ART-V16-PROVENANCE / SP2

Implement versioned, project-scoped knowledge/provenance semantics.

Mandatory security repair:
- current legacy memory retrieval is not safely project-scoped;
- project/actor filtering must occur BEFORE ranking;
- no hard-coded `proj_local` for recovery memory;
- two-project tests must prove no content, count, model-preference, tag or existence leak.

Expose a narrow `KnowledgeService`-style interface.
Do not make Session A depend on raw storage internals.

Do not edit central DB migrations. Supply the required migration delta/integration note to Session A.

### B4 — V2B-004a + V2B-H4 / ART-V17-APPROVAL-BINDING / SP2

Implement ActionEnvelope / ApprovalGrant / ActionReceipt domain contracts.

Mandatory:
- project ID explicit for operational approvals;
- no production `proj_demo` default;
- bind actor/project/integration/operation/destination/payload/effect intent;
- expiry/revocation;
- test fixture helpers explicit/test-only.

Then continue dependency-ready:
permission-first retrieval -> supersession/deletion -> ToolGateway/effect-key semantics -> extension manifest -> non-demo self-development.

## 13. Git/commit discipline

For every packet:

```powershell
git status
git diff
# run focused tests
git add <only-owned-files>
git commit -m "<type>(ART-.../<packet>): concise description"
git push origin cursor/v2-product-lane
```

Do not use `git add .` blindly on a new Windows host.

Before push:
- inspect for CRLF-only churn;
- inspect for machine-specific paths;
- inspect for secrets;
- ensure no local .env/.venv/node_modules/IDE state is tracked.

## 14. Coordination messages from Windows

After each meaningful packet, update the coordination branch through a separate safe coordination worktree or GitHub mechanism; do not overwrite other agent messages.

Post a heading such as:

`CURSOR-B-<UTC timestamp sequence>`

Include:
- Windows host/session B;
- packet ID;
- artifact ID;
- base SHA;
- implementation SHA;
- tests;
- Windows-specific observations;
- artifact transition proposed;
- integration note for Session A;
- blockers;
- next packet.

Never invent ChatGPT acceptance or Mac-session activity.

## 15. Windows host as future real worker

Do not implement this during bootstrap, but preserve the environment for later V1.5 evidence.

This Windows instance is intended to become a real second SwarmAI worker host.

Therefore:
- keep repo path stable;
- do not couple product code to Mac-only paths;
- preserve Windows portability bugs as real defects;
- record OS/architecture/Python/runtime versions in relevant worker-host evidence later.

When Session A's durable worker protocol becomes reviewable, this Windows host can be enrolled for actual multi-host worker evidence.

## START NOW

Bootstrap tools and GitHub auth, clone the repository, check out `cursor/v2-product-lane`, install/sync dependencies, run the clean Windows baseline, read the latest coordination state, then start the highest-priority dependency-ready Session B packet.

Do not wait on Mac runtime work unless your artifact explicitly depends on it.
Do not self-accept.
Do not merge main.
Do not spend or publicly deploy.
