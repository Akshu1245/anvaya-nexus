# Judge defense: direct answers

## "Where is the AI model?"

ANVAYA uses OpenRouter **free-tier** routing by default (`openrouter/free` plus ordered `:free` fallbacks; ~50 req/day without credits). Keys are configured via AppSail env vars and never committed. Two AI capabilities: (1) `llm_interpret` — turns multilingual investigator questions into a bounded `QueryPlan`; (2) `llm_answer` — phrases a natural-language summary strictly over the policy-filtered, masked records the deterministic search already returned (optional cached `results` avoid re-search). The LLM never accesses the database directly, never bypasses policy or masking, and never invents source record IDs — any ID it emits that is absent from the retrieved set is stripped. Every AI output is validated against an allow-list schema. Bounded retries (short timeouts, 429 brief pause) never burn the free daily quota in a loop. The system works identically without a key: the deterministic parser takes over automatically (fail-closed, feature-flagged). Sarvam AI (`saaras:v3` STT, `bulbul:v3` TTS, `mayura:v1` translation) handles multilingual voice entirely on the server side.

## "How does this satisfy conversational AI?"

ANVAYA is a **form-first KSP-style portal** with a **chat assist**. Investigators type or speak questions in English, Kannada (ಕನ್ನಡ), or code-mixed (Hindi speech when Sarvam is enabled). Optional AI interprets the question into a bounded plan; the officer confirms or edits filters on the Search section before any retrieval. Answers and briefs stay source-cited. Sarvam `bulbul:v3` can read answers aloud when voice is enabled. Chat assist phrases (`shift briefing`, `send me PDF`, `open case SYN-CASE-0001`) open portal sections and drawers — they do not dump Case 360 into an endless transcript. Every AI path shows an engine badge (AI-assisted or Deterministic), cited source record IDs, and a "human review required" notice. Without API keys, the deterministic parser and templates keep the same safety story.

## "Is this predictive policing?"

No. Monthly views, hotspot deltas, and unusual-volume flags describe authorised recorded FIR counts. They do not forecast future crime, estimate prevalence, or score people or locations. Responses include those limitations and use no protected demographic attributes.

## "Are related cases or comparisons evidence of the same offender?"

No. Every edge and comparison field is labeled as a stored or projected factual reason and carries provenance. Shared people, legal provisions, units, time context, or MO feature labels are investigative leads requiring human review, never identity or guilt conclusions.

## "How do you control hallucinations?"

The LLM is bounded: it only phrases text over records the deterministic search already returned; any source record ID it emits is verified against that record set before being surfaced; the system prompt forbids inventing IDs, people, or facts; and the entire AI path falls back to a deterministic templated summary on any error, timeout, or key absence. Query plans reject extra fields and database language. Source scope, policy decisions, masking, uncertainty, and limitations are surfaced throughout.

## "What is Shift Intelligence?"

A policy-scoped daily briefing composed from source health, descriptive volume deltas, unusual volume flags, open Record Assurance findings, factual network leads, and stored MO co-occurrence labels. Every card is review-only.

## "How is sensitive data protected?"

The demo is synthetic. The prototype still enforces role, purpose, source, jurisdiction, result limit, and masking on the server; uses short-lived HttpOnly SameSite sessions; audits sensitive actions; and does not cache FIR/API data offline. AI and voice API keys are server-side only (AppSail env vars, never committed). No audio is persisted — voice input is forwarded to Sarvam and the transcript returned; no audio file is stored. Production identity, managed key storage, data retention, and certification remain future integration requirements.

## "Can it scale to KSP data?"

The workflow and interfaces are separable from the synthetic repository, but production scale is not yet proven. The current AppSail deployment uses ephemeral SQLite. A real rollout requires KSP-approved data contracts, managed persistent storage, indexed search/graph infrastructure, tenancy, observability, load testing, and disaster recovery.

## "What was evaluated?"

Report only measured backend/frontend tests, briefing determinism, seeded defect recall on known cases, golden-query non-empty retrieval, related-case top-five coverage for the hard-ID story, live health response, and golden-journey evidence. Do not repeat unmeasured targets such as 90% intent accuracy.

## "Why should this reach the finals?"

ANVAYA demonstrates a coherent live **government-portal** workflow: form-first search with confirmation, Case 360 drawer with provenance, descriptive briefing/trends (not forecasts), candidate network clusters (not guilt), watermarked dossier PDF, optional AI/voice with fail-closed fallback, and accountable policy/masking. Its strongest competitive position is accountable investigation support — with a full deterministic fallback so the safety story holds even without API keys.

## "Is the PDF a real charge-sheet?"

No. The downloadable artefact is a **synthetic investigation dossier (DRAFT)** generated from policy-filtered Case 360 fields. It is explicitly watermarked `DRAFT · HUMAN REVIEW REQUIRED · SYNTHETIC DATATHON PROTOTYPE`. It is not a BNSS s.193 / CrPC s.173 charge-sheet, not a live CCTNS export, and not court-ready. Missing operational annexures (case diary detail, mahazar, remand/bail chronology, hearing schedules) print as **Not represented in authorised synthetic records** rather than being invented.

## "Are the exhibit images real evidence?"

No. Exhibit images are **generated watermarked synthetic assets** (PNG) with exhibit IDs, SHA-256 hashes, MIME type, collection timestamps, chain-status labels, and source-record IDs. Decorative offence SVGs under `frontend/public/offence-icons/` are category illustrations only and never appear under Evidence / Exhibits / Seizure or inside the dossier PDF.

## "What is still missing?"

Production voice STT validation at scale, full Hindi UI chrome (voice-only when Sarvam on), financial transaction analysis, socio-economic correlation, crime forecasting, live KSP/CCTNS integration / attachment sync, production identity, managed persistent storage, exhibit image thumbnails in Case 360 UI (images embed in dossier PDF), supervisor review console beyond review-only gate, and operational certification. Catalyst read-only mode does not claim full FIR Case 360 / dossier parity with the AppSail SQLite path.
