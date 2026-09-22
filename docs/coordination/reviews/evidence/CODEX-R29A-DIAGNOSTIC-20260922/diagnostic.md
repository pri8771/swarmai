# R29a baseline diagnostic — 2026-09-22

## Source boundary

- Coordination release: `origin/coordination/swarm-control@8ce9f5ef0069fde2ac4ad708f465612ddb3cb36d`, `docs/coordination/assignments/CODEX_R29A_20260922.md`, `docs/coordination/packets/R29a.md`.
- Accepted source: `ba458eb1a9a1af5f7e022159f36e6ce296d472cc`, tree `8c22e55f11351f567ae7d62b139383179caeb6fa`; worktree clean before/after inspection.
- Pure offline probe only. No DB, provider, model, network, host, timer, source or test mutation.

## Reproduced baseline gaps

`baseline_probe.py`/`.log` shows:

1. `AdapterManifest.model_fields` has 17 old-vocabulary fields versus the released 14-field frozen vocabulary. Old-only fields are `filesystem_allowed`, `filesystem_roots`, `network_allowed`, `scopes`, `secrets_required`, and `side_effect_class`; new fields are absent.
2. `ApiMcpAdapter` and `BrowserSessionAdapter` constructors accept no manifest; both construct `@1.0` manifests inline. `inline_manifest_hits.txt` also finds LocalSandbox and `LegacyToolCallAdapter` inline construction.
3. `ActionReceiptV17.model_fields` has no `manifest_digest`.
4. Registry registration keeps the adapter's live mutable manifest object. The probe changes `network_allowed` after registration and the resolved manifest changes from true to false, demonstrating there is no file/digest binding today. This is diagnostic only, not a claim R29a requires immutable Pydantic models.

## Mechanical implementation map

1. **Contracts** (`src/swarm/contracts/actions.py:135-171`): replace only the six obsolete vocabulary fields; extend adapter-class literals with `http_api`/`http_session`; retain manifest risk as ceiling. Validate every operation risk using explicit rank `low<medium<high<critical`, raising exactly `operation_risk_exceeds_manifest`.
2. **Loader** (`src/swarm/tools/manifests.py`, new): parse JSON then recursively scan every string value (including map keys only if “any string value” is interpreted literally; see ambiguity) before/with strict model validation; verify `path.name == f"{id}@{version}.json"`; sort paths and reject duplicate identity; canonical digest over `manifest.model_dump(mode="json")` with UTF-8 SHA-256 and exact compact separators.
3. **Files**: add the two released JSON files. Their operations must retain existing authority scopes (`sandbox.fs`; `network.https`,`mcp.call`) while `network_scopes`/`filesystem_scopes` describe resource boundaries. Do not substitute allowed origins for authorization scopes.
4. **Adapters**: constructor requires validated manifest and checks exact expected class. Normalization should use the selected `OperationDecl` for scopes, side-effect, and risk. This removes manifest-level classification and preserves `_effective_envelope`/policy checks.
5. **Callers**: production directly constructs only `LegacyToolCallAdapter` (`permission_mission.py:214`); built-in constructors are used extensively in tool and DB tests (see `version_callers.txt`). Update all constructors to load/inject a manifest fixture. Add foreign-manifest negative coverage for all three released adapter surfaces.
6. **Receipt path**: gateway resolves the adapter before admission (`v17_gateway.py:113-135`) and again during reconciliation. Compute the digest from that resolved manifest and thread it through every `_finalize`/`_build_receipt` route, including cancellation, timeout, denial, unknown, reconciliation and success. Replay returns the stored receipt and must not recompute it.
7. **Persistence**: `ActionReceiptRow.receipt` is JSONB and has no digest column (`db/models.py:329-351`); inserts already persist the complete model dump. Therefore no Alembic column migration is mechanically required. However three durable read paths call strict `ActionReceiptV17.model_validate(row.receipt)` (`tools/effects.py:810,822,836`). Existing rows lack a required `manifest_digest`, so a required `str` breaks historical readback. Lead must select JSONB backfill or an explicit legacy-compatible representation; silently calculating the current manifest digest on read would falsify historical binding.
8. **Tests**: add required loader/secret/name/duplicate/foreign/digest/vocabulary cases; extend durable receipt round-trip and replay tests to assert stored digest. Include a legacy receipt readback test once the compatibility decision is made. Preserve R28c test asserting LegacyToolCallAdapter's operation scope includes literal `network`.

## Precise ambiguities requiring resolution

- Required filenames are `local.sandbox@1.json` and `mcp.echo@1.json`, while current identities are `local.sandbox@1.0` and `api.mcp.echo@1.0`. Exact name/content agreement means this is both an ID rename (`api.mcp.echo` → `mcp.echo`) and version change (`1.0` → `1`) unless filenames are corrected. Approval pins and many tests use current identities; choose explicitly rather than aliasing silently.
- Browser constructor must stop inline construction, but no `browser.session@...json` is listed. LegacyToolCallAdapter also constructs inline but is absent from listed surfaces. Either supply/load manifests for both, or scope the exit grep/“remove inline adapter manifest construction” to the three adapter files while explicitly preserving the legacy bridge.
- Required `ActionReceiptV17.manifest_digest: str` conflicts with persisted pre-R29 receipts. Backfill requires a historically known manifest; optional/legacy sentinel changes the stated type. This is a lead/schema-contract decision.
- Clarify whether the recursive secret guard scans dictionary keys as well as values. The phrase “string value anywhere” normally excludes keys, but a fail-closed implementation can scan both without broadening the manifest schema.

## Smallest safe order

Resolve identity/browser/legacy/old-receipt choices first; then contract+loader+JSON; inject manifests and operation classification; thread digest through receipt finalization; update focused tests/callers; run tool unit tests, affected PG durable receipts, full offline, Ruff, mypy. No R28d work is implicated.
