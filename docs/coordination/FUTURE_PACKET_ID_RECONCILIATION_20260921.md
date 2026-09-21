# Packet identity and historical aliases

Execution IDs live in V17_RECOVERY_PACKET_QUEUE.json, V17_TO_V23_PACKET_QUEUE.json and the future graph's v30_packets. Coarse groups in the future graph are visualization/coverage groups only; each lists maps_to. Contract-era names are aliases, never competing queue entries.

Historical V2A/V2B lane names do not reactivate those workers. Fine V30B–F/X IDs remain proposed until independently frozen. A split keeps the old ID as aggregate and provides child IDs, so historical evidence retains meaning. `basis` points at an audited parent without requiring that defective parent to complete itself first.

Closure splits: R17b -> R17b-1/R17b-2 (DB mapping and leased loop); R17c -> R17c-1/R17c-2 (authenticated transport and separate CLI); R33c -> R33c-1/R33c-2 (typed GitHub adapter and real-world harness). R28s is the documented sandbox gap correction; it does not duplicate ToolGateway authority.

Run tools/validate_plan.py to validate IDs, references, ordinary cycles, completion cycles, contract coverage, gates and generated catalog equality. Historical aliases may map to several fine slices; real execution IDs must remain unique.
