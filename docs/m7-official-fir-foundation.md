# M7 Official FIR Domain Foundation

This increment starts the dataset-focused rebuild without deleting the tested M0–M6 prototype.

Implemented:

- Migration `005_official_fir_domain.sql`
- Official FIR-shaped canonical entities for case details, person roles, Acts/Sections, units, officers, courts, arrests/surrenders and chargesheets
- Idempotent synthetic-only fixture based on the supplied ER schema
- Authenticated dataset-readiness endpoint
- Dataset-focused case search by crime/case number, person role, Act, Section, unit, court and status
- Dataset-focused Case 360 with people, law, arrests, chargesheets, provenance and transparent shared-person related cases
- Regression tests

New endpoints:

- `GET /api/fir/readiness`
- `GET /api/fir/cases`
- `GET /api/fir/cases/<case_id>/360`

Safety:

- No real police or citizen data is included.
- Protected fields such as caste and religion are not represented in the canonical intelligence model.
- Relationships are factual stored links; no guilt, risk or suspect scores are generated.

Next increment:

1. Replace the old frontend search and Case 360 screens with the new FIR endpoints.
2. Add deterministic official-dataset Record Assurance rules.
3. Add official relationship graph edges and report sections.
4. Implement the Catalyst repository adapter only after sandbox capability validation.
