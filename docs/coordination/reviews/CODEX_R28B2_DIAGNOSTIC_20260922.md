# R28b-2 — read-only actor boundary diagnostic

**REVIEW_BLOCKED for implementation: native R28b-2 remains HELD**, no assignment released. R28b-1 exact2ebaa5a0cd64b2de665202c5cf9db0dd4f0a1510 remains submitted PR22, not yet formally accepted. This diagnostic prepares one known rule6 boundary and does not broaden R28b-1 scope or imply that its intentionally excluded feature was claimed complete.

Native R28b rule6 requires authenticated ActorContext before any policy/fence/reservation. Current gateway receives only caller-controlled envelope.actor and checks project/scopes without caller-context binding. A synthetic stop-at-reservation store shows a forged actor passes present checks and reaches reservation; the store raises before admission, begin_execution or adapter execution. No local file effect, PG, credential, provider or model action. [Reproducer](evidence/CODEX-R28B2-DIAGNOSTIC-20260922/reproduce.py), [observed output](evidence/CODEX-R28B2-DIAGNOSTIC-20260922/observed.txt), [causal note](evidence/CODEX-R28B2-DIAGNOSTIC-20260922/causal-note.txt).

Smallest next action: formal exact-SHA R28b-1 verdict, then an explicit native R28b-2 assignment with expected base and context/provider contract. No implementation started, no Fable handoff or original-worker/heartbeat changes. Genuine CP and V2.0 gates remain open.
