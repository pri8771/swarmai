# SECRETS_SWARMAI_SECTION: the swarmai additions to the inference_server SECRETS_SETUP

**Status: MERGED (2026-09-26).** Edits 1–6 below are applied in inference_server `docs/plans/v2.3/SECRETS_SETUP.md` on branch `cursor/v23-plan-460c` (§5 SEC-15, §8, §9 STEP E1/G/G-PUBLIC/H/I and the final report, §10). Use that file's §9 as the ONE computer-use prompt for both repos. This file is kept as the record of what swarmai asked for.

Target file: `pri8771/inference_server` → `docs/plans/v2.3/SECRETS_SETUP.md` on branch `cursor/v23-plan-460c` (read at `28232556`). Apply the edits below to it. They are written for the inference_server coordinator, or for the owner pasting the §9 computer-use prompt by hand. swarmai adds exactly **one** name, `SPLITSIGNAL_MODEL` (coordinator decision C5). Its value is not secret. It is kept in the Desktop file so that one file holds every SwarmAI setting.

`SPLITSIGNAL_API_KEY` (SEC-13, group `shared`) and `SPLITSIGNAL_BASE_URL` (SEC-14, group `swarmai`) are already in that file. Keep them unchanged.

## Edit 1: §8, replace the line `SWARMAI-SPECIFIC SECRETS: to be appended after the swarmai audit.` with
```markdown
SWARMAI-SPECIFIC SECRETS (swarmai audit, 2026-09-26): none beyond the three rows above. Coordinator decision C5 puts `SPLITSIGNAL_MODEL` in the Desktop file (group `swarmai`) and in Cursor as an Environment Variable, so that one file holds every SwarmAI setting. This supersedes "Not in the Desktop secrets file" in the row above. SwarmAI needs no provider key, no database secret and no `SWARM_ROUTER_*` value for V2.3. The only session that reads these values is SW-X2-S1 (`docs/plans/v2.3/prompts/SW-X2-S1.md` in swarmai). Every other SwarmAI session uses fakes.
```

## Edit 2: §9 prompt, STEP E1, append directly after the `printf 'SPLITSIGNAL_BASE_URL=...` line (still before E2)
```text
    note SPLITSIGNAL_MODEL "config value, not secret: recommended default route id (SplitSignal Gemini free tier)" "swarmai; Cursor Environment Variable"
    printf 'SPLITSIGNAL_MODEL=gemini/gemini-3.5-flash-lite\n' >> "$F"
    grep -c '^SPLITSIGNAL_MODEL=gemini/' "$F"      (must print 1)
```
On a resumed run (T4 said FILE_EXISTS), first run `has SPLITSIGNAL_MODEL`, and skip these three lines if it prints PRESENT.

## Edit 3: §9 prompt, STEP G, add this row directly below the `SPLITSIGNAL_BASE_URL` row
```text
  SPLITSIGNAL_MODEL               Environment Variable  pri8771/swarmai
```

## Edit 4: §9 prompt, STEP H, replace the counts
- `(prints 16 names, never values)` → `(prints 17 names, never values)`
- `(must print 16)` → `(must print 17)`
- `[ ] The file has the 16 names (the 14 Cursor names plus GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET), 4 group headers, ...` → `[ ] The file has the 17 names (the 15 Cursor names plus GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET), 4 group headers, ...`
- `[ ] Cursor My Secrets lists the 14 names ...` → `[ ] Cursor My Secrets lists the 15 names ...`

The group-header count stays 4: `SPLITSIGNAL_MODEL` goes under the existing `# --- swarmai ---` header.

## Edit 5: §9 prompt, FINAL REPORT, add this line directly below the `SPLITSIGNAL_BASE_URL — ...` line
```text
SPLITSIGNAL_MODEL — file: yes/no — cursor: yes/no, personal, Environment Variable, swarmai
```

## Edit 6: §10, replace the last paragraph (`On a new agent on pri8771/swarmai ...`) with
````markdown
Start a **new** Cursor cloud agent on `pri8771/swarmai` and have it run (it prints names and status words only):

```bash
for v in SPLITSIGNAL_API_KEY SPLITSIGNAL_BASE_URL SPLITSIGNAL_MODEL; do test -n "${!v}" && echo "$v SET" || echo "$v MISSING"; done
python3 -c "import os,re;print('API_KEY_FORMAT_OK' if re.fullmatch(r'ss_live_[0-9a-f]{32}_[A-Za-z0-9_-]{43}',os.environ.get('SPLITSIGNAL_API_KEY','')) else 'API_KEY_FORMAT_BAD')"
python3 -c "import os;u=os.environ.get('SPLITSIGNAL_BASE_URL','');print('BASE_URL_OK' if u.startswith('https://') and u.endswith('/v1') else 'BASE_URL_BAD')"
```

If `SPLITSIGNAL_API_KEY` or `SPLITSIGNAL_BASE_URL` prints `MISSING`, the public-repo caveat in §8 applies: allow secrets for `pri8771/swarmai` in the dashboard, or make the repo private (swarmai OWNER_PREFLIGHT R-1). `SPLITSIGNAL_MODEL MISSING` is harmless, because SwarmAI then uses `gemini/gemini-3.5-flash-lite`.
````

## How to get each swarmai value (summary)
| Name | Group | How obtained | Cursor type · Apply to |
|---|---|---|---|
| `SPLITSIGNAL_API_KEY` | shared | STEP E2 (already present): `openssl`, format `ss_live_<32 hex>_<43 base64url>` | Runtime Secret · inference_server **and** swarmai |
| `SPLITSIGNAL_BASE_URL` | swarmai | STEP E1 (already present): `SPLITSIGNAL_PUBLIC_URL` + `/v1` | Environment Variable · swarmai |
| `SPLITSIGNAL_MODEL` | swarmai | Edit 2: the fixed value `gemini/gemini-3.5-flash-lite` | Environment Variable · swarmai |
