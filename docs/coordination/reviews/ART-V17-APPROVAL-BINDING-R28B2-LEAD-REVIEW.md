# ART-V17-APPROVAL-BINDING — R28b-2 independent lead review

Date: 2026-09-22
Reviewer: ChatGPT engineering/product lead / formal acceptance authority
Decision: **BOUNDED SLICE ACCEPTED — R28b-2 (native rules 4–6)**
Reviewed exact source: `codex/swarm-r28b2-authority-20260922@a06b8a82925daa4dd08a137cb1eb724aaa2d4efb`
Tree: `20a1c9b5ea240c009d41c5a5effb1c075aa78a70`
Base: accepted R28b-1 `2ebaa5a0cd64b2de665202c5cf9db0dd4f0a1510`
PR: #23
Live/checkpoint acceptance: **NOT GRANTED**

## Exact-SHA verdict

The candidate closes the released actor/policy/fence authority gaps without moving durable lease ownership into tools.

### Authenticated actor/project boundary

The gateway now requires an explicit `ActorContext` on execution/reconciliation and checks project and actor before policy, fence, effect-store reservation or adapter execution. Approval creation is likewise bound to context.

The retained pre-repair forged-actor diagnostic is therefore repaired at this SHA. Negative tests show wrong-project/forged-actor denial with zero adapter calls and no effect row.

### Explicit policy authority

The gateway no longer uses constructor-owned project/scope authority. `PolicyProvider` supplies the current policy version and effective scopes for the authenticated project/actor/integration. The gateway requires:
- current policy version;
- declaration scopes UNION caller-requested scopes to be contained in policy effective scopes.

Policy/scope denial occurs before fence/effect boundaries. The resolved mechanical policy-order finding is covered by tests that use forbidden fence/store sentinels.

### Explicit fence authority and committed recheck

`FenceProvider.current` is the pre-admission authority source. `LeaseFenceProvider` delegates durable reads to `db/lease_fencing.py`; tools code does not query worker tables.

The new `read_current_fence` validates project/mission/task/attempt binding under read locks for the precheck. At committed admission, `LeaseFenceProvider.reader` deliberately delegates to the existing `LeaseLifecycleService.read_effect_fence`, preserving the established mission -> worker lease -> attempt lock order and the full expiry/revocation/active-lease checks.

The real-PostgreSQL cancellation-race regression bumps cancellation after precheck/reservation and before `begin_execution`; committed admission fails closed, adapter calls remain zero, approval use remains zero, and the effect remains only reserved.

`FenceState.authority` is reserved but ignored by V1.7; a test proves future authority fields do not alter current behavior.

## Evidence considered

Native evidence at coordination commit `99a7b2c736abf45335e63f41eb602825796a1c6f` reports:
- **578 full tests passed in 43.76s** with actual disposable PostgreSQL;
- 19 new authority checks;
- 66 gateway compatibility checks;
- 71 affected PostgreSQL compatibility checks;
- Ruff clean across source/tests;
- mypy clean across 171 source files.

Raw initial setup failures and the resolved policy-order finding are retained rather than rewritten.

The exact-source CI supplement `3389fab06ea1c771b1fdac3475385033af4fb4f1` records two hosted runs / six jobs with runner_id 0 and zero executable steps. GitHub annotations explicitly report the account payment/spending-limit gate. Hosted CI is therefore neither green evidence nor an observed source-test failure; no billing change/rerun is authorized.

This lead review independently inspected the exact one-commit diff, authority/provider code, DB fence reader, gateway order, native packet, adverse tests and evidence. It did not rerun the 578-test suite.

## Scope boundary

This accepts only R28b-2 rules 4–6 at exact SHA `a06b8a82925daa4dd08a137cb1eb724aaa2d4efb`.

It does **not**:
- accept the parent approval/tool artifacts;
- grant CP/live/product acceptance;
- waive hosted CI/account, live, host or elapsed gates;
- authorize CP1 attempt3, provider/model/public actions, spend, merge, deployment, scheduler changes or Fable routing.

## Scheduling decision

With R28b-1 and R28b-2 independently accepted, native R28b is engineering-complete at the reviewed stack.

**R28c is RELEASED TO CODEX** based exactly on `a06b8a82925daa4dd08a137cb1eb724aaa2d4efb`.

R28c must follow the existing native packet: introduce AdapterRegistry, route V1.7 by integration id/version, remove process-local legacy side-effect dedupe, and force legacy side-effecting calls through the V1.7 durable boundary. No plugin discovery or frozen-protocol change.

R28d remains held pending independent exact-SHA R28c review.
