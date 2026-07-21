# Safe Feature Replacement and Removal Manifest

**Status:** M7.2D-0 planning only. Nothing in this manifest is removed now. Existing modules remain operational until their FIR replacement passes the listed acceptance gate.

## Global removal rule

Every removal requires: (1) FIR replacement migration and synthetic fixtures, (2) repository/service/API tests including masking and scope, (3) a reachable frontend replacement, (4) report-section migration, (5) acceptance/demo regression, and (6) documentation update. Never combine removal with Catalyst deployment. Keep compatibility adapters only for the shortest tested transition.

| Current module | Current backend/API/UI locations | Data dependencies | Replacement | Safe removal gate | Main regression risk |
|---|---|---|---|---|---|
| Case DNA standalone | `services/intelligence.py:dna`; `api/m3.py:m5_dna`; `repositories/intelligence_requests.py`; `config/case_dna_v1.json`; `docs/case-dna-spec.md`; `features/m5/IntelligencePanel.tsx`; report section `Case DNA Comparisons`; M5 tests | `case_dna_features`, generic `entity_edges`, phones/devices/vehicles | FIR Case Comparison + Related Cases reason labels | D-7 returns transparent typed FIR reasons; comparison route and report section pass policy/masking tests; demo no longer calls DNA | accidental introduction of hidden similarity/guilt language; report compatibility |
| VERIFY standalone | `services/intelligence.py:verify`; `api/m3.py:m5_verify`; query intent/docs; `IntelligencePanel`; report section `VERIFY Findings` | Case DNA helper and generic cases | Record Assurance detail + Case Comparison explanation | D-9 shows all verification checks and comparison gaps as assurance findings; intent/API consumers migrated | broken existing query intent or audit event history |
| Hypothesis Challenge standalone | `services/intelligence.py:challenge`; `api/m3.py:m5_challenge`; `IntelligencePanel`; docs/tests | Case DNA helper; hypothesis text only | investigation notes with structured evidence gaps, or assurance evidence-gap findings | D-9/D-10 replacement is source-backed, notes are append-only/audited, and no free-text SQL-like input path remains | losing useful investigator rationale or audit trace |
| Action Impact Preview | `services/intelligence.py:actions`; `api/m3.py:m5_actions`; `docs/action-impact-spec.md`; `IntelligencePanel`; report section | Case DNA helper and static demo recommendations | none — remove, do not replace with operational actions | all UI/nav/API/report references removed after other replacements; acceptance confirms no automatic action claim | stale route, report section, demo script, or test expectation |
| Generic phone/IMEI/device/vehicle discovery | `phones`, `devices`, `vehicles`, generic `entity_edges`; SEARCH/DISCOVER requests, generator, M3/M4 tests, frontend result reasons | current demo schema and fixture generator | person roles, legal/classification, organisational/court, arrest and authorised location relations | D-7 Related Cases and D-8 graph meet scenario coverage with official FIR relations; old values no longer in demo/report sections | selected-source/policy regression; loss of deterministic related-case examples |
| Generic Case 360 entity tabs | `services/investigation.py:case_360`, generic entity/evidence/forensic reads; `InvestigationExperience.tsx` tabs | generic persons/phones/devices/vehicles/locations/evidence/forensics | typed FIR Case 360 sections | D-6 API and UI display all required FIR sections and preserve Passport/assurance/policy paths | cross-user/jurisdiction masking and empty-state regression |
| Generic Evidence Graph labels/edges | `services/intelligence.py:graph`; `api/m3.py:m5_graph`; graph requests/config/tests | generic `entity_edges` | official FIR relationship set in D-8 | every displayed edge maps to a stored typed source relationship; caps/masking pass | fabricated/reverse edges or changed path cap |

## Files that require deliberate follow-up review

| Area | Files / artifacts to inspect in D-10/D-11 |
|---|---|
| Backend services and API | `backend/anvaya/services/intelligence.py`, `services/investigation.py`, `services/search.py`, `api/m3.py`, repository request/filter types, generator, migration list |
| Frontend | `frontend/src/features/m5/IntelligencePanel.tsx`, `features/m4/InvestigationExperience.tsx`, `features/m6/ReportConsole.tsx`, `frontend/src/api/m3.ts`, `App.tsx`, routing/navigation and all corresponding tests |
| Reports | selected section array, preview metadata/HTML, report lifecycle test fixtures, review and audit assertions |
| Documentation/demo | `docs/case-dna-spec.md`, `docs/action-impact-spec.md`, `docs/query-language.md`, `docs/api-contract.md`, `docs/application-flow.md`, `docs/demo-plan.md`, `docs/project-charter.md`, traceability/decision docs |
| Tests | M3 SEARCH/DISCOVER, M4 Case 360/Passport/path, M5 intelligence, M6 report/acceptance, generator/fixture and policy/masking suites |

## Required compatibility approach

- **Do not delete generic tables in the submission window.** Stop exposing them in final routes only after the FIR fixtures and acceptance flow no longer depend on them. Any physical schema retirement is post-submission.
- Keep existing endpoint envelopes during migration where feasible; introduce typed FIR fields additively and only remove old fields after frontend/report consumers are migrated.
- Preserve audit history as historical facts. Do not rewrite or delete old audit events, report versions, source records, or reviews.
- Retain `source_record_id` links in every new canonical table so Source Passport and transformation history remain valid.
- When an old demo UI disappears, add a short migration note to the demo script rather than concealing removed capability.

## Explicit non-removals before 26 July

Authentication, authorisation, masking, source restrictions, audit, health, reports/reviews, local SQLite, migrations, synthetic generator framework, and the offline Catalyst compatibility foundation are not candidates for removal. Optional AI/Catalyst services are not added merely to replace anything.
