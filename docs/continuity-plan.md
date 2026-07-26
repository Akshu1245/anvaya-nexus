# Continuity and Degraded-Mode Plan

## P0 modes

| Mode | Capability |
|---|---|
| Full | Four P0 sources, optional language model, graph, assurance, Action Impact, HTML report |
| Degraded | Deterministic parsing, search, graph/text path, assurance, Action Impact, HTML report |
| Read-only continuity | Last synchronized synthetic snapshot with timestamp and limitations |
| Emergency local demo | Packaged Flask/SQLite application using the same deterministic core |

## Fallback ladder

| Failure | P0 fallback |
|---|---|
| LLM unavailable/no key | Rule parser and editable filters |
| Voice unavailable | Typed input; voice is P1 |
| One source unavailable | Continue and display limitation |
| Source stale | Display last sync and qualify claims |
| Graph fails | Text path, source list, source-record references |
| PDF fails | Print-ready HTML; PDF is P1 |
| Catalyst unavailable | Local deployment |
| Cost ceiling reached | Deterministic evidence summary |

## Recovery requirements

Every mode exposes current source states and snapshot time. Recovery never fabricates missing data or silently substitutes context for evidence. Audit records the active degraded mode where relevant.

## Cost controls

Rule-based parsing first; cache non-sensitive metadata; precompute normalized identifiers and Case DNA features; bound sources, rows, hops, nodes, report size, and tokens; measure the share of queries completed without an expensive model call.
