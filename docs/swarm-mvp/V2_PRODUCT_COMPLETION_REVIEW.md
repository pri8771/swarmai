# Cursor completion review — 2026-09-25

## Verified baseline and conclusion

Reviewed `pri8771/swarmai` dev at `4444a565cbe71dbf5f013e9bd6510c68c257e4b3`, including the merged portability stack #53–#58. GitHub remote and Cursor's SwarmAI project both report that tip. Main remained `08b910f981eff2ab66873a71055090f2c60f2a91`. This is a focused review of the latest portability changes and their integration with goal pursuit, not a claim that every historical module was audited.

The portability round is merged. The product is **not yet an accepted V2.0**. Source contains substantial V1.7–V2.0 scaffolding, contracts, UI and tests, but the operational pursuit path still manufactures success. The package version is `1.0.0rc1`; roadmap labels are capability milestones and must not be confused with the package version. No earlier accepted capability version was established by this review.

Next assignment: `V2_PRODUCT_COMPLETION_PLAN.md`, with machine-readable dependencies in `V2_PRODUCT_COMPLETION_PACKETS.json`.

## Independent checks

Fresh isolated checkout; generated temporary data; no external inference, credentials, deployment or spend.

| Check | Result |
|---|---|
| Portability, portable roles, continuous connector, acceptance, portable install tests | 77 passed, 1 skipped |
| Goals, pursuit, goal SDK tests | 21 passed |
| Total focused pytest results | **98 passed, 1 skipped** |
| Docker test | Not rerun; its default opt-in skip is included above |
| Additional review probes | Six recorded probes; multiple defects reproduced |
| Full suite, PostgreSQL integration, browser E2E, actual cross-host execution | Not rerun in this review |

Commands (from repository root):

```sh
uv run pytest tests/portability tests/workers/test_portable_roles.py tests/workers/test_continuous_connector.py tests/acceptance tests/deployment/test_portable_install.py -q
uv run pytest tests/goals tests/pursuit tests/sdk/test_goal_client.py -q
uv run python scripts/review_v2_product_completion.py .
```

The first suite was initially invoked with a sibling checkout's installed Python; pytest's configured `pythonpath` selected this checkout's source. Its subprocess checks created this checkout's locked uv environment. The second suite and probes used that environment. Evidence: `docs/evidence/v20-product-review/independent-probes.json`. The probe script reports observations, not a regression suite that should permanently expect broken behavior.

## Findings, ordered by priority

### R20-01 — P1: operational API can declare achievement without executing a mission

`src/swarm/api/store.py:127` explicitly constructs `RecordingExecutor(default_success=True)` regardless of `execution_mode` or `fixture_mode`. `src/swarm/api/routes_v1.py:1595` exposes it through `/v1/goals/{goal_id}/pursuit/tick`. `src/swarm/pursuit/loop.py:23` synthesizes evidence references and criteria satisfaction.

**Reproduced:** an operational app with `fixture_mode=false` returned HTTP 200 and `goal.status=achieved` after a tick; executor was `RecordingExecutor`, and no mission record existed. The source's "deterministic" docstring does not make this safe as an operational default.

**Required:** operational mode must dispatch a real durable mission or report a precise blocked state. Simulation is explicit and cannot produce operational achievement or release acceptance.

### R20-02 — P1: failed work can still satisfy all criteria and achieve a goal

`src/swarm/pursuit/loop.py:350` accepts `outcome.satisfied_criteria` as truth. At line 275 it adds `newly_met` even when verification failed; the later achievement test uses the accumulated set without checking valid verifier evidence.

**Reproduced:** injected executor returned `success=false`, one claimed criterion and no evidence. Verification returned `passed=false` while the goal became `achieved`.

**Required:** only independently validated receipts bound to the exact goal/criterion revision and artifact digest may advance criteria. Worker/model text and failed outcomes cannot do so.

### R20-03 — P1: operational runtime matching and filesystem confinement are incomplete

`src/swarm/workers/continuous_connector.py:74` matches overlapping capabilities rather than requiring all capabilities. A capability overlap also admits conflicting scopes. At line 125 the extract executor discards `work_dir` and reads the task-supplied path directly.

