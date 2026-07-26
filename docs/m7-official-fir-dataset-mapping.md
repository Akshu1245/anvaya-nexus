# Official Police FIR ER Dataset Mapping

**Status:** M7.2D-0 design only. This document changes no schema, code, API, data, or Catalyst resource. The official Police FIR ER design is a source-system contract, not ANVAYA's canonical schema. ANVAYA remains synthetic-only.

**D-1 implementation update (local SQLite):** the existing canonical `persons` table was extended additively with nullable `age_years`/`gender_code` and lifecycle timestamps; `case_person_roles` now records only `COMPLAINANT`, `VICTIM`, and `ACCUSED`. Each role row has a case/person/source-record FK, positive optional sequence, source-record uniqueness, and duplicate-link prevention. Case 360 now exposes additive typed people sections and structured search accepts bounded person name/role filters. Caste, religion, disability, blood group, full DOB, and HR data remain absent. Catalyst remains offline/unwired.

**D-2 implementation update (local SQLite):** `legal_acts`, `legal_sections`, `case_legal_sections`, `case_categories`, `gravity_offences`, `crime_heads`, `crime_subheads`, and `case_statuses` are now source-backed canonical tables. The Act–Section pair is enforced by a composite foreign key, and case classification references are nullable additive fields that preserve legacy `offence`/`status`. Case 360 exposes ordered legal links and inactive-aware classifications; structured Search supports exact legal/classification codes or IDs. Factual Act/Section edges are stored for later graph work. No legal advice, outcome prediction, live Catalyst work, or D-3 entity was added.

**D-3 implementation update (local SQLite):** `arrest_surrender_events`, `arrest_accused_links`, and `chargesheets` are source-backed canonical tables. Database triggers ensure an event can link only to an `ACCUSED` role belonging to that event's case. Case 360 now shows separate arrest/surrender and final-report sections plus deterministic factual timeline entries. Search accepts only allowlisted event/report types and trusted presence flags. No arrest recommendation, legal conclusion, live Catalyst work, or D-4 organisation data was added.

## Current ANVAYA inventory

| Area | Current implementation | Classification |
|---|---|---|
| Authentication, roles, policy, masking, sessions, audit, health | SQLite-backed services/API and React flows | Keep unchanged |
| Investigations, selected sources, query history | `investigations`, JSON selected sources, `investigation_messages` | Keep and extend |
| Search and Discover | generic `cases`, entity edges, deterministic source-backed search/discovery | Keep and extend to FIR fields/reasons |
| Case 360, Source Passport, transformations | generic case/entity/evidence/forensic/trust views and provenance | Keep and extend |
| Evidence Graph, Record Assurance | factual stored generic edges; seeded trust issues | Keep and extend/rewrite against FIR relations |
| Reports, versions, Supervisor review | immutable version and append-only review lifecycle | Keep unchanged; align sections later |
| Catalyst compatibility | SQLite default plus offline fake-backed read adapters; no live transport | Keep and extend after local FIR work |
| Case DNA | weighted similarity over phone/device/vehicle/demo edges | Merge useful transparent comparison into Related Cases; remove standalone after replacement |
| VERIFY | Case-DNA comparison wrapper | Merge into Record Assurance; remove after replacement |
| Hypothesis Challenge | deterministic Case-DNA-backed prompt checks | Merge useful evidence checks into investigation notes/assurance; remove after replacement |
| Action Impact Preview | static verification suggestions | Remove after replacement; no operational-action substitute |
| Phone/device/vehicle-centric paths | current synthetic demo entities and edges | Remove after official person/legal/organisation alternatives pass acceptance |

The present SQLite schema contains generic `cases`, `persons`, `locations`, `entity_edges`, `evidence_records`, `forensic_events`, `trust_issues`, provenance/import tables, auth/investigation/audit tables, and M6 report tables. It does **not** currently contain canonical FIR roles, Act/Section, arrest, chargesheet, organisational, court, or classification tables.

## Dataset gap matrix

Coverage reflects executable canonical support, not merely a similarly named UI field.

