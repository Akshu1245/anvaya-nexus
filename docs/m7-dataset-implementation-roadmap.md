# M7.2D FIR Dataset Implementation Roadmap

**Status:** M7.2D-0 planning only. All dates are deadline priorities, not a claim that later blocks have begun. “Catalyst” means manifest and sandbox-preparation work only until explicit credentials and permission are provided.

## Ordered blocks

| Block | Scope | Schema / fixture / repository | Service / API / frontend | Tests, privacy, non-goals | Dependency / complexity / priority |
|---|---|---|---|---|---|
| D-1 | Persons and case-person roles | Add `persons` compatibility fields only if needed; add `case_person_roles`; synthetic complainant/victim/accused records; fixed reads/filters | typed role reads; Case 360 role section placeholder; no matching inference | role uniqueness, source provenance, masking, cross-scope denial; exclude protected attributes | D-0; **MUST**, medium |
| D-2 | Acts, Sections, classifications | `legal_acts`, `legal_sections`, `case_legal_sections`, heads/subheads/categories/gravity/statuses; legal fixtures | validation services; basic FIR legal/classification API fields | valid/inactive Act–Section and FK tests; no legal advice/inference | D-1 optional; **MUST**, medium |
| D-3 | Arrests and chargesheets | event/link and `chargesheets` tables; synthetic timeline fixtures | typed event and chargesheet reads; timeline API fields | no case/accused, final-report type, chronology checks; no arrest recommendation | D-1/D-2; **MUST**, medium |
| D-4 | Organisation and court references | states/districts/units/officers/courts; small operational fixture hierarchy | reference lookup and case linkage reads | hierarchy/mismatch/masking tests; no payroll/HR/court scheduling | D-1; **MUST**, medium |
| D-5 | CaseMaster extension and complete fixtures | additive `cases` fields, indexes and scoped uniqueness; all 30-case synthetic fixture scenarios | importer/generator mapping and compatibility response fields | fixture determinism, provenance, coordinate/timeline validation; no real data | D-1–D-4; **MUST**, high |
| D-6 | FIR Case 360 | no unrelated schema; repository aggregation reads for typed rows | FIR header/summary, persons/legal/classification/timeline/organisation/court/chargesheet/provenance/assurance frontend sections | policy/masking, empty states, deterministic ordering, source links; no removal of old view yet | D-1–D-5; **MUST**, high |
| D-7 | FIR Search and Related Cases | search indexes only as justified; fixed typed repository filters/reasons | FIR filter API and UI; transparent related reason output | all filters, selected-source and jurisdiction tests; no similarity score | D-1–D-5; **MUST**, high |
| D-8 | Official relationship graph | typed source-backed edge projection / optional derived `entity_edges` compatibility | factual FIR graph and bounded preview | edge source/provenance, caps, masking, no fabricated reverse/path edges | D-1–D-5; **MUST**, high |
| D-9 | Dataset Record Assurance | no score table required; deterministic validation reads | FIR assurance findings, optional investigation-note evidence-gap display | each listed validation rule, no auto-fix/prediction | D-1–D-5; **MUST**, high |
| D-10 | Reports and frontend alignment | no lifecycle change; update report section choices/fixtures | final FIR navigation, 360/search/graph/assurance reporting sections | supervisor review and old-version regression; no standalone removals until pass | D-6–D-9; **MUST**, medium |
| D-11 | Obsolete feature removal | no destructive table migration | hide/remove legacy standalone APIs/UI/docs/tests after replacements | removal manifest gates, acceptance and audit/report compatibility | D-10; **SHOULD**, medium |
| D-12 | Catalyst schema-manifest update | update Data Store manifest only; no resource creation | map new repository table contracts; no Flask wiring | offline manifest/unit tests; no ZCQL/live SDK | D-1–D-5; **SHOULD**, medium |

## Per-block delivery checklist

Every implementation block must contain only its listed schema migration(s), deterministic synthetic fixtures, named repository methods, service policy enforcement, API envelope changes, smallest frontend slice, targeted tests plus full regression, privacy review, and documentation. It must state non-goals and leave Catalyst default selection unchanged. No block may accept client SQL/ZCQL/order/table fields, raw source payloads, credentials, or real data.

### D-1 completion record

Completed locally in the D-1 commit: migration `005_fir_people_roles.sql`; source-backed deterministic role fixtures; `find_person`, case role/list, and bounded case-level name-search repository methods; additive Case 360 `complainants`, `victims`, and `accused` sections; structured `person_name`/allowlisted `person_role` Search filters; role edges; frontend Case 360 sections; and focused contract/API/privacy tests. No legal/classification/arrest/chargesheet/organisation work, live Catalyst work, legacy deletion, or fuzzy identity matching was included. D-2 remains the next dataset block.

### D-2 completion record

