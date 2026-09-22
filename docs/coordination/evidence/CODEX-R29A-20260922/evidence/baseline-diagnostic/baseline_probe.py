from __future__ import annotations
import inspect, json
from swarm.contracts.actions import ActionReceiptV17, AdapterManifest
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.adapters.browser_session import BrowserSessionAdapter
from swarm.tools.adapters.local_sandbox import LocalSandboxAdapter
from swarm.tools.adapter_registry import AdapterRegistry

adapters = [ApiMcpAdapter(), BrowserSessionAdapter()]
rows = []
for adapter in adapters:
    rows.append({
        "adapter": type(adapter).__name__,
        "constructor": str(inspect.signature(type(adapter))),
        "manifest_identity": f"{adapter.manifest.integration_id}@{adapter.manifest.integration_version}",
        "manifest_fields": sorted(adapter.manifest.model_dump(mode="json")),
        "inline_manifest": "manifest" not in inspect.signature(type(adapter)).parameters,
    })
registry = AdapterRegistry()
api = adapters[0]
registry.register(api)
before = registry.resolve("api.mcp.echo", "1.0").manifest.network_allowed
api.manifest.network_allowed = False
after = registry.resolve("api.mcp.echo", "1.0").manifest.network_allowed
out = {
    "adapter_manifest_fields": sorted(AdapterManifest.model_fields),
    "expected_r29a_fields": sorted({"integration_id","integration_version","adapter_class","read_data_classes","write_data_classes","operations","network_scopes","filesystem_scopes","secrets_refs_required","risk_class","sandbox_required","host_requirements","user_interaction_consequential","schema_version"}),
    "receipt_has_manifest_digest": "manifest_digest" in ActionReceiptV17.model_fields,
    "adapters": rows,
    "registry_manifest_live_mutation": {"before": before, "after": after},
}
print(json.dumps(out, indent=2, sort_keys=True))
