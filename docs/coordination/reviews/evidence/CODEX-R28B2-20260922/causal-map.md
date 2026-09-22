# R28b-2 pre-edit causal map

Source under diagnosis: `2ebaa5a0cd64b2de665202c5cf9db0dd4f0a1510` (clean). Canonical assignment/packet: `origin/coordination/swarm-control@4fa4bd066c2a6415b4f1f9da84ef895d3882adb7`, `CODEX_R28B2_20260922.md`, `packets/R28b.md` rules 4–6.

The standalone harness `/tmp/swarm-r28b2-authority-red-harness.py` uses the real `ApiMcpAdapter`, gateway, envelope and approval code with a synthetic store that raises exactly on `reserve()`. Each adverse request reached reservation validation, while reservation mutation, `begin_execution`, adapter action, providers, network and PostgreSQL remained untouched. This extends the already-retained forged-actor baseline; it does not rerun or replace it.

## RED-1 — stale policy reaches reservation

Observed: envelope `policy_version=v17-policy-stale` reached `reserve`; adapter calls `0`, effects persisted `0`.

Cause: `ConsequentialToolGateway.__init__` has no `PolicyProvider` (`v17_gateway.py:64-86`). `execute_envelope` has no authenticated context (`:127-140`). `_evaluate_policy` only checks effective risk/approval (`:496-502`). Exact approval compares the approval to the same envelope policy claim (`:543-545`), never to a current project policy.

Small repair seam: inject `PolicyProvider`; before approval/reservation compare envelope version to `current_policy_version(project_id)` and reject `policy_version_stale`.

## RED-2 — scope without actor authority reaches reservation

Observed: actor `worker-no-admin` requested `admin.write` and reached `reserve` because the constructor-wide allow-list included it; adapter calls `0`, effects persisted `0`.

Cause: constructor `allowed_scopes` is the only scope authority (`v17_gateway.py:68-83`). `_authorize_project` checks requested/manifest scopes against that static set (`:484-494`) and has no actor-specific effective-policy lookup. No `ActorContext` exists.

Small repair seam: authenticated `ActorContext`; compute operation-declaration scopes union requested scopes and require containment in `PolicyProvider.effective_scopes(project, actor, integration, version)` before reservation.

## RED-3 — static stale fence reaches reservation

Observed: modeled durable authority `(lease=8,cancellation=4)` was invisible. Envelope `(7,3)` matching constructor constants reached `reserve`; adapter calls `0`, effects persisted `0`.

Cause: gateway stores fixed generation constants (`v17_gateway.py:70-83`) and `_check_generations` compares only envelope claims to those constants (`:547-551`). `src/swarm/tools/fences.py` is absent. The lease module already owns a locked `read_effect_fence` path (`lease_fencing.py:655-712`) and committed reader (`:1596-1607`), but no rule-5 `read_current_fence` provider seam exists for the gateway precheck. The current gateway invokes the committed reader only after reservation and only by directly importing `effect_fence_reader`.

Small repair seam: add the specified `FenceProvider` abstraction and lease-owned `read_current_fence`; use provider `current()` before reservation and provider `reader()` inside committed `begin_execution`. Normalize missing/mismatched mission, attempt and project to `lease_not_current` at the new read-only rule-5 boundary.

## Evidence

- Harness log: `/tmp/swarm-r28b2-authority-red.log`, exit `0`.
- Harness SHA-256: `fe0054de5757c6ca4ef03b535966553e2c85625b141dcf8d16b3046da4dae6a9`.
- Log SHA-256: `2802ff68b53bcd69905e5c0ae53e4ed2b8d27f96697aa08558218355dfc5cfbb`.
- First command attempted the absent worktree-local `.venv` and exited `127`; the retained source-independent environment at `../swarm-source/.venv/bin/python` then ran the exact source successfully.
- No repository writes, database use, provider calls, credentials, external actions or reservations occurred.
