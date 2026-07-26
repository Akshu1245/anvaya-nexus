# Finalist pitch outline

Use the organiser’s official presentation template. Keep the main deck to eight slides.

## Slide 1 — ANVAYA NEXUS

Investigator Shift Intelligence: evidence-first **KSP-style portal** for faster, accountable investigation (form search + chat assist).

Proof points: live AppSail URL, synthetic-only badge, team names, Challenge 01.

## Slide 2 — The investigator’s daily pain

- Natural-language questions must be translated into rigid record searches.
- “What changed?” and “what needs attention?” are answered across disconnected screens.
- Black-box recommendations are unacceptable in high-stakes law enforcement.

## Slide 3 — The workflow

Portal Search (filters + confirm) → Discover results → Case 360 drawer → Prioritise (briefing / trends / related) → Preview/export cited dossier PDF. Chat assist opens sections — no infinite scroll dump.

Show one screenshot with FIR filters visible and Case 360 drawer or Shift Briefing.

## Slide 4 — What is genuinely implemented

- English + Kannada portal chrome; code-mixed query interpretation; Hindi/voice when Sarvam keys are set.
- Policy-scoped FIR retrieval, Case 360 drawer, related cases, graph, network clusters, and priorities.
- Shift Intelligence briefing with volume deltas, unusual-volume flags, quality alerts, and MO co-occurrence leads; descriptive seasonality (not forecasts).
- Source Passport, Record Assurance, grounded brief preview, native cited PDF, masking, and role/purpose controls.

## Slide 5 — Why it stands out

- Evidence trail before eloquence.
- Human confirmation before execution.
- Factual relationships and comparison instead of opaque similarity or guilt scores.
- Daily briefing that answers what changed and what needs review.
- High-stakes safeguards implemented server-side.
- Government-portal UX judges can navigate without training.

## Slide 6 — Architecture and security

Browser React/Vite → Flask policy and evidence boundary → synthetic SQLite fixtures → Docker/AppSail Custom Runtime.

Call out HttpOnly short-lived sessions, server-side RBAC, masking, audit, bounded queries, and no FIR/API offline caching.

## Slide 7 — Evaluation and limitations

Show only measured test/build results. State:

- synthetic data only;
- deterministic parser and rules, not trained ML;
- descriptive analytics, not forecasting;
- no live CCTNS/KSP integration or person-risk scoring;
- AppSail workflow state is ephemeral;
- optional voice is progressive enhancement only.

## Slide 8 — Deployment and roadmap

Live evaluator URL: <https://appsail-50044124045.development.catalystappsail.in/>

Next validated increments:

1. KSP-approved schema adapter and identity provider.
2. Sandboxed Kannada speech-to-text with measured accuracy.
3. Evaluated semantic retrieval with citation enforcement.
4. Privacy-reviewed socio-economic aggregate datasets.
5. Operational monitoring, persistent managed storage, and red-team testing.

Close: “ANVAYA helps investigators start the shift knowing what changed, what needs attention, and what evidence supports it—without hiding uncertainty or accountability.”
