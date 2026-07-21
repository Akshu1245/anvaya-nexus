# Finalist pitch outline

Use the organiser’s official presentation template. Keep the main deck to eight slides.

## Slide 1 — ANVAYA NEXUS

Investigator Shift Intelligence: evidence-first conversational crime support for faster, accountable investigation.

Proof points: live AppSail URL, synthetic-only badge, team names, Challenge 01.

## Slide 2 — The investigator’s daily pain

- Natural-language questions must be translated into rigid record searches.
- “What changed?” and “what needs attention?” are answered across disconnected screens.
- Black-box recommendations are unacceptable in high-stakes law enforcement.

## Slide 3 — The workflow

Shift Board → Ask/confirm → Discover → Verify → Prioritise → Preview/export cited brief.

Show one screenshot with the editable interpretation and Shift Intelligence briefing visible.

## Slide 4 — What is genuinely implemented

- English, Kannada, and code-mixed deterministic query interpretation with follow-up context and optional browser voice fallback.
- Policy-scoped FIR retrieval, Case 360, related cases, graph path, and side-by-side comparison.
- Shift Intelligence briefing with volume deltas, unusual-volume flags, quality alerts, and MO co-occurrence leads.
- Source Passport, Record Assurance, grounded brief preview, native cited PDF, masking, and role/purpose controls.

## Slide 5 — Why it stands out

- Evidence trail before eloquence.
- Human confirmation before execution.
- Factual relationships and comparison instead of opaque similarity or guilt scores.
- Daily briefing that answers what changed and what needs review.
- High-stakes safeguards implemented server-side.

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