Completed locally in the D-2 commit: migration `006_fir_legal_classifications.sql`; eight source-backed legal/classification tables; nullable additive case references; database-enforced Section-to-Act consistency; deterministic synthetic legal/classification fixtures; fixed repository reads; Case 360 legal/classification sections; exact bounded Search filters; stored `CASE_INVOKES_ACT` and `CASE_INVOKES_SECTION` edges; focused tests and a small FIR filter UI. Existing legacy offence/status, people roles, reports, audit, and offline Catalyst boundary remain compatible. D-3 arrests, surrender events, accused links, and chargesheets remain next.

### D-3 completion record

Completed locally in the D-3 commit: migration `007_fir_arrests_chargesheets.sql`; source-backed arrest/surrender events, accused links, and chargesheets; trigger-enforced same-case ACCUSED links; deterministic fixtures with arrest, surrender, multi-accused events, all three final-report types, and provenance; fixed repository reads; Case 360 operational-event and chargesheet sections; factual timeline entries; exact bounded event/report Search filters; and stored `CASE_HAS_ARREST_EVENT`, `ARREST_INVOLVES_ACCUSED`, and `CASE_HAS_CHARGESHEET` edges. Reports remain backward compatible because existing immutable snapshots tolerate absent or additive case data. No recommendations, live Catalyst work, or D-4 organisation data was included.

## Final product plans

### Search

Repository requests use fixed fields and fixed ordering only: CrimeNo, CaseNo, authorised role-person name, Act, Section, category, gravity, major/minor crime head, status, unit, district, officer, court, chargesheet type, registration date, and incident range. Server policy applies selected sources, role, jurisdiction, masking, result cap, and deterministic ordering before shaping. Caste, religion, disability, blood group, full DOB, HR data, raw addresses, and raw payload filters are absent.

### Related Cases and Case Comparison

The service returns an ordered set of case references with one or more source-backed reason codes: `SHARED_ACCUSED`, `SHARED_COMPLAINANT`, `SHARED_VICTIM`, `SHARED_ACT`, `SHARED_SECTION`, `SHARED_CRIME_HEAD`, `SHARED_CRIME_SUBHEAD`, `SHARED_UNIT`, `SHARED_OFFICER`, `SHARED_COURT`, `SHARED_ARREST_PERSON`, and `NEAR_LOCATION`. It explains only observed deterministic relations, not identity, likelihood, guilt, risk, or a predicted action.

### Graph

Node types: CASE, PERSON, ARREST_EVENT, ACT, SECTION, POLICE_UNIT, OFFICER, COURT, CHARGESHEET, DISTRICT, STATE. Edges are exactly the factual relationship list in `m7-focused-product-scope.md`; each carries a canonical source relation and source-record reference. Bounded traversal/cycle prevention stays in service code and must not rely on unverified provider recursion.

### Assurance

Implement checks for duplicate CrimeNo, scoped CaseNo duplicate, orphan rows, invalid/inactive Act–Section/classification/status, arrest/case/accused failures, chargesheet/case and final-report failure, organisational/court/geography mismatch, incident/information timestamp order, coordinate bounds, and broken FKs. Return severity and explanation, no score, no prediction, and no automatic correction.

## Synthetic acceptance dataset

The D-5 generator produces exactly a compact deterministic dataset: **30 cases, 4 districts, 8 units, 12 officers, 5 courts, 80–120 people, 6–10 Acts, 20–30 Sections, 20 arrest/surrender events, and 15–20 chargesheets**. It includes:

1. A standard authorised FIR with all Case 360 sections.
2. Related cases for every transparent reason family, without relying on phone/device/vehicle data.
3. External-jurisdiction person/location records that visibly mask.
4. Unavailable/stale source provenance.
5. Intentional deterministic Assurance defects: duplicate number, invalid Act–Section, inactive reference, arrest without accused, orphan chargesheet fixture, hierarchy mismatch, invalid time order, invalid coordinate, broken FK.
6. Investigator/Supervisor report-review path using FIR sections, immutable versions, and safe audit events.

## Catalyst schema-manifest requirements (D-12 only)

| Canonical family | expected columns / keys | query and storage risk | required sandbox validation |
|---|---|---|---|
| cases | synthetic string ID; scoped Crime/Case numbers; FKs; timestamps; `brief_facts`; coordinates | composite unique/index, text size, date ordering | type lengths, nulls, indexed filters, conditional uniqueness |
| persons + roles | synthetic IDs, case/person/source FKs, role/sequence | person-role joins and name index | joins/IN-list, duplicate link protection |
| legal/classification | code/name/active/FKs | Act–Section and case joins | composite uniqueness and active filters |
| arrests/chargesheets | case/person/organisation/court FKs and dates | timeline joins, multi-row atomic import | transaction/partial-failure/retry parity |
| organisation/geography | hierarchical FKs, active flags | reference joins | import order and integrity behavior |

