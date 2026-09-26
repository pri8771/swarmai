**Goal.** Add offline operator commands under `swarm v23 …` in a **new module**, `src/swarm/cli_v23.py`, and hook it into `src/swarm/cli.py` with three tiny edits. Keeping the commands in their own module keeps `cli.py` (1000+ lines, also touched by SW-W4-S1) conflict-free.

**Commands.** Every command prints one JSON document; any failure prints `{"ok": false, "error": …}` and exits with code 2.

| Command | What it does |
|---|---|
| `swarm v23 scheduler-policy [--policy PATH]` | loads `config/v23/scheduler_policy.v1.json` through `WdrrConfig.from_policy_file` and prints it |
| `swarm v23 scheduler-simulate --projects a:1,b:3 [--decisions N]` | offline `SchedulerService` run with constant demand; prints admitted counts, share and target share. `N` must be in 1..100000. |
| `swarm v23 pack-sign --manifest M --out O` | signs using the key in `SWARM_PACK_KEY_<PUBLISHER>` (through `trusted_keys_from_env`); never prints the key |
| `swarm v23 pack-verify --manifest M` | `verify_manifest` against trusted env keys |
| `swarm v23 export --project-id P [--out-dir D]` | `PortabilityService.export_project` |
| `swarm v23 import --bundle B [--target-project-id T]` | `PortabilityService.import_bundle`; tampering gives `bundle_integrity_mismatch` |

Rules:
- There is no network, provider or HTTP call in any command.
- The simulation broker is local to this module. Do **not** import from `tests/` or from `swarm.acceptance`; SW-W3-S4 has its own copy so the two sessions stay parallel.

The code below was compiled and run against `dev @ 8e1c0fde` plus Wave-1/Wave-2:
- `tests/product/test_v23_cli.py`: 9 passed.
- `swarm v23 scheduler-simulate --projects a:1,b:3 --decisions 400` gives admitted `{"a":100,"b":300}`, an exact 1:3 share.
- ruff and mypy: clean.

### Step 1 — `src/swarm/cli_v23.py` (create, exactly)
```python
{{FILE:src/swarm/cli_v23.py}}
```

### Step 2 — hook into `src/swarm/cli.py` (three edits, nothing else)
Save this patch as `/tmp/SW-W3-S3-cli.patch`, then run `git apply --check /tmp/SW-W3-S3-cli.patch && git apply /tmp/SW-W3-S3-cli.patch`.
```diff
{{FILE:patches/SW-W3-S3-cli.patch}}
```
If the check fails because line numbers moved, make the three edits by hand:
1. Add `from swarm import cli_v23` as the **first** `from swarm…` import, right after `import uvicorn` and its blank line. Ruff requires it there, with no extra blank line.
2. Directly after `sub = parser.add_subparsers(dest="command", required=True)` inside `main()`, add `    cli_v23.register(sub)`.
3. Directly after `args = parser.parse_args()` inside `main()`, add:
```python
    if cli_v23.dispatch(args):
        return
```

### Step 3 — `tests/product/test_v23_cli.py` (create, exactly)
```python
{{FILE:tests/product/test_v23_cli.py}}
```

### Step 4 — run
```bash
uv run pytest tests/product/test_v23_cli.py -q          # 9 passed
uv run swarm v23 scheduler-simulate --projects a:1,b:3 --decisions 400   # admitted a=100, b=300
uv run swarm --help | grep v23                          # the subcommand is listed
uv run pytest tests/product -q
```
The tests set `SWARM_PACK_KEY_ACME` to a **test-only** literal through `monkeypatch`. Never put a real key in a test, a doc or a commit.
