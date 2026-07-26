# Focused FIR Product Scope — Submission Plan

**Deadline:** 26 July 2026. **Status:** M7.2D-0 documentation only. This is the binding scope for the remaining build; it supersedes earlier generic-demo priorities where they conflict.

## Submission outcome

ANVAYA will demonstrate a secure, explainable, synthetic FIR case-intelligence workflow: authorised user → selected sources → FIR search → Case 360 → transparent related cases → factual relationship graph → source provenance → deterministic record assurance → reviewed report → audit trail. SQLite remains the working local backend. Catalyst work must be minimum viable deployment only after the local FIR slice is stable and live platform gates are available.

## Scope decisions

| Decision | Features | Rule |
|---|---|---|
| Keep unchanged | authentication, roles, jurisdiction/purpose policy, masking, selected-source controls, query history, audit, health, reports/version immutability/review history, SQLite default, offline Catalyst boundary | Do not regress existing response/security contracts. |
| Keep and extend | FIR Search, Case 360, Related Case Discovery, Relationship Graph, Source Passport, transformation history, Record Assurance, report sections, frontend navigation | Extend from typed FIR data only; retain provenance and source restrictions. |
| Merge | Case DNA comparison → transparent Case Comparison/Related Cases; VERIFY → Record Assurance; useful Hypothesis Challenge evidence gaps → investigation notes/assurance | Replacements must be tested and reachable before the original standalone path is hidden. |
| Remove after replacement | standalone Case DNA, standalone VERIFY, standalone Hypothesis Challenge, Action Impact Preview, phone/IMEI/device/vehicle-centred demo routes and sections | Do not delete in D-0; removal is D-11 only after acceptance gates. |
| Postpone | chatbot/RAG, multilingual AI, OCR, face/voice, NoSQL/cache/signals/circuits/notifications, QuickML/AutoML, custom domain, optional Catalyst extras | No partial implementations before submission. |
| Never build | predictive policing; suspect/offender/guilt/risk/criminal-likelihood score; arrest recommendation; repeat-offender prediction; protected-attribute ranking | These are prohibited in schema, services, UI, reports, tests, and demo language. |

## FIR Search contract

Add only server-validated, policy-scoped filters: Crime Number, Case Number, complainant, victim, accused, Act, Section, category, gravity, major/minor crime head, status, police unit, district, registering officer, court, chargesheet type, registration date, and incident date range. Search continues to use fixed repository operations, source selection, jurisdiction filtering, masking, deterministic ordering, pagination caps, safe errors, query history, and audit.

Excluded filters: caste, religion, disability, blood group, full date of birth, exact unauthorised address/location, employee HR fields, raw source payloads. Related Cases does not emit a similarity score. It returns explicit reason codes only:

`SHARED_ACCUSED`, `SHARED_COMPLAINANT`, `SHARED_VICTIM` (authorised only), `SHARED_ACT`, `SHARED_SECTION`, `SHARED_CRIME_HEAD`, `SHARED_CRIME_SUBHEAD`, `SHARED_UNIT`, `SHARED_OFFICER`, `SHARED_COURT`, `SHARED_ARREST_PERSON`, and `NEAR_LOCATION` (a stated deterministic proximity rule only).

## Case 360 delivery contract

| Section | Repository read | Service/API responsibility | UI and privacy |
|---|---|---|---|
| FIR header and summary | canonical case + source record | scope, status/date formatting, source links | masked identifiers where required; explicit empty state |
| Complainants / victims / accused | role links + persons | authorised role visibility, label/sequence ordering | no protected attributes or full address/DOB |
| Acts, Sections, classifications | legal and classification links | active/inactive notices, deterministic ordering | code/name only; provenance link |
| Arrest / surrender timeline | event + accused links | timeline assembly, chronology warnings | no action recommendation |
| Chargesheet | case chargesheet | document type/status shaping | unavailable/missing warning |
| Unit / officer / court | typed operational references | jurisdiction checks and labels | officer identifier masked if policy requires |
| Incident dates / location / facts | extended case fields | timeline validation and location masking | coarse/masked location when needed |
| Source Passport / transformations | existing provenance reads | source freshness/reliability explanations | no raw payload/URL/credentials |
| Assurance, Related, Graph preview | bounded typed reads | deterministic checks and factual edge shaping | no inferred guilt/risk relationship |

