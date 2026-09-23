# ART-V23-PORTABILITY — project export/import bundle contract

Status: drafting
Target: V2.3
Owner: ChatGPT lead

## Goal

Move or back up a project between compatible SwarmAI installations without moving live authority/secrets accidentally.

## Export bundle

Manifest:
- bundle_version
- created_at
- source SwarmAI version/schema versions
- project_id + project config (secret-free)
- mission/history manifest
- artifact metadata/content hashes or portable artifact refs
- accepted knowledge/provenance/tombstones
- extension manifests/config (secret refs only)
- qualification/profile refs if portable
- event/audit range included
- content digests
- encryption/storage policy metadata

Explicitly EXCLUDE:
- raw provider/API credentials
- browser cookies/session state
- worker membership tokens
- active leases
- current site authority epoch
- unexpired approvals unless exported only as inert audit history
- live provider quota reservations
- machine-specific secret paths

## Import

1. validate bundle digest/version;
2. inspect compatibility;
3. map project identity according to explicit operator choice;
4. import data into staging;
5. validate artifact/knowledge references;
6. extensions incompatible -> disabled, not best-effort loaded;
7. approvals/leases/reservations import as historical/non-active only;
8. new install generates its own identity/site epoch/worker credentials;
9. activate project after integrity report.

## ID collisions

Default:
- preserve mission/artifact/knowledge IDs inside a newly mapped project namespace when safe;
- detect conflict and require deterministic remap manifest rather than overwrite.

## Evidence

- export project A, import into clean installation;
- no raw secrets in bundle;
- missions/artifacts/knowledge reopen;
- deleted/tombstoned knowledge stays deleted;
- incompatible extension disabled;
- no active worker/provider/tool authority appears after import;
- project B on target unaffected.
