---
doc: agents_v17_done
audience: ai_agent
status: done
eng_claim: true
operator_accepted: false
version_accepted: false
tip: dd7726eb8c22986ef72847994c8e435a81a869b6
verified_at: 2026-09-25T21:07Z
---

# V17_DONE

## verdict

| key | value |
|---|---|
| eng | done |
| false_success_R20-01 | closed |
| mission_path | tip_proven |
| accepted | false |

## packets_prs

| id | type | pr | merge_sha | status |
|---|---|---|---|---|
| L5 | FAST_TRACK | #61 | `c294d8ca` | done |
| L1 | FAST_TRACK | #63 | `3357d944` | done |
| L3 | FAST_TRACK | #62 | `53401981` | done |
| L4 | FAST_TRACK | #64 | `45efb242` | done |
| L2 | FAST_TRACK + R20-01 | #65 | `ad0ed567` | done |
| L6 | FAST_TRACK | #60 | `dd7726eb` | done |

## composition_ops

| mode | executor | cite |
|---|---|---|
| operational (default) | `NativeMissionDispatchExecutor` | `src/swarm/api/store.py` @ tip |
| fixture / mock | `RecordingExecutor(default_success=True)` | fixture/mock gate only |
| no-executor default | `BlockedMissingImplementationExecutor` | tip |

## evidence_commands

```text
git fetch origin dev
git rev-parse origin/dev
# expect dd7726eb8c22986ef72847994c8e435a81a869b6

uv run pytest tests/mission/test_v17_mission_path.py -q
# 3 passed

uv run pytest \
  tests/mission/test_v17_mission_path.py \
  tests/pursuit/test_protected_verification.py \
  tests/mission/test_v17_protected_verify.py \
  tests/pursuit/test_pursuit_durability.py -q
# 17 passed
```

## r20_01_smoke_shape

| field | expected |
|---|---|
| executor | NativeMissionDispatchExecutor |
| outcome_success | false |
| failure_class | submitted_pending |
| mission_status | running |
| goal.status | waiting (not achieved) |

## portable_on_tip

| packet | pr | status |
|---|---|---|
| PORT-01 | #55 | done |
| PORT-02 | #57 | eng_done (cells experimental) |
| PORT-03 | #56 | eng_done |
| PORT-04 | #54 | eng_done |
| PORT-05 | #58 @ `f39e0032` | stale → V20-E01 |

## explicit_non_claims

- not operator-accepted
- not version-accepted V1.7–V2.0
- not LiveGrant / live-qualified
- not public / paid / main-merged
