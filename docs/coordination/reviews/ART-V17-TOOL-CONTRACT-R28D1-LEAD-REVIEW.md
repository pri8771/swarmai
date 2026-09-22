# ART-V17-TOOL-CONTRACT — R28d-1 independent lead review

Date: 2026-09-22
Reviewer: ChatGPT engineering/product lead / formal acceptance authority
Decision: **BOUNDED SLICE ACCEPTED — R28d-1**
Reviewed exact source: `codex/swarm-r28d1-local-sandbox-20260922@a2cfb3c1d5e326a1b15d7d23cfe3c91ea2e40bf4`
Tree: `d4a76d4f697194fc649b16edc00fdeb3eeb1ad9b`
Base: accepted R29a `1ea1ca55a2470d94fe704d64c029a991c3c0dea5`
PR: #26
Live/checkpoint acceptance: **NOT GRANTED**

## Exact-SHA verdict

The candidate satisfies the released R28d-1 adapter-operations/confinement slice.

### File effect

`local.sandbox@1` now declares `fs.write_text` as idempotent/low with `fs.worktree` scope.

The adapter requires an explicit injected root. File paths must be relative, cannot contain a `..` component, and are resolved under the injected root. Absolute paths and resolved symlink escapes fail with `AdapterDeniedError("path_outside_root")` before the write. The implementation re-resolves after parent creation before mutation.

Pre-observation records the existing file SHA-256 or null; post-observation records SHA-256 and byte count.

The retained red diagnostic demonstrates the accepted R29a adapter could follow a root symlink into a sibling owned temporary directory. The repaired regression proves the represented lexical/absolute/existing-symlink escape cases do not mutate the outside target.

This slice does not claim a hostile concurrent filesystem race proof beyond the released path-resolution contract; R28d-2 must not weaken this confinement.

### Process effect

`proc.run` is idempotent/low with `proc.test` scope.

The adapter accepts an argv list and positive timeout only. Execution:
- uses the injected root as cwd;
- uses `shell=False`;
- requires one of the exact released argv prefixes;
- does not execute a command that fails the allowlist;
- records full stdout/stderr SHA-256;
- exposes only 4096-byte tails;
- treats a nonzero process exit as an explicit successful adapter execution with the exit code available to the caller.

The default allowlist exactly matches the released packet and contains no push/merge shell path.

Runtime root and command allowlist remain instance configuration, not new manifest/trust identity.

## Evidence considered

Native evidence at `codex/portfolio-review-20260922@0df1c74260c218fd440100b38cd00a0d8ff92bc9` reports:
- 42 focused compatibility passes with 14 environment skips;
- 46 affected real-PostgreSQL compatibility passes, cleanup zero;
- full offline: 411 passed / 208 DB-dependent skips;
- full actual PostgreSQL: **606 passed / 13 existing environment skips / 26.78s**, cleanup zero;
- Ruff clean;
- mypy clean across 173 source files.

The first compatibility run's two failures from the removed `write_text` name and old sandbox scope/error expectation are retained; callers were migrated explicitly rather than restored through an alias.

This lead review independently inspected the exact one-commit diff, manifest, adapter implementation, confinement/process tests and native evidence. It did not rerun the 606-test suite.

The exact-source hosted workflow again has failed jobs with no executable steps; no hosted-green claim is made.

## Scope boundary

This accepts only R28d-1 at exact SHA `a2cfb3c1d5e326a1b15d7d23cfe3c91ea2e40bf4`.

It does **not**:
- wire RepoWorker or MissionRuntime;
- run/accept the R28d live_local mission;
- grant CP/live/product acceptance;
- authorize CP1 attempt3, provider/model/public actions, spend, merge, deployment, scheduler changes or Fable routing.

## Scheduling decision

**R28d-2 ENGINEERING is RELEASED TO CODEX** from this exact accepted SHA.

Because the current owner constraint keeps provider/model execution held, the released R28d-2 assignment covers operational RepoWorker/MissionRuntime wiring, receipt propagation and deterministic/real-local no-model engineering verification only. The packet's brokered `live_local` mission remains a separate held evidence step until an applicable live/model grant is explicitly active for that run.

No R28d parent completion may be claimed until the R28d-2 engineering SHA is independently reviewed and the required live_local evidence gate is genuinely satisfied.
