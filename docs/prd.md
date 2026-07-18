# Product Requirements Document

## Product boundary

ANVAYA is a read-only, permission-aware investigation and data-integrity layer over synthetic CCTNS-style and authorised-source replicas. It does not establish identity, liability, guilt, legal conclusions, or coercive action.

## Users

| Role | P0 need |
|---|---|
| Investigator | Search assigned cases, inspect source-backed relationships, challenge leads, create reports |
| Crime Analyst | Compare patterns across a broader area with sensitive identifiers masked |
| Supervisor | Review reports, audit events, permission denials, and basic source health |

## P0 functional requirements

| ID | Requirement |
|---|---|
| FR-01 | Authenticate three predefined accounts through a prototype adapter. |
| FR-02 | Enforce role, purpose, jurisdiction, source permission, and masking in the backend. |
| FR-03 | Require source selection or an approved preset before retrieval. |
| FR-04 | Accept typed English, Kannada, and Kannada-English code-mixed queries. |
| FR-05 | Show editable intent, filters, entities, time range, protected identifiers, and sources before execution. |
| FR-06 | Support SEARCH, DISCOVER, VERIFY, and REPORT restricted intents. |
| FR-07 | Search by offence, location, time, status, and identifiers. |
| FR-08 | Show selected, searched, stale, unavailable, and excluded sources. |
| FR-09 | Attach reason-for-match and Source Passport to factual results. |
| FR-10 | Provide Case 360 and explainable Case DNA comparison. |
| FR-11 | Render a bounded source-backed graph and textual fallback. |
| FR-12 | Detect missing source, duplicate identifier, invalid chronology, conflicting value, and candidate identity. |
| FR-13 | Show supporting, weakening, conflicting, missing, and alternative-explanation information. |
| FR-14 | Rank verification gaps through a deterministic basic Action Impact panel. |
| FR-15 | Generate a print-ready, source-backed, watermarked HTML report. |
| FR-16 | Log query, selection, view, unmask, export, and denial events. |
| FR-17 | Provide minimal Supervisor Review for reports, audits, denials, and source health. |
| FR-18 | Remain usable without an LLM, unavailable source, graph renderer, PDF, or Catalyst. |
| FR-19 | Validate synthetic CCTNS CSV/JSON imports and report readiness failures. |

## P0 non-functional requirements

- Ordinary local query median below two seconds; graph path median below four seconds.
- Ten consecutive golden-path runs without page or server failure.
- Every factual claim and graph edge has a source-record reference.
- Keyboard access, readable contrast, labelled badges, and graph text alternative.
- Bounded rows, source fan-out, graph depth, visible nodes, report size, and optional model tokens.
- SQLite and Catalyst repositories conform to one interface.
- Synthetic, replica, simulated, unavailable, and future capabilities remain visibly distinguished.

## P1

Voice with editable transcript; small map; advanced Action Impact interaction; synthetic Court and Prosecution adapters; PDF conversion; IPC–BNS cross-reference; expanded Supervisor analytics; downloadable graph fallback; additional assurance rules; optional Catalyst Authentication.

## FUTURE

Custody, SOP/legal, NAFIS, 112, ANPR, digital-evidence, court, prison, forensic, and prosecution operational connectors; controlled and departmental pilots; multi-jurisdiction federation; Policy Learning Engine.

## OUT

Facial recognition; person-risk prediction; predictive policing; guilt scoring; arrest/search recommendations; autonomous policing; automatic identity merge; social-media scraping; live CCTNS/ICJS; full OCR; general legal advice; Neo4j; multi-agent architecture; large crime heatmaps; FIR registration; case-entry forms; complaint portal; generic status tracking; basic keyword product; generic dashboard.
