from __future__ import annotations
import json, tempfile
from pathlib import Path
from swarm.tools.adapters.local_sandbox import LocalSandboxAdapter
from swarm.tools.manifests import MANIFEST_DIR, load_manifest

out = {}
with tempfile.TemporaryDirectory(prefix="swarm-r28d1-probe-") as raw:
    owned = Path(raw)
    root = owned / "root"
    outside = owned / "outside"
    root.mkdir(); outside.mkdir()
    adapter = LocalSandboxAdapter(load_manifest(MANIFEST_DIR / "local.sandbox@1.json"), root=root)
    out["current_operations"] = sorted(adapter.manifest.operations)
    env = adapter.normalize({"project_id":"probe", "operation":"write_text", "path":"nested/a.txt", "text":"safe-current"})
    adapter.validate(env)
    pre = adapter.observe_pre_state(env)
    result = adapter.execute(env)
    post = adapter.observe_post_state(env, result)
    out["current_write_text"] = {"classification":[env.side_effect_class, env.risk_class], "pre_keys":sorted(pre), "result":result, "post_keys":sorted(post), "content":(root/"nested/a.txt").read_text()}
    for operation in ("fs.write_text", "proc.run"):
        try:
            adapter.normalize({"project_id":"probe", "operation":operation, "path":"x", "text":"x", "argv":["git","status"], "timeout_s":1})
        except Exception as exc:
            out[operation] = {"error_type":type(exc).__name__, "error":str(exc)}
        else:
            out[operation] = {"error":None}
    for label, path in (("relative_parent","../outside.txt"),("absolute",str(outside/"absolute.txt"))):
        candidate = adapter.normalize({"project_id":"probe", "operation":"write_text", "path":path, "text":"must-not-write"})
        try:
            adapter.validate(candidate)
        except Exception as exc:
            out[label] = {"error_type":type(exc).__name__, "error":str(exc), "outside_exists":(outside/"absolute.txt").exists() or (owned/"outside.txt").exists()}
    (root/"escape").symlink_to(outside, target_is_directory=True)
    escaped = adapter.normalize({"project_id":"probe", "operation":"write_text", "path":"escape/pwn.txt", "text":"current-escape"})
    try:
        adapter.validate(escaped)
        validation = "passed"
    except Exception as exc:
        validation = f"{type(exc).__name__}:{exc}"
    escaped_result = adapter.execute(escaped) if validation == "passed" else None
    out["symlink_escape"] = {"validation":validation, "result":escaped_result, "outside_created":(outside/"pwn.txt").exists(), "outside_content":(outside/"pwn.txt").read_text() if (outside/"pwn.txt").exists() else None}
    out["temp_cleanup_pending_inside_context"] = owned.exists()
out["temp_cleanup_after_context"] = not owned.exists()
print(json.dumps(out, indent=2, sort_keys=True))
