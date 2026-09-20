# V0.1 — Real Mission Runtime

**Date:** 2026-09-20  
**Branch:** `cursor/v0.1-real-mission-runtime`  
**Spend:** `$0.00` (loopback Ollama only)

## Objective
A real software-development mission can be planned, decomposed, executed by isolated git-worktree workers, verified, reviewed, synthesized, persisted, and reported.

## Real proof (dogfood)
| Field | Value |
|---|---|
| Mission ID | `51e8336f6a05404e9e748a8fa6682893` |
| Goal | Fix off-by-one in `sandbox/selfdev_issue/parser_helper.py` |
| Status | **completed / accepted** |
| Model / route | `gemma3:4b` / `rt_ollama_gemma3:4b` |
| Cost USD | `0.0` |
| Tasks | inspect → implement → verify → review (all accepted) |
| Changed files | `sandbox/selfdev_issue/parser_helper.py` (`end - start + 1`) |

### Evidence paths
- `var/missions/51e8336f6a05404e9e748a8fa6682893.json`
- `var/reports/missions/51e8336f6a05404e9e748a8fa6682893/mission-report.json`
- `var/reports/missions/51e8336f6a05404e9e748a8fa6682893/MISSION_REPORT.md`

## Packets
| Packet | Delivered |
|---|---|
| P22 | Structured mission plan + `swarm mission plan/run` |
| P23 | Real `git worktree` isolation + repo workers |
| P24 | Verify commands + review/synthesis + repair rounds |
| P25 | File persistence, live status, machine/human reports, `swarm cost show` |
| P26 | Dogfood mission succeeded |

## Commands
```sh
export OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
export SWARM_ALLOW_PAID=false
uv run swarm mission plan --goal "…"
uv run swarm mission run --goal "…" --model gemma3:4b
uv run swarm mission status --mission-id <id>
uv run swarm cost show
```

## Limitations
- Cloud providers remain unavailable without zero-charge keys.
- Dogfood target was the intentional selfdev sample (legitimate repo bug).
- `swarm release verify` flags local `.env` presence as do-not-ship (gitignored; not staged).
- Competing multi-worker synthesis is single-candidate for V0.1.
- P18 live still skipped.

## Next
Human checkpoint. Do **not** start V0.2 until instructed.
