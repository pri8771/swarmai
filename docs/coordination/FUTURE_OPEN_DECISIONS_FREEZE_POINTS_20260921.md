# SwarmAI future open decisions and freeze points

Date: 2026-09-21
Status: PLANNING ONLY

These are intentionally NOT decided by prep work. Each has a latest-safe decision point and evidence required.

## D18-01 SiteEpoch fencing authority mechanism

Need:
A restored copy of the application database cannot simply assume it has globally newer authority if the old site may still exist.

Options may include:
- an approved external/shared authority store/lease;
- infrastructure-level fencing plus DB epoch proof;
- another reviewed mechanism.

Do not freeze until:
- target deployment topology is known;
- zero/paid infrastructure constraints are known;
- threat model demonstrates stale-site fencing.

Latest safe freeze:
before V2A-018a implementation becomes candidate-bound.

## D18-02 backup storage/encryption target

Do not assume cloud storage or paid service.

Need:
- actual deployment/storage environment;
- retention requirements;
- encryption/key ownership;
- restore speed target.

Latest safe freeze:
before counted V1.8 recovery evidence.

## D19-01 supported OS/install matrix

Current product can develop across macOS/Linux/Windows, but support claims require real evidence.

Do not promise an OS until clean-install evidence exists.

Latest safe freeze:
V2.0 support matrix.

## D19-02 extension trust/signature mechanism

Need:
- threat model;
- distribution model (local/private/public);
- publisher identity model.

Early versions may rely on exact digest + locally approved source while keeping schema signature-ready.

Latest safe freeze:
before any public/shared capability ecosystem claim.

## D20-01 V2 reliability duration/tolerance

The existing reliability protocol is canonical when frozen.

Do not shorten elapsed windows to meet schedule.

Latest safe freeze:
before campaign start.

## D23-01 fairness acceptance tolerance

Current ART-V23 draft proposes approximately +/-15% after >=200 successful scheduling decisions under controlled equal-cost synthetic load, explicitly as a proposed default.

Freeze or replace before counted V2.3 evidence.
Do not tune after seeing counted results.

## D23-02 normalized service cost function

Need to choose how worker/provider/tool classes map to scheduler service units.

Constraint:
It is a fairness abstraction, not billing and not permission.

Freeze before:
counted fairness workload.

## D23-03 OpenTelemetry adoption

Proposal:
optional traces/metrics exporter only, Swarm-native receipts remain source of truth.

Need:
actual operator observability needs and dependency cost/complexity.

No blocker:
V2.3 can implement normalized observability without OTEL first.

## D23-04 capability pack packaging format

Need:
extension substrate from V1.9, migration needs, portability needs.

Freeze after:
V1.9 extension contract implementation is stable.

## D30-01 schedule missed-run default

Each objective policy must explicitly choose skip_missed, coalesce_latest, or bounded catch-up.

Do not create one universal hidden default that can cause unbounded mission creation.

Freeze:
per objective/template policy.

## D30-02 objective semantic stop conditions

Deterministic predicates are preferred.
If model semantic evaluation is used, it remains advisory until deterministic policy consumes it.

Need:
actual objective use cases before adding semantic stop evaluator.

## D30-03 learning statistical thresholds

Sample sizes/confidence/effect-size thresholds are target-specific.

Do not set universal magic numbers now.

Freeze:
per LearningProposal/evaluation protocol before held-out execution.

## D30-04 canary size/duration

Target-specific by risk and effect class.

Safety-critical rollback triggers must be deterministic regardless of canary size.

Freeze:
before candidate canary begins.

## D30-05 capability publisher trust model

Depends on whether ecosystem is:
- single-owner/private;
- team/organization;
- public third-party.

Schema should support provenance/revocation now; trust policy freezes later.

## D30-06 autonomous promotion authority

Current default:
models propose; software/review accepts according to frozen policy.
No self-release/merge/deploy/spend/permission expansion.

Any future relaxation requires explicit operator governance change, not an inference from V3 completion.

## Freeze discipline

For every open decision:
1. record decision ID;
2. list candidate options;
3. record evidence/input used;
4. freeze before counted evidence;
5. hash/version the selected policy;
6. invalidate counted evidence if the policy materially changes afterward.