| Official source table / fields | Key role | Current ANVAYA equivalent | Coverage | Proposed canonical destination and work | Product impact | Privacy |
|---|---|---|---|---|---|---|
| CaseMaster: CrimeNo, CaseNo, station/unit, dates, status, facts, location | case root | `cases(fir_number, crime_number, station_id, district_id, offence, incident_at, registered_at, status)` | Partial | extend `cases`; retain current canonical ID; add FIR-specific foreign keys and timestamps | Search, Case 360, Related, Graph, Assurance | brief facts/location masked by policy |
| ComplainantDetails | person-to-case role | generic `persons` plus generic edges | Missing | `persons` + `case_person_roles(role=COMPLAINANT)` | Search/360/Related/Graph | name protected; no address/DOB import |
| Victim | person-to-case role | generic `persons` plus generic edges | Missing | `case_person_roles(role=VICTIM)` | Search/360/Related/Graph | authorised/role-masked |
| Accused | person-to-case role | generic `persons` plus generic edges | Missing | `case_person_roles(role=ACCUSED)` | Search/360/Related/Graph/arrest links | no ranking or prediction |
| ArrestSurrender | event | `arrest_surrender_events`, `arrest_accused_links` | Complete | source-backed factual event and accused link | 360 timeline/Graph/Assurance | person and temporary-reference masking |
| Act | legal reference | `legal_acts` | Complete | source-backed legal Act reference | Search/360/Related/Graph/Assurance | public legal metadata |
| Section | legal reference | `legal_sections` | Complete | source-backed Section reference tied to one Act | Search/360/Related/Graph/Assurance | public legal metadata |
| ActSectionAssociation | Act–Section validity | `case_legal_sections` | Complete | ordered source-backed case Act/Section relation | Assurance and import validation | public legal metadata |
| CrimeHeadActSection | classification-to-legal mapping | case links with independent classification FKs | Partial | retain explicit source mapping/assurance validation for later source ingestion | Search/360/Assurance | public classification metadata |
| CrimeHead / CrimeSubHead | classification hierarchy | `crime_heads`, `crime_subheads`, nullable case FKs | Complete | source-backed active/inactive hierarchy | Search/360/Related/Graph/Assurance | public classification metadata |
| CasteMaster / ReligionMaster | sensitive personal attributes | none | Excluded | no canonical intelligence table or filter | none | never ingest/display/use for ranking |
| OccupationMaster | optional descriptive attribute | none | Protected / postpone | no P0 canonical table; may retain only an approved broad label if future legal basis exists | none before submission | avoid unless required; no profiling |
| CaseStatusMaster | status reference | `case_statuses`, nullable case FK; legacy `cases.status` retained | Complete | source-backed active/inactive status reference | Search/360/Assurance | public status metadata |
| Court | hearing court reference | none | Missing | `courts` | Search/360/Related/Graph/Assurance | operational reference only |
| District / State | jurisdiction hierarchy | string IDs in `cases`, `locations`, users | Partial | `districts`, `states`, then controlled FKs | Search/360/Graph/Assurance | geography masking applies |
| Unit / UnitType | police organisation | station string only | Partial | `police_units`, `unit_type` as constrained attribute | Search/360/Related/Graph/Assurance | operational access-controlled |
| Employee / Rank / Designation | registering officer reference | user assignment is not police personnel | Missing | `police_employees`, rank/designation constrained labels, unit FK | Search/360/Related/Graph/Assurance | identifier masked; no HR/payroll fields |
| CaseCategory / GravityOffence | classification | `case_categories`, `gravity_offences`, nullable case FKs | Complete | source-backed active/inactive classification | Search/360/Related/Assurance | public classification metadata |
| ChargesheetDetails | downstream case artefact | `chargesheets` | Complete | source-backed final-report record | Search/360/Graph/Assurance | source/provenance controlled |
| relationship matrix | factual source relations | generic `entity_edges` | Partial | retain `entity_edges` only as a derived projection from typed canonical relations | Related/Graph | no inferred or reverse-fabricated edge |

## Small canonical FIR model

### Identity and roles

`persons(id, display_name, approximate_birth_year?, person_label?, source_record_id, active)` is the one canonical person table. `case_person_roles(id, case_id, person_id, role, sequence_no?, source_role_record_id?, source_record_id)` records only `COMPLAINANT`, `VICTIM`, and `ACCUSED`.

Canonical IDs remain generated synthetic IDs (for example `SYN-PER-*`, `SYN-CPR-*`); source identifiers remain provenance fields and are never exposed as replacement API IDs. Name matching is transparent and conservative: the dataset may not contain a safe universal identity key, so duplicate people are not silently merged. Store a synthetic display name, optional coarse age/birth-year only when necessary for fixture differentiation, and a sequence/person label. Never store caste, religion, blood group, disability, full DOB, real phone numbers, or full addresses.

### Legal and classification

