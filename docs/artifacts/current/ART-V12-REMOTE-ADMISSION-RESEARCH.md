# ART-V12-REMOTE-ADMISSION-RESEARCH — remote route admission research

Status: lead research draft, 2026-09-20. This is public-document research, **not** account-specific authorization, authentication proof, current quota proof, or permission to call a provider. `ART-V12-PROVIDER-ELIGIBILITY` remains the account-specific source of truth and currently reports zero admissible remote routes.

## Purpose

Reduce W-121A/W-121B ambiguity by identifying the smallest evidence set Cursor must obtain for two exact remote routes without risking spend. No provider is admitted from public documentation alone. Every chosen route still needs current account/tier verification, exact model identity, actual auth, current quota/health, privacy suitability and a bounded zero-charge canary before G12 remote inference.

## Candidate 1 — OpenRouter Free plan / exact `:free` route

Public evidence checked 2026-09-20:

- OpenRouter pricing: https://openrouter.ai/pricing
  - Free plan lists API access, 25+ free models, four free providers, 50 requests/day and **no payment options** on the Free plan.
- OpenRouter support: https://openrouter.ai/support/
  - `:free` is the static model variant for a free model with low rate limits.
- Example exact model page: https://openrouter.ai/poolside/laguna-s-2.1:free
  - page labels the route free / zero prompt and completion price and documents tool calling support.

### Required account-specific evidence before admission

1. Browser/dashboard confirms the authenticated account is actually on the Free plan and no paid fallback/credit-funded route will be selected.
2. Select one exact current `model:free` identifier from the account/API model list; do not use a generic auto-router for the proof.
3. Record public pricing snapshot for that exact route showing zero input/output token price.
4. Record current account request/quota state when available; otherwise reserve conservatively under the published Free-plan daily limit.
5. Execute one bounded non-sensitive canary through the exact free route only after steps 1–4. Receipt must bind provider, account alias, route/model, timestamp, status, token counts if available and observed cost = 0 / no credit debit.
6. Disable provider/model fallback for the canary and G12 overlap proof unless each fallback route is independently admitted.
7. Free endpoints may have different data policies/providers; G12 proof should use non-sensitive synthetic/public tasks unless the selected route's privacy policy is independently approved.

Verdict: **high-priority candidate for fresh admission**, not currently admitted.

## Candidate 2 — Groq Free plan / one exact model

Public evidence checked 2026-09-20:

- Groq rate limits: https://console.groq.com/docs/rate-limits
  - documents organization-level RPM/RPD/TPM/TPD and current example model limits; exact account limits must be read from the account Limits page/headers.
- Groq billing FAQ: https://console.groq.com/docs/billing-faqs
  - explicitly describes upgrading **from the Free tier** to Developer tier and says a valid payment method is required to upgrade.
- Groq community FAQ staffed by Groq: https://community.groq.com/t/do-i-get-charged-for-anything-on-the-groq-free-plan/832
  - states Free Plan usage is not charged and exceeding free limits yields rate-limit failure rather than a charge. This is supporting evidence, not a substitute for the account's actual tier.

### Required account-specific evidence before admission

1. Authenticated Groq console proves current organization/account is still on Free tier and has not been upgraded to Developer/paid tier.
2. Choose one exact model currently available to that organization and record its account-specific RPD/RPM/TPM/TPD from Limits or response headers.
3. Confirm no service tier flag such as paid-only Flex is requested. G12 should use the ordinary free-plan path only.
4. Execute one bounded non-sensitive canary. Receipt must bind provider, account alias/org alias, exact model, timestamp, request/status, rate-limit headers and observed billed amount/no-charge evidence available from the account.
5. Treat 429 as honest quota exhaustion; never auto-upgrade or retry onto a paid service tier.

Verdict: **high-priority candidate for fresh admission**, not currently admitted.

## Candidate 3 — Gemini API Free tier / exact Flash model

Public evidence checked 2026-09-20:

- Gemini API rate limits: https://ai.google.dev/gemini-api/docs/rate-limits
  - defines a Free usage tier and distinguishes it from paid tiers requiring a linked billing account.
- Gemini Developer API pricing: https://ai.google.dev/gemini-api/docs/pricing
  - current pricing tables list zero-cost input/output for several Flash-family models on Free tier; availability is model-specific.
- Gemini 3 guide: https://ai.google.dev/gemini-api/docs/generate-content/gemini-3
  - says `gemini-3-flash-preview` and `gemini-3.1-flash-lite` have Gemini API free tiers; Pro preview does not.
- Deprecations: https://ai.google.dev/gemini-api/docs/deprecations
  - use this before choosing an older Flash route; do not admit a retired preview/model.

### Required account-specific evidence before admission

1. Verify the exact Google AI project/key is a Free-tier project with no paid-tier/billing route active for the selected API use.
2. Select an exact currently supported model whose current pricing page explicitly has Free-tier input/output at zero cost.
3. Record the project's current rate-limit/quota state for that model.
4. Use standard text generation only for the canary; do not enable grounding, maps, image generation, context features or other tools unless their zero-cost eligibility is separately proven.
5. Execute one bounded non-sensitive canary and bind account/project alias, exact model, timestamp, quota/error state, usage and observed zero-charge result.

Verdict: **candidate after exact project/tier verification**, not currently admitted.

## G12 admission checklist — must be true for each remote

A route is `admissible` only if all boxes are evidenced and current:

- [ ] account alias and provider are known without storing private identity in Git;
- [ ] current authenticated account/tier is verified;
- [ ] exact model/route identifier is fixed;
- [ ] current public/account price evidence establishes zero additional charge for this exact route/use;
- [ ] no paid fallback, auto-upgrade, Flex/priority/grounding/other billable add-on is enabled;
- [ ] current quota/remaining allowance or a conservative reservation is recorded;
- [ ] current health/inference canary succeeds;
- [ ] canary evidence shows observed charge/credit effect is zero or otherwise proves no charge under the account tier;
- [ ] privacy/data policy permits the G12 test payload;
- [ ] broker route is configured to fail closed rather than choose an unadmitted alternative;
- [ ] evidence is fresh enough for the G12 run and bound to exact config/candidate.

## Recommended order

1. **OpenRouter exact `:free` route** — clearest public zero-price route and Free-plan API allowance.
2. **Groq Free plan exact model** — strong second candidate if account Free tier is verified.
3. **Gemini exact Flash Free-tier model** — useful fallback/third route after project/model tier is verified.

This order is about minimizing admission ambiguity, not model quality. G13 decides task fitness; G12 only proves governed concurrent inference capacity.

## Stop conditions

Stop route admission immediately if the account is paid-tier without a technically enforced no-charge route, public/account price is ambiguous, quota/charge prevention cannot be established, the route auto-falls back to paid capacity, or the test would expose private repository/customer data outside approved policy.
