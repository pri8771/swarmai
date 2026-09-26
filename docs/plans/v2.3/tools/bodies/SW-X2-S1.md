**Goal.** Record SwarmAI's side of the joint V2.3 finish with SplitSignal (owner decision D4). One bounded live smoke test proves sync points SP4 (non-streaming) and SP5 (streaming) from SwarmAI's side, and SP6 is checked against inference_server's evidence. The session makes **at most 2 live calls in total**: one run of the script, one text call and one streamed call, each with `max_tokens` 16, on a route SplitSignal lists as free. Zero spend.

**Gates, in order.** Each one is checked before anything touches the network.
1. The environment variables (section 2): `SPLITSIGNAL_BASE_URL` (the public URL + `/v1`), `SPLITSIGNAL_API_KEY`. `SPLITSIGNAL_MODEL` is optional: when unset, the script uses `gemini/gemini-3.5-flash-lite` and records `model_source: default`.
2. The approval line, `SW-PREAPPROVAL-A3: APPROVED`, in `docs/swarm-mvp/DECISIONS.md`.
3. SW-X1-S1 and SW-W4-S1 merged (section 2).

### Step 0 — approval line (read-only)
```bash
grep -c "^- SW-PREAPPROVAL-A3: APPROVED" docs/swarm-mvp/DECISIONS.md
```
It must print `1`. If it prints `0`, STOP (S7, section 10) with reason `SW-PREAPPROVAL-A3 not approved`. Never add or edit that line yourself.

### Step 1 — `scripts/v23_splitsignal_smoke.py` (create, exactly)
```python
{{FILE:scripts/v23_splitsignal_smoke.py}}
```

### Step 2 — `tests/providers/test_v23_splitsignal_smoke.py` (create, exactly)
```python
{{FILE:tests/providers/test_v23_splitsignal_smoke.py}}
```
Run the offline tests first: `uv run pytest tests/providers/test_v23_splitsignal_smoke.py -q` must print `7 passed`. These tests make no network call.

### Step 3 — the live run (once; the only permitted second run is the `model_not_listed` case below)
```bash
uv run python scripts/v23_splitsignal_smoke.py --stream; echo "exit=$?"
```
The script writes `docs/evidence/v23/splitsignal_live.json` and prints its `status`.
- `exit=0`, status `pass`: SP4 **and** SP5 are verified from SwarmAI's side.
- `exit=1`: read `calls` in the JSON.
  - If `calls[0].mode` is `text` and it has no `error_class`, SP4 is verified and SP5 is not reached. Record `SP5: not reached (<status>)`.
  - Otherwise, SP4 is not reached. Record `SP4: not reached (<status>)`.
  - Either way, continue to Step 4 and do not re-run the script.
- `exit=3` with status `blocked:model_not_listed`: no model call was made. Read `listed_route_ids` in the JSON.
  - If exactly one id starts with `gemini/`, run the command **once more** as `SPLITSIGNAL_MODEL=<that id> uv run python scripts/v23_splitsignal_smoke.py --stream; echo "exit=$?"`. The 2-call cap still holds, because the first run made no model call. Then handle its exit code with these same rules, except that this bullet no longer applies. Record `SPLITSIGNAL_MODEL substituted: <old> -> <new>` under "Decisions" and under "Needs other owner" (the owner sets the Cursor Environment Variable `SPLITSIGNAL_MODEL` to the new id).
  - Otherwise, STOP (S7) with reason `model_not_listed`.
- `exit=3` with any other `blocked:<reason>`: no live call was made. STOP (S7) with that reason. The JSON is honest evidence: commit it.

Check that the evidence holds no secret and no content:
```bash
grep -c "ss_live_" docs/evidence/v23/splitsignal_live.json   # must print 0
grep -c '"content"' docs/evidence/v23/splitsignal_live.json  # must print 0
```
If either prints anything other than `0`, delete the file, write `evidence withheld: <which check>` in the handoff, and STOP (S3).

### Step 4 — SP6 check (read-only)
```bash
gh api "repos/pri8771/inference_server/contents/docs/evidence/v2.3-offline.md?ref=cursor/is-v23-integration-460c" --jq .content 2>/dev/null \
  | base64 -d 2>/dev/null | grep -c "swarmai-consumer 1\." || true
```
- A number of 1 or more: SP6 is reached (inference_server records the same contract). Record `SP6: reached (swarmai-consumer 1.x)`.
- `0`, or no output: record `SP6: not reached yet`. This is **not** a STOP. The coordinator re-runs this prompt on a new branch named `cursor/v23-x2-s1-splitsignal-live-r2`, then `-r3`, and so on, after SP6. Before any re-run, the coordinator adds a fresh approval line `SW-PREAPPROVAL-A3-R<n>: APPROVED` for the extra calls. Without it, the re-run skips Step 3 and reuses the committed evidence.

### Step 5 — `docs/v2.3/EXIT_CHECKLIST.md` (the SplitSignal row only)
Replace the status cell of the row that starts `| SplitSignal consumer adapter` with exactly `done (fake SplitSignal); live SP4 <verified/not reached>, SP5 <verified/not reached>; SP6 <reached/not reached yet>`, filled in from Steps 3–4. In the evidence cell of the same row, append `; docs/evidence/v23/splitsignal_live.json`. Change nothing else in the file.

### Step 6 — `docs/v2.3/STATUS.md` (append one section at the end)
```markdown
## SplitSignal sync points (SW-X2-S1, <UTC date>)
Contract `swarmai-consumer 1.x`; evidence `docs/evidence/v23/splitsignal_live.json` (status `<status>`); live calls made: <0, 1 or 2>, `max_tokens` 16, spend: none reported (`cost_source` <value>).
| SP | Meaning | SwarmAI state |
|---|---|---|
| SP1 | contract frozen | reached (SW-X1-S1 merged) |
| SP2 | mock testable | <reached / not run> |
| SP3 | key issuable | <reached if SP4 reached, otherwise unknown> |
| SP4 | live non-streaming | <verified / not reached (reason)> |
| SP5 | live streaming | <verified / not reached (reason)> |
| SP6 | joint V2.3 finish | <reached / not reached yet> |
Not claimed: V2.3 accepted.
```

### Acceptance (this session)
- [ ] Step 0 printed `1`, and the environment check printed three `SET` lines.
- [ ] `tests/providers/test_v23_splitsignal_smoke.py` gives 7 passed offline.
- [ ] The live script ran exactly once (at most 2 calls), and its exit code and status are in the handoff.
- [ ] The evidence JSON contains no `ss_live_` and no `"content"`.
- [ ] The SplitSignal checklist row and the appended STATUS section match the evidence.
- [ ] The SP4/SP5/SP6 states in the handoff are copied from Steps 3–4, not assumed.