| Canonical table | Minimal columns / constraints |
|---|---|
| `legal_acts` | `id`, `code`, `name`, `active`, `source_record_id`; unique code |
| `legal_sections` | `id`, `act_id`, `code`, `title`, `active`, `source_record_id`; unique `(act_id, code)` |
| `case_legal_sections` | `id`, `case_id`, `act_id`, `section_id`, `source_record_id`; unique `(case_id, section_id)`; validates Section belongs to Act |
| `crime_heads` / `crime_subheads` | id, code, name, active, parent head where applicable |
| `case_categories`, `gravity_offences`, `case_statuses` | id, code, name, active, source record |

Inactive references are retained for provenance but rejected for new synthetic imports and emitted as Record Assurance findings. Act–Section pairs are validated during import and assurance; no free-text legal inference is permitted.

### Arrest, chargesheet, and organisation

`arrest_surrender_events` holds a case FK, `event_type` (`ARREST` or `SURRENDER`), occurred timestamp, unit/officer/court references where the source supplies them, and provenance. `arrest_accused_links` is only added if the source relationship cannot be represented by a direct event/person FK; it must be unique per event/person. `chargesheets` holds case FK, document/final-report type, filed date, court reference, status, and source record.

`states`, `districts(state_id)`, `police_units(district_id, unit_type)`, `police_employees(unit_id, rank_label, designation_label, active)`, and `courts(district_id, active)` are operational references only. They deliberately exclude payroll, promotion, attendance, personal HR, and unnecessary employee attributes.

### Case extensions

Add only these FIR fields to `cases` in a later additive migration: `case_category_id`, `gravity_offence_id`, `crime_major_head_id`, `crime_minor_head_id`, `court_id`, `registering_officer_id`, `incident_from_at`, `incident_to_at`, `information_received_at`, `latitude`, `longitude`, and `brief_facts`. Existing `fir_number`, `crime_number`, `station_id`, `district_id`, `registered_at`, `status`, and `source_record_id` remain compatible until replacements are tested.

## Product mapping

| Product | FIR-backed inputs after delivery | Service-owned controls |
|---|---|---|
| FIR Search | Crime/Case number; role person; Act/Section; classification; status; unit/district/officer/court; chargesheet type; dates | query parsing, policy, masking, deterministic result shaping |
| Case 360 | FIR header/facts; role people; legal/classification; arrests; chargesheet; unit/officer/court; location; provenance; assurance | authorisation, masking, empty states, source links |
| Related Cases | explicit shared person-role/legal/classification/unit/officer/court/arrest/location relation | transparent reason labels; no hidden similarity score |
| Relationship Graph | only typed factual canonical relationships | node/edge shaping, access/masking; no inferred links |
| Record Assurance | referential, lifecycle, legal, geography, and timeline checks | deterministic findings and explanations; no score or automatic correction |

## Catalyst impact per canonical addition

All future Data Store rows preserve ANVAYA synthetic string IDs as unique application columns; Catalyst row IDs stay internal. No resource is created by this document.

| Table family | Primary / foreign references | indexes and uniqueness | join/page risk | transaction / conditional update gate |
|---|---|---|---|---|
| people + role links | string ID; case/person/source FKs | case-role-person uniqueness; case/person indexes | role-search joins and masked name filtering | atomic role import; duplicate protection |
| legal/classification | string ID; Act/Section and case FKs | Act code; `(act, section code)`; case link indexes | Act/Section/search joins | validate pair and active state before link write |
| arrest/chargesheet | string ID; case/person/unit/officer/court FKs | case/date and event-person indexes | timeline joins bounded by case | event and accused link must commit together |
| organisation/court/geography | string ID; hierarchy FKs | district/state, unit/district, court/district indexes | low-risk lookups | reference import order and inactive checks |
| extended cases | case ID; classification/court/officer FKs | CrimeNo/CaseNo scoped uniqueness and search indexes | multi-filter search, stable keyset/offset gate | validate all refs before case import |

Catalyst sandbox gates before any live implementation: supported column/text lengths for `brief_facts`, nullable timestamp behavior, composite uniqueness/index semantics, multi-table joins/IN-lists, deterministic `LIMIT/OFFSET`, conditional update/transaction parity, and storage limits for source payload JSON. SQLite remains default until those checks pass.

## Data boundaries

- Synthetic fixture data only; no official PDF, real FIR, citizen, employee, address, identifier, phone number, or coordinate is committed.
- Names, exact locations, officer identifiers, source payloads, and audit metadata remain protected/masked according to server-side role, jurisdiction, source, and purpose policy.
- Health and logs contain no source payload, credential, endpoint, SQL, raw exception, or sensitive field values.
- There is no predictive policing, suspect/offender ranking, guilt/risk/criminal-likelihood score, arrest recommendation, or protected-attribute use.