No table, schema bootstrap, ZCQL, SDK, credential, endpoint, project/environment ID, or Catalyst resource is created by D-0. Live deployment cannot start until a target project, minimum service identity, platform decisions, and sandbox verification are explicitly authorised.

## Deadline priority

**Must before submission:** D-1 through D-10 plus a minimum, explicitly authorised Catalyst deployment path. **Should:** D-11 and D-12. **Only if time remains/post-submission:** optional AI/OCR, advanced Catalyst extras, broad cleanup, schema retirement, non-essential UI polish. On 26 July, submit only; do not start major development.

## D-6 complete — dataset-focused Case 360

D-6 is a service/API-shape and frontend presentation milestone, not a schema or Catalyst milestone. It adds a fixed FIR-oriented section order, a sticky FIR summary, structured people/legal/classification/organisation/event cards, safe provenance summaries, factual timeline rendering, data-quality display, and section-level empty/degraded states. D-7 remains the next gap: FIR Search and transparent Related Cases redesign.

## D-7 complete — FIR Search and transparent Related Cases

D-7 adds the bounded repository fact read, service-owned factual reason grouping/masking/order, an investigation-scoped related-cases API, safe audit events, FIR result cards, and a Related Cases panel. `FIR_SEARCH_EXECUTED` and `RELATED_CASES_VIEWED` record only filter categories, source selection, base-case ID, and result counts. The legacy DISCOVER and Case DNA routes remain compatible but are no longer the primary visible workflow. D-8 remains the official graph replacement gap.

## D-8 complete — FIR Relationship Graph

D-8 adds a bounded graph response and accessible structured graph panel to the existing investigation workflow. The service assembles fixed factual FIR nodes and edges from the completed D-1 through D-7 records; it does not introduce a graph database, dynamic query language, or speculative relationship. `FIR_GRAPH_VIEWED` and `FIR_RELATIONSHIP_PATH_VIEWED` audit only case, source-selection, layer/result-count, request, and hop metadata. A deterministic authorised path is limited to three hops and reports a clear no-path state.

The frontend keeps official FIR layers enabled by default and legacy graph compatibility collapsed. It provides node/edge details, provenance/freshness, masking indicators, caps/truncation feedback, layer controls, and a text fallback. D-9 remains the next gap: materialised deterministic Record Assurance findings.

## D-9 complete — deterministic FIR Record Assurance

D-9 adds a bounded case-level evaluator, idempotent issue materialisation, investigation-scoped assurance API, source-safe finding shape, supervisor-only acknowledgement/resolution actions, and audit events for execution and status changes. Case 360 now presents **Record Assurance** in its Data Quality section with severity/status totals, deterministic rule version, factual explanation, affected record, and safe provenance. Legacy VERIFY, Hypothesis Challenge, and Action Impact Preview remain compatibility-only until D-11.

## D-10 complete — FIR reporting and product alignment

D-10 makes the dataset-focused route the primary local experience: Investigation Home → FIR Search → Case 360 → Related Cases → FIR Relationship Graph → Record Assurance → Reports → Supervisor Review. The report composer supplies a deterministic FIR section catalogue and keeps legacy section names in a collapsed compatibility group. It rejects empty section sets and unsafe title/note markup, preserves immutable submitted versions, selected-source snapshots, masking notices, and existing review/audit behavior.

The browser preview is print-friendly and explicitly directs users to **Print → Save as PDF**; no native PDF dependency or generation claim is made. Primary navigation and documentation use FIR terminology. Empty, loading, restricted, stale, unavailable, and partial-data states remain explicit. D-11 is optional legacy cleanup; D-12 remains the separately authorised Catalyst deployment preparation gate.

## D-12A complete — offline Catalyst deployment package

D-12A adds only reviewable offline artifacts: service/topology choice, Data Store and fixed-query manifests, placeholder environment declaration, AppSail and frontend-hosting preparation, authentication/Gateway/write plans, privacy rules, rollback/smoke/live-validation/submission checklists. Every Data Store constraint, join, transaction, pagination, hosting syntax, Authentication, Gateway, and deployment behavior remains a live sandbox validation gate. SQLite remains the sole working backend; no live transport, SDK, credential, resource, or deployment is introduced. D-11 remains deferred and D-12B requires explicit authorization.

No AI/ML, probability, score, automatic correction, legal conclusion, or recommendation is used. D-10 remains the next gap: final reports and frontend completion.
# D-4 completion — FIR organisation, officers, courts and geography

M7.2D-4 adds synthetic-only `states`, `districts`, `police_unit_types`, `police_units`, `police_ranks`, `police_designations`, `police_employees`, and `courts`. Cases, arrest/surrender events, and chargesheets now carry additive canonical references while legacy station/district/reference fields remain compatible. Case 360 exposes the organisation snapshot; Search supports exact state, district, unit, officer, and court filters. The factual graph now contains case-to-unit/officer/court and hierarchy edges. D-5 CaseMaster field completion remains next.
