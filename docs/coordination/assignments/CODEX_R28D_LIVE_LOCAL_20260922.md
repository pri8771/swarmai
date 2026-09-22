# Codex assignment — R28d live_local evidence

Date: 2026-09-22
Basis: accepted R28d-2 engineering at 6dbf8c43463cbdbd8c87561af2abcdde59969765.
Owner grant: bounded private incremental-$0 live testing using existing accounts/subscriptions and owned machines.

Run exactly one real brokered local mission on a throwaway target from the accepted source.

Requirements:
- incremental cost must remain $0;
- use a private/local or already-authorized existing-subscription route only;
- no public post/message, real job submission, destructive action, CAPTCHA/MFA bypass, purchase/upgrade or paid fallback;
- do not treat this as CP1 or consume/create a CP1 attempt;
- preserve exact source SHA, route/model identity, request count and recorded cost;
- evidence must include non-empty action_receipt_ids;
- every mission-created/modified file must be matched to an fs.write_text receipt;
- command effects used by the mission must have proc.run receipts;
- preserve the isolated worktree behavior and do not auto-promote changes to the primary checkout;
- package evidence under docs/evidence/v17-recovery/R28d/ and label it live_local;
- record cleanup state.

If a $0 eligible route is unavailable or authentication/MFA/CAPTCHA appears, stop and record the exact blocker rather than changing account state or spending.

Return READY_FOR_LEAD_REVIEW with exact evidence/source refs. No merge, deployment, scheduler change, public action, spend, CP1 attempt3, Fable routing or V1.8+ work.