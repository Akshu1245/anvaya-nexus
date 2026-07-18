# Decision Log

| ID | Decision | Class |
|---|---|---:|
| D-001 | Locked workflow is Ask → Select Sources → Discover → Verify → Prioritise → Report. | P0 |
| D-002 | Four working P0 sources only: CCTNS, Forensics, Vehicle, offline Context/GIS. | P0 |
| D-003 | Court and Prosecution are P1 synthetic adapters; P0 may label them unavailable/future only. | P1 |
| D-004 | Action Impact working engine/basic panel is P0; advanced interaction is P1. | P0/P1 |
| D-005 | CCTV review ranks highest in the golden demonstration. | P0 |
| D-006 | Minimal Supervisor Review is P0; expanded analytics is P1. | P0/P1 |
| D-007 | Data Readiness and CCTNS CSV/JSON validation are P0. | P0 |
| D-008 | Repository root is used directly; no nested `anvaya/`. | P0 |
| D-009 | P0 uses prototype auth with three backend-enforced accounts; Catalyst Authentication is optional P1. | P0/P1 |
| D-010 | Freshness thresholds are configurable; states are Fresh, Stale, Unavailable. | P0 |
| D-011 | Multilingual benchmark is 4 pure Kannada plus 6 code-mixed. | P0 |
| D-012 | Case DNA bands are 0–24 weak, 25–49 limited, 50–69 moderate, 70–84 strong candidate, 85–100 very strong candidate. | P0 |
| D-013 | Case DNA is a ranking aid, never offender/guilt/identity probability. | P0 |
| D-014 | Purposes are Active Case Investigation, Entity Verification, Pattern Research, Supervisor Review, Procedural Review. | P0 |
| D-015 | Jurisdictions are assigned station, assigned district, external. | P0 |
| D-016 | Backend masking covers names, phones, IMEIs, registrations, addresses, sensitive evidence references. | P0 |
| D-017 | Source Passport includes ordered transformation history. | P0 |
| D-018 | Graph text fallback includes path, source list, source-record references; download is P1. | P0/P1 |
| D-019 | Every P0 report displays the mandated synthetic-prototype watermark. | P0 |
| D-020 | Offline versioned context fixture avoids external paid APIs. | P0 |
| D-021 | External AI is optional; deterministic workflow needs no API key. | P0 |
| D-022 | GitHub is the sole code/document source of truth; Base44 is visual reference only. | P0 |
| D-023 | No live police-system access or live-integration claim. | OUT boundary |

Changes to locked decisions require an explicit reviewed decision-log entry and traceability update.