## Factual graph contract

Only source-backed stored/derived-from-stored edges are shown: `CASE_HAS_COMPLAINANT`, `CASE_HAS_VICTIM`, `CASE_HAS_ACCUSED`, `CASE_HAS_ARREST_EVENT`, `ARREST_INVOLVES_ACCUSED`, `CASE_INVOKES_ACT`, `CASE_INVOKES_SECTION`, `CASE_REGISTERED_AT_UNIT`, `CASE_REGISTERED_BY_OFFICER`, `CASE_HEARD_AT_COURT`, `CASE_HAS_CHARGESHEET`, `OFFICER_ASSIGNED_TO_UNIT`, `UNIT_BELONGS_TO_DISTRICT`, and `DISTRICT_BELONGS_TO_STATE`.

Graph services own response shaping, labels, masking, source links, output caps, and warnings. Repositories return fixed typed records only. No reverse-edge fabrication, implicit association, client graph expression, recursive provider query, path persistence, or score is allowed.

## Record Assurance contract

Record Assurance is deterministic and explanatory, not a score or automated enforcement engine. It reports: duplicate CrimeNo; scoped duplicate CaseNo; missing/broken case relations; invalid or inactive Act–Section/classification/status; arrest without case or accused; chargesheet without case or invalid final-report type; officer/unit, court/district, and unit/district/state mismatch; invalid incident/information-received timeline; invalid coordinates; and broken foreign keys. Findings retain safe source references and must never correct a record automatically.

## Privacy and synthetic rules

- Use only generated identifiers, names, addresses, phones, coordinates, source payloads, employee IDs, and facts.
- The Police FIR PDF is never committed. It is a mapping reference, not fixture data.
- Person names, exact locations, officer identifiers, source payloads, and audit metadata are protected by existing masking/policy and never copied into health/logs.
- Caste, religion, blood group, disability, full DOB, and unnecessary HR fields are excluded from canonical intelligence and UI.

## Compact synthetic fixture target

Create in D-5: 30 FIR cases across 4 districts, 8 police units, 12 synthetic officers, 5 courts, 80–120 synthetic people, 6–10 Acts, 20–30 Sections, 20 arrest/surrender events, and 15–20 chargesheets. Seed deliberate transparent links: recurring accused across selected cases; shared complainant/victim only where authorised; shared officer/unit/Act/Section; a deterministic near-location cluster. Seed deterministic assurance defects: duplicate scoped number, invalid Act–Section, inactive reference, arrest without accused, chargesheet missing case, hierarchy mismatch, invalid timeline, invalid coordinate, and broken reference fixture.

**D-1 delivered:** the existing test fixture generator now creates source-backed synthetic complainant, victim, and accused links for the current case set. It includes repeated accused, two accused on selected cases, a repeated complainant, valid no-victim cases, sequence labels, and stored factual `CASE_HAS_COMPLAINANT`, `CASE_HAS_VICTIM`, and `CASE_HAS_ACCUSED` edges. The final 30-case fixture target remains D-5.

**D-2 delivered:** synthetic Acts, concise Sections, categories, gravity levels, crime heads/sub-heads, and case statuses now have source provenance and active/inactive state. Case 360 displays ordered Acts/Sections and classifications while retaining legacy offence/status. Search accepts only exact bounded legal/classification filters. The scope deliberately excludes legal recommendations, sentencing/outcome claims, arrests, chargesheets, courts, officers, and full CaseMaster extensions.

