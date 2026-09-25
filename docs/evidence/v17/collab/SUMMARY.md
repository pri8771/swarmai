# V1.7 collaborative mission + X→Y handoff (Lane A residual)

**Date:** 2026-09-25  
**Branch:** `cursor/v17-connector-collab-e2e-b28d`  
**Hostname:** `swarm.splitsignal.ai`  
**Spend:** $0

## Proven

| Item | Evidence |
|---|---|
| Collaborative messages (help/evidence) on one mission | `collab.py` + campaign board dump |
| X→Y context handoff digest + generation bump | handoff `context_digest`, `agent_y` generation ≥ 2 |
| Authority not expanded by message text | rejection of `expand_budget` / self_accept language |
| Predecessor claim fenced after adopt | continuous connector campaign |
| Successor claim → renew → submit pending | lease path; `acceptance_state=pending` |
| Not one-shot self-approve | `one_shot=false`, `self_accepted=false` |

## Commands

```sh
uv run pytest tests/mission/test_v17_collab_handoff.py \
  tests/mission/test_v17_collab_connector_campaign.py -q
uv run python scripts/v17_collab_connector_campaign.py
```
