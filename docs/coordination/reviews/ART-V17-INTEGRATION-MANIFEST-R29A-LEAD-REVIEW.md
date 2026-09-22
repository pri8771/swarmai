# ART-V17-INTEGRATION-MANIFEST — R29a independent lead review

Date: 2026-09-22
Reviewer: ChatGPT engineering/product lead / formal acceptance authority
Decision: **BOUNDED SLICE ACCEPTED — R29a**
Reviewed exact source: `codex/swarm-r29a-manifests-20260922@1ea1ca55a2470d94fe704d64c029a991c3c0dea5`
Tree: `1b8577c91b2984b804ea6df259e6a47a697ccc31`
Base: accepted R28c `ba458eb1a9a1af5f7e022159f36e6ce296d472cc`
PR: #25
Live/checkpoint acceptance: **NOT GRANTED**

## Exact-SHA verdict

The candidate satisfies the released R29a manifest/version/receipt-binding contract and the lead compatibility clarification `463ee661...`.

### Versioned definitions and identity

The built-in manifests are now file-backed and strict:
- `local.sandbox@1`
- `mcp.echo@1`
- `browser.session@1`

There are no compatibility aliases for the accepted-base `@1.0` / `api.mcp.echo` identities and no historical approval upgrade. Current callers/tests explicitly use the new identities.

`AdapterManifest` has the frozen 14-field V1.9-subset vocabulary. Manifest-level side-effect classification is removed; per-operation declarations remain authoritative. Operation risk cannot exceed the manifest ceiling.

Built-in adapters accept validated manifests and reject a foreign adapter class. Inline `AdapterManifest(...)` construction is removed from the built-in adapter modules.

### Loading, digest and secret guard

`load_manifest` validates strict content and filename/content identity. `load_all` rejects duplicate identity even across subdirectories.

`manifest_digest` is SHA-256 over canonical model JSON with sorted keys and compact separators.

The secret-like guard recursively scans string keys and values using the released regex.

### Dynamic legacy manifest

`LegacyToolCallAdapter` remains generated from the injected legacy capability registry rather than inventing a static operation catalogue. It uses the new schema, preserves operation scopes including literal `network` authority for network tools, and its canonical manifest is digestable by the same gateway path.

### Receipt provenance and historical compatibility

`ActionReceiptV17.manifest_digest` is required with no default. New gateway receipts receive the canonical digest of the exact resolved adapter manifest.

Durable historical JSONB readback uses the approved explicit marker `historical-unbound` only when the persisted payload lacks the key. The compatibility helper copies the payload before validation; it does not mutate/backfill storage or compute a current digest for a past action.

The PostgreSQL regression verifies both a new real digest-bearing receipt and non-mutating historical readback.

The marker is provenance state only; this acceptance does not make it equivalent to a real digest for future binding checks.

### Runtime sandbox root boundary

The local sandbox manifest binds the declared integration definition and default filesystem scope. An explicitly injected adapter root remains runtime instance configuration and is not separately digest-bound in this slice. That limitation is documented and is not expanded into R29a resource-scope enforcement.

## Evidence considered

Native evidence at `codex/portfolio-review-20260922@a04dd5b5c3ac7d830d21a40af12c22c47014efd4` reports:
- **612 tests passed, 0 skipped** with actual disposable PostgreSQL;
- 19 focused manifest checks;
- 35 compatibility checks;
- exact-source migrated permission path: one effect, one new digest-bearing durable receipt, one consumed approval, cleanup zero;
- Ruff clean;
- mypy clean across 173 source files.

The first full run's 41 failures are retained. Evidence attributes them to four old-signature test-helper files; the final candidate's second commit changes only those test files and the settled full run is green. Production behavior was not weakened to restore the old signatures.

This lead review independently inspected the exact two-commit diff, manifest files/schema/loader, built-in adapters, dynamic legacy manifest, gateway receipt construction, durable historical readback and focused PostgreSQL regression. It did not rerun the 612-test suite.

The exact-source hosted workflow has three failed jobs with no exposed executable steps. No hosted-green claim is made and no billing/rerun action is authorized.

## Scope boundary

This accepts only R29a engineering at exact SHA `1ea1ca55a2470d94fe704d64c029a991c3c0dea5`.

It does **not**:
- grant live/checkpoint/product acceptance;
- add trust/signatures/install lifecycle;
- authorize CP1 attempt3, provider/model/public actions, spend, merge, deployment, scheduler changes or Fable routing.

## Scheduling decision

R29a's acceptance satisfies the native dependency for R28d.

**R28d-1 is RELEASED TO CODEX** as the bounded adapter-operations half of the native split, based exactly on this accepted R29a SHA.

R28d-1 covers only `local.sandbox` `fs.write_text` and `proc.run` operations, path/command confinement, observations/outcomes and focused adverse tests. Mission `RepoWorker` wiring and the packet's real $0 brokered local mission remain held for R28d-2 and require a separate exact-SHA R28d-1 lead review/release.

No model/provider/live mission is authorized by this release.
