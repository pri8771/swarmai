# ART-V20-SUPPORT-MATRIX — support truth template

Status: drafting
Target: V2.0
Owner: ChatGPT lead + Cursor Session B

Use only these status classes:
- supported
- experimental
- local_only
- external_prerequisite_blocked
- unsupported

Every row must link:
- source artifact/version;
- acceptance/evidence refs;
- required environment/provider/tool;
- known limitations;
- security/privacy notes;
- recovery behavior.

## Rows to populate on integrated candidate

### Mission/task families
- coding
- planning
- reasoning
- extraction
- review
- summarization
- other declared handlers

### Model/inference
- local Ollama
- each admitted remote provider/route class
- fallback
- qualification-based routing

### Workers
- single-host
- multi-process
- multi-host
- drain
- kill/reassignment
- browser/session trust class

### Knowledge
- scoped facts/procedures
- retrieval
- supersession/deletion
- export/import

### Tools
- local sandbox/read/write
- API/MCP adapters
- browser/session workflows
- consequential approval/reconciliation

### Operations
- backup
- restore
- site recovery
- clean install
- upgrade
- extensions
- self-development

A row is never `supported` because code exists. It needs the relevant accepted/verified artifact evidence and honest external prerequisites.