**Reproduced:** an extract-only runtime matched a task requiring `extract` plus `admin`, and matched `secrets.read` despite only having `workspace.read`. A generated input outside the supplied workspace was read successfully and reported completed.

This proves defects at the executor boundary. It is not a claim that an unauthenticated remote attacker has a complete exploit chain. The runtime must enforce grants even when upstream callers also validate.

**Required:** conjunction of all required capabilities, scope authorization and current grants; resolve input artifacts through authorized handles; reject traversal/symlink escapes and revoked grants at effect time.

### R20-04 — P1: pursuit state and clock do not provide persistent autonomous pursuit

`src/swarm/pursuit/loop.py:81` keeps criteria progress, history, deduplication, active missions and commitments in dictionaries. `src/swarm/pursuit/schedule.py:18` defaults to a clock permanently returning zero. API reconstruction only reopens GoalStore, not those dictionaries.

**Reproduced:** pursuit history went from one record to zero after constructing another ProductStore against the same root. Scheduler time was zero and next due was one. Source inspection shows a normal, non-forced subsequent tick stays not-due without an injected clock. A force button is not an autonomous scheduler.

**Required:** persistent cycles, schedules, commitments, lessons and progress; a real clock; a bounded coordinator loop; transactional duplicate prevention and crash recovery.

### R20-05 — P1: enrollment reports unqualified claims as verified

`src/swarm/workers/capability_authority.py` defaults to broad grants when no project policy exists and correctly labels that result `verified=false`. `src/swarm/workers/identity.py:120` swallows support-matrix rejection, then promotes granted capabilities to verified. `src/swarm/api/store.py:1119` derives verification from a nonempty capability list.

**Reproduced:** a worker claiming `code.write` on invented unsupported OS/architecture was enrolled with `capabilities_verified=true` without explicit project policy.

**Required:** distinguish advertised ability, operator permission and proven runtime capability. Unsupported hosts may be inventoried as quarantined/unqualified but cannot receive operational work. Qualification must have current evidence and preserve the authorization result.

### R20-06 — P2: container proof is narrower than its name suggests

`scripts/portable_protocol_proof.py:168` checks environment and GET `/health/live`. The worker container does not enroll, claim, execute, submit or verify a result. `src/swarm/product/portable_protocol.py` separately creates an in-process registry, writes an echo artifact, then directly accepts it. Its "persistent recovery" is configuration bundle export/import.

**Fact:** these are useful configuration, connectivity and contract checks. They do not establish a task traversing the deployed product, nor recovery of an in-flight mission. A green Docker run cannot be cited for those broader claims.

**Required:** retain honest smoke-test labels and add an authenticated product-path campaign using the shipped API, shipped connector, real PostgreSQL, real artifacts and protected verifier.

### R20-07 — P2: product installation and operator control remain incomplete

`docs/install/ENROLLMENT_AND_REVOCATION.md` explicitly records absent operator revoke/drain HTTP and CLI commands. `deploy/compose/worker.yml` bypasses the server volume-initialization entrypoint while starting UID 1000 against a fresh named workspace volume. `Dockerfile` and server compose do not build/package the console.

**Facts:** missing admin controls and UI packaging are visible in source. **Risk to verify, not reproduced here:** fresh worker volume ownership may prevent startup. **Inference:** a clean installation needs a complete operational proof; documentation/config tests alone are insufficient.

## What Cursor improved

- Hostname validation is now configuration-driven.
- The generic worker mount is bounded instead of mounting the entire repository.
- Operational echo/fixture defaults were removed from the connector; unsupported execution is more honest.
- A valid grant without an adapter is now distinguished from missing authorization.
- Installation/reference guides and support statuses are clearer.
- V1.7–V2.0 remain explicitly unaccepted; this distinction is correct.

These fixes should be retained. They do not close the newly reproduced integration defects above.

## Tracking and external gates

Linear was reachable through this reviewer's connector. Searches did not identify the actual SwarmAI project; a text search returned a separate SplitSignal inference project. No issues were created in an uncertain destination. Cursor's own connector auth may differ. Preserve reconciliation entries until an exact existing team/project is verified; do not create a duplicate project or invent issue keys.

No LiveGrant was supplied for this round. Live qualification, public ingress and physical cross-host deployment remain separately gated. They do not prevent implementing and testing the real product with a deterministic provider behind its normal inference boundary.
