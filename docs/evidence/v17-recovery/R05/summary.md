# R05 — reviewer calibration contract

Implemented `g13-reviewer-calibration-v1`:
- reviewer input contract
- calibration dataset (10 labeled cases, all required scenarios)
- deterministic scorer
- contamination guard vs product holdout IDs
- calibration receipt (no qualification claim)

Negatives covered in unit tests: wrong-result accept, forbidden action, stale identity, mock success.
Positive control: correct accept.

No held-out reviewer qualification started. No invent-accept.
