# R29a exact-base diagnostic and compatibility disposition

REWORK_FOUND baseline gaps reproduced on accepted `ba458eb1a9a1af5f7e022159f36e6ce296d472cc`, tree `8c22e55f11351f567ae7d62b139383179caeb6fa`; native release `8ce9f5ef0069fde2ac4ad708f465612ddb3cb36d`. Codex diagnostic only; no source changes or live action.

Inline manifests retain obsolete vocabulary, constructors have no validated-manifest input, and receipts lack a resolved definition digest. The [offline causal inventory](evidence/CODEX-R29A-DIAGNOSTIC-20260922/diagnostic.md) and [hash manifest](evidence/CODEX-R29A-DIAGNOSTIC-20260922/manifest.sha256) identify exact paths/callers. Independent integration owner inspected the report/source boundary; the mechanical probe has not been independently rerun yet.

Request narrow lead contract clarification before the version/receipt compatibility change:

1. Packet explicitly names local.sandbox@1 and mcp.echo@1 while accepted identities are local.sandbox@1.0 and api.mcp.echo@1.0. Proposed: follow exact new packet identities, update bounded callers/tests and grant pins, no alias or historical approval upgrade.
2. Browser must also lose inline manifest. Proposed: add browser.session@1.json for its existing bounded operation set. LegacyToolCallAdapter's operation table is dynamically registered, outside adapters/; proposed retain its generated validated manifest using renamed vocabulary, preserve literal network authority scope, and digest it on receipts rather than invent a static legacy operation catalogue.
3. ActionReceiptV17 digest is required str, but existing durable JSONB receipts predate it. Proposed: explicit historical-unbound marker for missing old digest, never compute a current manifest hash for a past action; all new gateway receipts require a real resolved digest. Please choose exact approved representation/compatibility behavior. No column migration is mechanically required because receipt model dumps already persist to JSONB.

Secret guard will scan strings recursively including keys (a conservative implementation of anywhere), with no new trust/signature/discovery lifecycle. R28d remains held. This record does not authorize a grant or change live gates.
