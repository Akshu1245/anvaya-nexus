# ANVAYA NEXUS - implemented final demo scope

ANVAYA NEXUS is a synthetic-only, explainable FIR intelligence prototype. It is not a police production system and does not access real Karnataka Police, CCTNS, ICJS, court, CCTV, or citizen data.

## Working five-experience demo

1. **Evidence-grounded Investigation Brief** - deterministic statements generated only from the opened FIR record and carrying source-record citations.
2. **Explainable identity-link suggestions** - shared synthetic person-record links list matches, counter-evidence, provenance, and require an explicit human decision. No automatic merge exists.
3. **Contradiction and timeline radar** - deterministic FIR integrity checks are non-mutating and show their source record.
4. **Related cases with evidence/counter-evidence** - stored factual relationships only, with a limitation that they do not establish identity, coordination, guilt, or responsibility.
5. **Source-cited report draft** - authenticated, printable HTML draft with the mandatory synthetic watermark and citations. The existing report lifecycle supports owner drafts, Supervisor review, changes requested, immutable submissions, approval/rejection, and audit events.

## Dataset boundaries

The included fixture contains 24 deliberately selected synthetic benchmark cases and models CaseMaster, person roles, legal acts/sections, units, officers, courts, arrest/surrender events, chargesheets and source provenance. It deliberately excludes protected attributes from intelligence behavior, including caste, religion, disability, blood group and HR data. See [research-led benchmark rationale](RESEARCH_LED_BENCHMARK.md).

## Non-goals

- Predictive policing, suspect ranking, guilt/risk/criminal-likelihood scores, or arrest recommendations.
- Autonomous identity resolution, automated record merging, face recognition, CCTV, OCR, external chatbot/RAG, or unrestricted AI over confidential data.
- Any claim that synthetic fixture behavior is a live-police integration.
