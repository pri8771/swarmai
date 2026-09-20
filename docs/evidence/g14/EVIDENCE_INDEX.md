# G14 / SWARM-141 evidence index

**Tip binding:** `a17ae17e430831eb23d2fafc871244c096ca275d`  
**Live multi-planner claimed:** **false**

| Artifact | Claim | Not claimed |
|----------|-------|-------------|
| `swarm-141/graph-expand-contract-offline.json` | Offline graph expand/contract prep | Live adaptive mission |
| `swarm-141/logical-assignment-10-50-100.json` | Offline 10/50/100 logical assignment prep | 100 reasoning agents |
| `swarm-141/elastic-vs-fixed-offline.json` | Offline elastic vs fixed vs single comparison | Live multi-planner concurrency |
| `swarm-141/evidence-exchange-offline.json` | Offline evidence-exchange prep | Live specialist spawn from evidence |
| `swarm-141/admission-gated-expand-offline.json` | Offline expand under budget → deny at `max_graph_nodes` → retire frees capacity → expand_after_contract; $0 | Live multi-planner concurrency |

**Script:** `scripts/g14_offline_admission_gated_expand_proof.py` (exit 0 locally).  
Note: cancelled nodes still count toward `max_graph_nodes`; retirement removes the node from the task map.

LIVE-142 not started. Requires G10–G14 live-accepted evidence first. No invented live multi-planner.