**D-3 delivered:** synthetic arrest/surrender events, their factual accused links, and final-report records are source-backed and displayed as separate Case 360 sections. Timeline entries are factual (`ARREST`, `SURRENDER`, `CHARGESHEET_FILED`, `B_FALSE_REPORT`, and `C_UNDETECTED_REPORT`); Search exposes only allowlisted event/report filters and presence checks. The scope deliberately excludes arrest recommendations, guilt/risk claims, D-4 organisation masters, and live Catalyst operations.

## Delivery guardrails

1. Additive migration and source-backed synthetic fixture first.
2. Repository and service response contract next; test policy/masking/provenance before UI.
3. Show replacement route/section before hiding an old demo module.
4. Keep M7 Catalyst adapter changes separate from local FIR model changes unless a schema manifest is the explicit block.
5. If time is constrained, complete typed Search, Case 360, Related, Graph, Assurance, reports, tests, and a minimum Catalyst deployment path; defer cleanup and optional services.
# D-4 scope update

Organisation data is limited to synthetic operational identity: synthetic unit, district/state, rank/designation, officer display identity, and court. Payroll, home addresses, personal phones, full dates of birth, court-hearing management, judicial prediction, and real personnel data are excluded. Role/jurisdiction masking remains service-owned.

# D-6 scope update

The main Case 360 workspace uses dataset terminology and factual labels only. It shows FIR facts, roles, Acts/Sections, classifications, operational references, arrest/surrender and final-report records, evidence counts, timeline, safe provenance, and existing data-quality issues. It does not expose raw source payloads, make legal recommendations, draw a guilt/risk conclusion, or make Catalyst operational. SQLite remains the default backend.

# D-7 scope update

The visible investigation workflow now calls the factual comparison experience **Related Cases**, not Case DNA. Reason chips identify stored shared records or the fixed temporal context rule; they are not an identity, offender, risk, probability, or guilt assessment. Phone, IMEI, device, vehicle, and legacy DISCOVER routes remain compatibility-only and are not promoted in FIR Search. No protected attribute participates in search or matching.

# D-8 scope update

The visible graph is now **FIR Relationship Graph**, not the generic Evidence Graph. It is a bounded factual relationship list with graph-layer controls and an accessible text fallback: people, Acts/Sections, police/court hierarchy, operational events, evidence, and explained Related Cases projections. It carries source provenance and freshness but never raw payloads, coordinates, protected attributes, a Case DNA score, prediction, guilt/risk framing, or a recommendation. Legacy graph modules remain only in collapsed compatibility tooling until their scheduled removal gate.

# D-9 scope update

The dataset-focused Data Quality section is now **Record Assurance**. It shows transparent deterministic rule findings, fixed severity, lifecycle status, safe observed values, provenance, and no-remediation language. It does not calculate a score, infer guilt/risk, use protected attributes, modify canonical FIR records, or make an operational recommendation. Only Supervisors can resolve a materialised finding; compatibility modules remain collapsed until D-11.

# D-10 scope update

The primary navigation is Investigation Home, FIR Search, Case 360, Related Cases, FIR Relationship Graph, Record Assurance, Reports, and Supervisor Review. Reports use a fixed FIR-focused catalogue, deterministic selected-section order, source and masking notices, a structured graph fallback, assurance rule version, review history, and a browser preview. The supported local export instruction is **Use your browser’s Print → Save as PDF**; ANVAYA makes no native PDF-generation claim.

Primary product output and reports exclude legacy age, gender, phone, IMEI, vehicle, protected demographic, and raw-source-payload values. Legacy compatibility routes and storage remain available only as secondary/collapsed compatibility until D-11. No AI/ML, prediction, score, recommendation, or live Catalyst integration is introduced.

# D-12A scope update

The Catalyst package is offline preparation only: AppSail, Data Store, Authentication, API Gateway, and frontend-hosting choices are documented with fail-closed configuration and validation gates. Fixed fake-backed templates remain test-only; no running Flask application selects them. No Catalyst project, endpoint, token, credential, SDK, schema, seed, transport, or deployment exists. SQLite remains the default and only operating persistence backend.