## D-6 completion — dataset-focused Case 360

Case 360 now supplies an additive, stable FIR view model in the fixed order: FIR Summary, Incident, People, Acts & Sections, Classification, Police & Court, Arrest / Surrender, Chargesheet / Final Report, Evidence, Timeline, Sources & Provenance, and Data Quality. It reuses the D-1 through D-5 canonical records; policy and masking remain in the service. Case 360 and Source Passport provenance summaries deliberately omit raw source payloads and checksums; they expose only safe source metadata and transformation history. Empty, unavailable, and legacy sections are explicit rather than failing the complete case view.

## D-7 completion — FIR Search and Related Cases

FIR Search now presents identifiers, dates, people/roles, legal/classification, organisation, and operational-event filters as structured, bounded server-validated inputs. Results are FIR summaries rather than generic candidates. Related Cases uses fixed stored reason types: shared role person, Act/Section, unit, court, officer, classification, arrest-linked accused, and a clearly labelled temporal rule (overlap or incident starts within 7 days). Ordering uses fixed reason precedence, direct count, total count, registration time, then case ID. It has no Case DNA score, probability, protected-attribute comparison, or conclusion about guilt/common offenders.

## D-8 completion — FIR Relationship Graph

The primary graph is now a bounded, service-assembled FIR Relationship Graph. Its default view uses source-backed `CASE`, `PERSON`, `ACT`, `SECTION`, `POLICE_UNIT`, `POLICE_OFFICER`, `DISTRICT`, `STATE`, `COURT`, `ARREST_EVENT`, `CHARGESHEET`, `EVIDENCE`/`DOCUMENT`, and `FORENSIC_EVENT` nodes. It emits only factual typed edges, including case-role, Act/Section, organisation hierarchy, arrest/accused, chargesheet, and evidence links. D-7 related cases are an optional projected layer with one explicit factual reason per edge; no Case DNA score is exposed.

The graph is capped at 75 nodes, 150 edges, 10 related cases, and a three-hop deterministic BFS path. Every displayed edge carries safe provenance metadata; source filtering and policy/masking occur before graph assembly. Coordinates, raw source payloads, protected attributes, predictions, risk/guilt labels, and recommendations are excluded. Generic Evidence Graph routes remain compatibility-only until D-11. Live Catalyst joins, provider ordering, graph limits, and schema behavior remain sandbox gates; SQLite is still the only working backend.

## D-9 completion — Deterministic FIR Record Assurance

`trust_issues` is now the single additive materialisation boundary for deterministic FIR assurance. Rule version `fir-assurance-v1` records a stable finding ID from rule, case, affected record, field, and version. The service evaluates only fixed CaseMaster, people/role, legal/classification, organisation, arrest, chargesheet, and provenance conditions. Impossible canonical violations remain staged/rejected source defects; the valid 30-case dataset is never corrupted merely to create a finding.

Severity is fixed: blocking for invalid chronology, scoped-number duplicates, hierarchy/Act–Section mismatch, incomplete coordinates, wrong-case arrest linkage, and invalid final-report type; warning for missing/inactive required references and unavailable provenance; informational for permitted absence/staleness. Findings use only `OPEN`, `ACKNOWLEDGED`, and `RESOLVED`. A rerun updates one stable finding, preserves acknowledgement notes, and reopens a resolved finding only when its deterministic rule fails again. Findings never correct FIR records automatically.

## D-10 completion — Dataset-focused reports and final local journey

The report catalogue now mirrors the canonical FIR model: selected sources, FIR criteria/cases, header/incident, people, legal provisions, classification, organisation/court, operational events, evidence/timeline, related-case reasons, structured graph summary, deterministic Record Assurance, provenance/limitations, masking notes, audit reference, reviewer notes, and disclaimer. Selection order is deterministic; empty selections and markup-like title/notes are rejected. Existing report versions and older section names remain readable through a collapsed legacy compatibility group.

The local preview is responsive and print-oriented. The documented export path is browser **Print → Save as PDF**, not native PDF generation. Primary output excludes legacy sensitive entity values, protected demographics, and raw payloads. This changes no SQLite default or offline Catalyst boundary: live schema, joins, provider limits, credentials, and deployment validation remain D-12 gates.
# D-4 source mapping

`State`, `District`, `UnitType`, `Unit`, `Rank`, `Designation`, `Employee`, and `Court` map to the corresponding canonical D-4 tables. Each imported synthetic reference has a source record and transformation event. Hierarchy validation enforces district→state, unit→district, employee→unit, and court→district consistency; availability is retained with explicit active/inactive flags.
