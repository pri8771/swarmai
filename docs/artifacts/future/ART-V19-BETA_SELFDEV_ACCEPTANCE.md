# ART-V19-BETA-ACCEPTANCE — Independent beta and controlled self-development

Status: drafting
Target: V1.9
Owner: ChatGPT lead

## Goal

Prove SwarmAI is usable outside the developer's existing environment and can use itself to prepare a useful change without self-approving security/release decisions.

## External installation artifact

Need two clean installations that:
- start without personal/default credentials;
- show honest empty/unconfigured state;
- follow documented install/upgrade steps;
- validate migrations;
- connect only explicitly authorized resources;
- produce a support bundle without secrets;
- can remove/uninstall local state cleanly.

Record OS/runtime/dependency versions and failures.

## Extension / SDK freeze

Define stable extension surfaces for:
- provider adapters;
- task-family handlers;
- tools/integrations;
- worker capabilities;
- evidence/acceptance hooks.

Each extension contract needs:
- version compatibility;
- permissions;
- configuration schema;
- tests;
- failure semantics;
- migration/deprecation policy.

## Self-development proof

Use SwarmAI on a non-demo repository/problem.

Required:
1. issue/problem selected before execution;
2. no supplied patch/reference answer to workers;
3. swarm creates bounded plan/tasks;
4. code changes occur only in isolated workspace;
5. tests/review run independently;
6. system produces a PR candidate/diff/artifacts;
7. SwarmAI cannot approve its own security/credential/release action;
8. independent reviewer accepts/rejects final candidate;
9. failed attempts remain evidence.

## Beta acceptance

- two clean external installs;
- held-out mission set with declared support;
- real browser/API operator journeys;
- install/upgrade/backup documentation exercised;
- support/known-limit matrix;
- self-development PR candidate independently reviewed;
- hourly worker automation has observed non-overlapping consecutive invocations.

Public release remains a separate owner decision.
