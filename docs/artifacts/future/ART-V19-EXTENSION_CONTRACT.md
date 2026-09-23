# ART-V19-EXTENSION-CONTRACT — stable capability extension interface

Status: drafting
Target: V2.0 candidate / V1.9 capability group
Owner: ChatGPT lead
Depends on: V1.7 tool/permission contracts

## Extension kinds

- provider adapter
- task-family handler
- tool/integration adapter
- worker capability
- evaluator/scorer
- artifact processor

## Manifest

Every extension declares:
- extension_id
- extension_version
- kind
- SwarmAI API compatibility range
- config schema version
- required permissions/scopes
- network/filesystem needs
- data/privacy classes
- entry point
- deterministic capability claims
- optional live capability claims (never trusted without evidence)
- migrations
- test contract version
- license/source metadata

## Loading

- explicit install/enable only;
- validate manifest before import;
- no permission expansion beyond operator/project policy;
- extension failures are isolated and reported;
- extension cannot self-mark routable/qualified;
- secrets are references, never stored in manifest.

## Compatibility

Semantic compatibility:
- patch: bugfix, no contract change;
- minor: additive compatible contract;
- major: breaking contract.

Core must reject unsupported ranges rather than best-effort execute.

## Session B packets

- V2B-019a SP2: manifest models/validation.
- V2B-019b SP2: entry-point registry for one extension kind.
- V2B-019c SP2: migrate one built-in tool/provider behind interface.
- V2B-019d SP2: install/disable/compatibility tests.

## V1.9 beta relation

External installs must be able to:
- enumerate extensions safely;
- report incompatibility;
- disable extension without corrupting core state;
- produce a secret-safe support bundle.
