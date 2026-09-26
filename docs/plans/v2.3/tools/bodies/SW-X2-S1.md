**Goal.** Record SwarmAI's side of the joint V2.3 finish with SplitSignal (owner decision D4). One bounded live smoke test proves sync points SP4 (non-streaming) and SP5 (streaming) from SwarmAI's side, and SP6 is checked against inference_server's evidence. The session makes **at most 2 live calls in total**: one run of the script, one text call and one streamed call, each with `max_tokens` 16, on a route SplitSignal lists as free. Zero spend.

**Gates, in order.** Each one is checked before anything touches the network.
1. The environment variables (section 2): `SPLITSIGNAL_BASE_URL` (the public URL + `/v1`), `SPLITSIGNAL_API_KEY`. `SPLITSIGNAL_MODEL` is optional: when unset, the script uses `gemini/gemini-3.5-flash-lite` and records `model_source: default`.
2. The approval line, `SW-PREAPPROVAL-A3: APPROVED`, in `docs/swarm-mvp/DECISIONS.md`.
3. SW-X1-S1 and SW-W4-S1 merged (section 2).
4. inference_server sync point SP4 (and, for the streamed call, SP5) recorded on `cursor/is-v23-integration-460c` (Step 0b). The joint schedule (`docs/plans/v2.3/JOINT_PLAN.md`) runs this session after IS-W8-MERGE, so SP6 is normally reached too and no re-run is needed.

### Step 0 — approval line (read-only)
```bash
grep -c "^- SW-PREAPPROVAL-A3: APPROVED" docs/swarm-mvp/DECISIONS.md
```
It must print `1`. If it prints `0`, STOP (S7, section 10) with reason `SW-PREAPPROVAL-A3 not approved`. Never add or edit that line yourself.

### Step 0b — inference_server sync points SP4/SP5 (read-only, no call to SplitSignal)
inference_server writes one marker line per sync point, starting at column 0, into `docs/evidence/m1/hosted-v05.md` on its integration branch (IS-W2-DEPLOY writes `SP3:`/`SP4:`; IS-W4-MERGE, or the IS-W6/W8-MERGE fallback, writes `SP5:`).
```bash
gh api "repos/pri8771/inference_server/contents/docs/evidence/m1/hosted-v05.md?ref=cursor/is-v23-integration-460c" --jq .content 2>/dev/null \
  | base64 -d 2>/dev/null > /tmp/is_hosted_v05.md || true
SP4=$(grep -c '^SP4: reached' /tmp/is_hosted_v05.md 2>/dev/null || true); SP5=$(grep -c '^SP5: reached' /tmp/is_hosted_v05.md 2>/dev/null || true)
echo "SP4=${SP4:-0} SP5=${SP5:-0}"
if [ "${SP5:-0}" -ge 1 ]; then STREAM_FLAG=--stream; else STREAM_FLAG=; fi; echo "STREAM_FLAG=${STREAM_FLAG:-none}"
```
- `SP4=0`: STOP (S7) with reason `external gate SP4 not reached`. No live call is made, and the approval stays unused for a later run.
- If `gh api repos/pri8771/inference_server --jq .full_name` does not print `pri8771/inference_server`, this environment cannot read the private repo: STOP (S7) with reason `inference_server not readable from this environment` (launch this session from an environment that has both repos, JOINT_PLAN §4).
- `SP4` ≥ 1 and `SP5=0`: continue without `--stream` (one text call). Record `SP5: not reached (inference_server SP5 line absent)`.

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
uv run python scripts/v23_splitsignal_smoke.py $STREAM_FLAG; echo "exit=$?"
```
`$STREAM_FLAG` comes from Step 0b (`--stream` only when SP5 is recorded). The script writes `docs/evidence/v23/splitsignal_live.json` and prints its `status`.
- `exit=0`, status `pass`: with `--stream`, SP4 **and** SP5 are verified from SwarmAI's side; without it, SP4 is verified and SP5 stays `not reached` (Step 0b).
- `exit=1`: read `calls` in the JSON.
  - If `calls[0].mode` is `text` and it has no `error_class`, SP4 is verified and SP5 is not reached. Record `SP5: not reached (<status>)`.
  - Otherwise, SP4 is not reached. Record `SP4: not reached (<status>)`.
  - Either way, continue to Step 4 and do not re-run the script.
- `exit=3` with status `blocked:model_not_listed`: no model call was made. Read `listed_route_ids` in the JSON.
  - If exactly one id starts with `gemini/`, run the command **once more** as `SPLITSIGNAL_MODEL=<that id> uv run python scripts/v23_splitsignal_smoke.py $STREAM_FLAG; echo "exit=$?"`. The 2-call cap still holds, because the first run made no model call. Then handle its exit code with these same rules, except that this bullet no longer applies. Record `SPLITSIGNAL_MODEL substituted: <old> -> <new>` under "Decisions" and under "Needs other owner" (the owner sets the Cursor Environment Variable `SPLITSIGNAL_MODEL` to the new id).
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
- `0`, or no output: record `SP6: not reached yet`. This is **not** a STOP. The coordinator re-runs this prompt on a new branch named `cursor/v23-x2-s1-splitsignal-live-r2`, then `-r3`, and so on, after SP6. Before any re-run, the coordinator adds a fresh approval line `SW-PREAPPROVAL-A3-R<n>: APPROVED` for the extra calls. Those extra calls are outside the joint 7-call budget (IS-A6 5 + SW-A3 2), so the owner must approve them explicitly. Without it, the re-run skips Step 3 and reuses the committed evidence.

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
