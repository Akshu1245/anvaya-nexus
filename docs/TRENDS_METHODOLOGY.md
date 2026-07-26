# Aggregate trends methodology

## Purpose

The trends panel and Shift Intelligence briefing answer a narrow question: “What patterns exist in the authorised synthetic FIR records currently available to this investigation?” They are descriptive decision support, not predictive policing.

## Method

1. Re-evaluate the user’s role, purpose, selected sources, station, and district policy.
2. Read source-backed FIR rows in deterministic pages of 25, capped at 500 records.
3. Exclude rows that fail record-level policy.
4. Aggregate counts by incident month, offence, police unit, and recorded status.
5. Suppress offence, police-unit, or status groups with fewer than two records.
6. Compute current-versus-previous incident-month police-unit deltas; suppress absolute deltas below two.
7. Flag unusual monthly volume when a month is at least `max(4, 2× median of earlier months)`.
8. Return the exact record count, source count, date coverage, cap status, suppression count, deltas, anomaly flags, and limitations with every response.

Implementation: `backend/anvaya/services/trends.py` and `backend/anvaya/services/briefing.py`.

## Interpretation rules

- “Hotspot” means higher recorded FIR volume within the selected authorised source scope.
- Deltas describe authorised recorded FIR volume change between adjacent months, not crime prevalence or future risk.
- Volume anomaly flags describe unusual recorded volume versus recent authorised history only.
- Counts may reflect reporting behavior, source coverage, administrative boundaries, or synthetic fixture design.
- No age, gender, caste, religion, income, migration, education, or other protected/socio-demographic attribute is used.
- No person, accused, victim, location, or police unit receives a risk score.
- Stored modus-operandi co-occurrence uses fixture feature labels only and never establishes offender identity.

## Evaluation

Automated tests verify:

- authenticated, owned-investigation access;
- non-empty deterministic monthly and police-unit aggregates on seeded fixtures;
- small-cell suppression;
- briefing determinism and absence of guilt/risk language;
- explicit non-forecasting and protected-attribute limitations;
- safe 404 behavior for an unowned or missing investigation.

For submission evidence, record the tested fixture scale, returned authorised case count, latency, and whether the 500-record cap was reached. Do not report prediction accuracy because the feature does not predict.
