# Swarm V1.7 engineering return — 2026-09-22 22:01 UTC

Owner task: implement SwarmAI through genuinely accepted LIVE V1.7, then stop.
This is an implementation checkpoint, **not** a live or acceptance verdict.
The owner handoff was read; the dirty main source checkout, existing Cursor
processes, runtime, and other products were left untouched. Work used clean
isolated source worktrees and a disposable socket-only PostgreSQL database.

## Source and review state

PR30 (`4d16fe8`, tree `05d9798`) remains draft/open and has no formal review.
PR31 (`3c79a88`, tree `bc690d6`) and PR32 (`7aa45a0`, tree `d41eb5e`) remain
separate draft children of PR30, also without formal reviews. Their hosted
offline and console checks are green; live-gated notices are not live proof.
No PR was self-accepted or merged.

New draft chain on PR32:

| PR | Exact head | Tree | Completed offline prerequisite |
|---|---|---|---|
| [33](https://github.com/pri8771/swarmai/pull/33) | `9a72e4147be510a2996889a6abd4d750fd6299a3` | `62d221002aef294b24edf78d41255d2be4be2091` | Exact OpenRouter `:free` model/backend, zero-price request controls, no fallback |
| [34](https://github.com/pri8771/swarmai/pull/34) | `4f007684ca14a5b43249adc9eaefcf43af8473f2` | `5fd36fcadfae251d758b3e12535c3b27ae17e5c3` | Broker route-context admission fence |
| [36](https://github.com/pri8771/swarmai/pull/36) | `d4a988b7aeb522b58f23106442976bc0c72c2efa` | `9ca6645f3b6772585c5cb032dd70a3171bf4780e` | PostgreSQL one-use grant, reservation and send fence |
| [35](https://github.com/pri8771/swarmai/pull/35) | `d78971ea6370d14e6616f0b689aee7c7e3241f32` | `955b4588dc1a4ce9eb6be852b3fd00fcd94e901b` | Provider cost, routing and safe rate-limit receipt evidence |
| [37](https://github.com/pri8771/swarmai/pull/37) | `fc563672b6996f13abc92fed405daa8acebd171c` | `9fea1ef43a7194130dff37cbdedce552c417bac8` | Broker remote calls use durable gate, not in-memory quota |
| [38](https://github.com/pri8771/swarmai/pull/38) | `e13efef3a1da11d994863cb5e3ea4c0319d1c5e4` | `281524f021ea11f69bc94ef72055889b6f0b3e1d` | Groq explicit pin/no implicit metadata call, one-broker two-provider HTTP overlap with MockTransport |
| [39](https://github.com/pri8771/swarmai/pull/39) | `37e06f5a321a5aa2d39daa1ea3810f5c486910ad` | `02fbe1f55cefc69294a6e8f30658cd4d9abb32c5` | Clean Git tree attestation and exact attempt binding |
| [40](https://github.com/pri8771/swarmai/pull/40) | `f25eb19e2cd84ab75fcad424e7d7b9ec05a95e2a` | `cf913e49e9171e0d4073cdb19ea114e3ae6d1d32` | Durable request/token/concurrency holds for mission calls |

PR35 was rebased onto PR36 and its body updated; current ordering is
PR30 → PR32 → PR33 → PR34 → PR36 → PR35 → PR37 → PR38 → PR39 → PR40.
PR31 is still the separate R31a child. No source main merge occurred.

PR40 exact-source local checks: 16 isolated-schema PostgreSQL cases passed;
485 offline passed, 4 skipped, 223 deselected; Ruff, mypy (176 source files)
and diff checks clean. The dual-remote test forces both HTTP handlers through
a barrier, but uses synthetic grants/account data and `httpx.MockTransport`.
Hosted PR40 checks were green as of 22:00:47 UTC. No authenticated provider
request, real inference, local Ollama host probe, real dual overlap, account
charge readback, second-host proof, CP1/CP3/CP4/CP5 or R33c action occurred.

## Exact prerequisite access proposal — **not granted**

The owner handoff explicitly holds authenticated provider metadata/session
access and live host probes. Reuse the existing `OPENROUTER_API_KEY` and
`GROQ_API_KEY` references; both names are present and nonempty in the existing
private `/Users/pchordia/Downloads/swarm-ai/.env`. Never print or commit values.
Do not ask for a new account inventory.

Proposed **read-only metadata grant only**, one pass and no inference:

1. OpenRouter: one authenticated `GET https://openrouter.ai/api/v1/key` using
   the existing key. Retain only free-tier flag, key limit/remaining,
   BYOK-limit flag, expiry and timestamp; discard label and user IDs.
2. Groq: read the existing account's tier/Billing and organization/project
   Limits pages on `console.groq.com`, plus at most one authenticated
   `GET https://api.groq.com/openai/v1/models` to check the pinned
   `openai/gpt-oss-20b` model. Retain only tier, model permission, exact
   requests/tokens limits and observation time.
3. Ollama: one loopback `GET http://127.0.0.1:11434/api/tags` to read installed
   model names and host availability. No model generation or download.

No settings change, login credential submission by automation, payment,
model call, paid fallback, public action or scheduler. API calls have a 5 s
timeout and no retry. If a session needs interactive login, stop and report
the exact gate. Raw responses and keys stay out of Git and chat; save only a
redacted field-level receipt in private local evidence. This grant would
authorize observation only; a later bounded inference grant must bind the
reviewed source tree, exact account/model/backend/prompt/output cap,
allowance and expiry separately.

Official endpoint/limit documentation checked today:
OpenRouter [current key](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-key),
Groq [rate limits](https://console.groq.com/docs/rate-limits),
[billing](https://console.groq.com/docs/billing-faqs), and
[models](https://console.groq.com/docs/models).

## Next bounded owner action

Obtain the explicit read-only metadata/loopback grant above. If granted,
perform only those observations, preserve exact redacted receipts, and decide
whether two zero-charge remote routes can be proposed. Formal independent
review of PR30 must precede dispositions on its separate PR31/PR32 children;
the new dependent draft chain then needs independent exact-tree review.
No review request exists on GitHub, and the repository currently lists only
the owner as a collaborator. A green CI run or this return cannot substitute
for a formal verdict. Continue other released Swarm prerequisites while any
external gate waits.

## Independent CP3 evidence locator correction

The separately referenced `cp3-20260922T020141Z` package **does exist** in
source at `docs/evidence/v17-checkpoints/CP3/cp3-20260922T020141Z/` and was
added by `ebe71f237de2536890ef4f29f27e12efb8986641`. Its manifest binds
the run to `e53da7305d138658edfb9bd8f47ebbd140a40a63`; its receipt reports
9/9 harness requirements and 20/20 concurrent duplicate-result wins. The
cancellation generation bump went through `DurableWorkerService.revoke_mission_work`.
The run itself says independent review is pending, no second physical host
was used, and operational product-mission wiring still needs R17b. This
locates the evidence omitted by the earlier coordination disposition; it
does not promote CP3 or authorize another live run.
