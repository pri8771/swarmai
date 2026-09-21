# R04 — G13 current-topology verification

Host: Darwin Mac (CURSOR-V17-SINGLE)

Results:
- `g13_freeze_task_pool_v3.py verify` → OK (240 held-out; 15 archetypes/cell; answer_leak_count=0)
- stats → OK
- ruff/mypy on G13 modules → clean
- pytest freeze+qualify → 11 passed
- SHA256SUMS: all entries match; shard table digest matches manifest

Not claimed:
- ART-V13-TASK-POOL accepted/frozen by lead
- sealed bundle content digest bound (`sealed_bundle_content_digest_bound=false`)
- counted qualification ready (`false`)
