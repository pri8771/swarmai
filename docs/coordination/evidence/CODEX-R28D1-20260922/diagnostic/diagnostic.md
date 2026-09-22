# R28d-1 causal diagnostic — local sandbox operations

## Boundary

- Canonical release: `origin/coordination/swarm-control@bd08b419f2d4d61913a85b3921474e1aef942da7`, assignment `CODEX_R28D1_20260922.md`.
- Exact accepted source: `1ea1ca55a2470d94fe704d64c029a991c3c0dea5`, tree `1b8577c91b2984b804ea6df259e6a47a697ccc31`, clean.
- Pure local probe only. It used one `TemporaryDirectory`; no subprocess command, gateway mission, database, provider, model, network, public effect, grant, scheduler, or repository write occurred. The deliberate escape target remained inside that owned temporary directory and cleanup was verified.

## Reproduced gaps

`probe.py` and `probe.log` exercise the accepted adapter directly:

1. Manifest operations are only `write_text`. Normalizing required `fs.write_text` and `proc.run` raises `KeyError` before an envelope exists.
2. Current relative `write_text` succeeds and is idempotent/low, but its observations have the old shape: pre `{exists,path,observed_at}` and post `{exists,size,result}`, not the required content hashes and byte count.
3. Lexical `../` and absolute paths are rejected, but as `PermissionError("filesystem_path_escape_denied")`, not `AdapterDeniedError("path_outside_root")`.
4. Concrete confinement defect: `root/escape` was a symlink to a sibling directory within the owned temporary area. `escape/pwn.txt` passed validation and `execute` created the file outside injected `root`. The whole temporary tree was removed afterward.
5. Constructor still permits omitted `root` and has no `command_allowlist`; R28d-1 requires an explicit root and optional allowlist with exact defaults.
6. No `proc.run` code exists, so there is currently no prefix enforcement, fixed cwd, no-shell subprocess path, bounded tails/full-byte hashes, or nonzero-exit result representation.

## Smallest implementation map

### Manifest

Replace `write_text` with exactly two declarations:

- `fs.write_text`: idempotent/low, authority scope `fs.worktree`.
- `proc.run`: idempotent/low, authority scope `proc.test`.

Retain the accepted R29a manifest identity and vocabulary. Runtime root and allowlist remain instance configuration and do not change the manifest digest.

### Adapter

- Constructor: require `root: Path`; resolve it once; copy either the caller allowlist or the five exact default prefixes. Avoid a mutable shared default.
- Normalize by operation. `fs.write_text` retains only normalized `{path,text}`; `proc.run` retains `{argv:list[str],timeout_s}`. Both take classification/scopes from their manifest declaration.
- Centralize `_resolve_path`: reject absolute or lexical `..`; compute `(root/path).resolve()` and require `resolved.relative_to(root)` to succeed. Raise exactly `AdapterDeniedError("path_outside_root")`. Use the resolved target for pre/execute/post so validation and effect address the same path.
- `fs.write_text` pre-observation is the existing file's SHA-256 or null. Execute writes UTF-8 and returns explicit `outcome="succeeded"`; post reports SHA-256 and bytes.
- `proc.run` requires a nonempty string argv and a prefix match against one configured list. Deny before calling subprocess with exact `AdapterDeniedError("command_not_allowlisted")`. Invoke `subprocess.run(argv, cwd=root, shell=False, capture_output=True, timeout=timeout_s)`; hash all stdout/stderr bytes and decode/cap each tail to its last 4096 bytes. Return explicit succeeded outcome even when `returncode != 0`.
- Keep reconciliation operation-aware: file existence/hash for writes; process outcomes are already known from synchronous execution and should not fabricate external success during an unknown recovery.

### Compatibility callers

Current direct LocalSandboxAdapter construction is confined to existing tool/gateway tests (`callers.txt`); production permission proof uses the separate dynamic legacy adapter and is unaffected. Update existing tests that request `write_text` or rely on its default to `fs.write_text`, and their policy scope from `sandbox.fs` to `fs.worktree`. The normalizer-generation and three-integration compatibility tests also instantiate LocalSandboxAdapter and must continue to pass with explicit roots. Add focused R28d-1 tests for the released adverse cases. Do not wire mission worker/runtime yet; that is R28d-2.

## Stop condition

The first material defect is the demonstrated symlink escape, coupled with the missing released operations. No production repair was made in this diagnostic lane.
