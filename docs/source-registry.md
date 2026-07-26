# Source Registry and Governance

## P0 sources

| ID | Source | Treatment | Reliability role | Import method |
|---|---|---|---|---|
| CCTNS_REPLICA | Synthetic CCTNS-style cases | Working replica | Primary operational record | CSV/JSON functional adapter |
| FORENSICS_REPLICA | Synthetic forensic metadata | Working replica | Specialist corroboration | Seed/import |
| VEHICLE_REPLICA | Synthetic vehicle registry | Working replica | Authoritative administrative replica | Seed/import |
| CONTEXT_FIXTURE | Versioned offline synthetic GIS/context | Working offline fixture | Context only; never case proof | Versioned fixture |

## P1-labelled sources during P0

COURT_REPLICA and PROSECUTION_REPLICA may appear in Source Control as **Unavailable — P1 synthetic adapter**. They are never searched in P0 and never described as live.

## FUTURE sources

Custody, SOP/legal library, NAFIS metadata, 112 dispatch, ANPR, digital evidence, and authorised ICJS-aligned connectors.

## Source Passport — P0

Every factual result retains source ID, external record ID, source version, source update time, ANVAYA import time, access class, reliability role, Fresh/Stale/Unavailable state, checksum, and ordered transformation history.

Transformation events record: event ID, source-record ID, operation, input field, output field, rule/version, timestamp, and outcome. They must not overwrite source values.

## Governance

- Connectors are read-only.
- Source records are immutable.
- Conflicting values remain side-by-side with roles and timestamps.
- Context never establishes an individual-case relationship.
- Unavailable or stale sources limit claims and remain visible in results/reports.

## Data Readiness — P0

CCTNS CSV/JSON import reports mapped fields, missing keys, invalid dates, duplicate identifiers, unlinked documents, failed rows, accepted rows, checksum, and final import status. Failed rows are quarantined rather than silently accepted.
