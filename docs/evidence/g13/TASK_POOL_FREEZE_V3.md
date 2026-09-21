# ART-V13-TASK-POOL — g13-pool-freeze-v3

Packet: `V2B-001-R4`  
Requested transition: drafting -> reviewable only  
Accepted: **no** — independent lead freeze required  
`counted_qualification_ready`: **false**  
W-131B: **not started**

worker-pc `worker/swarmai-v13-task-pool-freeze-06@f7800332594d67c8b872b3597abd59f35987a2a0` is defect evidence only (15 records/cell but 5 archetypes/cell). This freeze does not inherit its qualification claims.

## What v3 changes

New independence checker `g13-independence-checker-v3` fail-closes on:

- semantic-archetype duplicates
- scenario-substitution siblings
- identifier/numeric reseeds (normalised templates)
- clause-prefix/containment siblings
- payload/prompt digest overlap
- calibration vs held-out id/hash overlap
- <15 distinct archetypes in any required cell

Held-out corpus: 16 cells × 15 unique archetypes = **240** independent inputs. Calibration is a separate 16-record split.

Sealed reference content digest is **not** declared. Fabricating it is prohibited.
