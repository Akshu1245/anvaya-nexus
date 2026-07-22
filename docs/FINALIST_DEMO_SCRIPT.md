# ANVAYA NEXUS finalist demo script (portal-first)

Canonical URL: <https://appsail-50044124045.development.catalystappsail.in/>

## Before recording

1. Confirm `/api/health` shows `status: ok`, `database: ok`, and `environment: production`.
2. Use a clean browser profile at 100% zoom and 1440×900 or larger.
3. Close developer tools, notifications, password managers, and unrelated tabs.
4. Never show AppSail secrets, cookies, tokens, private role passwords, or raw source payloads.
5. Rehearse the exact journey twice; record the third clean run.
6. Confirm form Search → Case 360 drawer → dossier PDF preview → ಕನ್ನಡ chrome path works.

## Spoken walkthrough

### 0:00–0:25 — Problem and live proof

“Investigators start every shift asking three questions: what changed, what needs attention, and what evidence supports it. ANVAYA is an Investigation Intelligence Prototype on a Karnataka State Police–style portal — synthetic datathon only, not live KSP or CCTNS. Health is green.”

Open **public demo**. Toggle **ಕನ್ನಡ | English** once so the chrome switches, then return to English if needed.

### 0:25–0:55 — Form-first Search

“This is not infinite chat scroll. Top nav opens real sections: Search, Shift Briefing, Crime Trends, Chat assist. On Search I set visible FIR filters — offence, status, station — or paste a golden query and click Preview. I confirm **Search records** myself.”

### 0:55–1:20 — Discover results

“Results appear in a results list, not buried in a transcript. Policy, purpose, sources, jurisdiction and masking stay server-side. Open the first candidate with **Open Case 360** — it opens a drawer overlay.”

### 1:20–2:00 — Verify in Case 360 drawer

“Case 360 shows FIR summary, people including witnesses, statements, investigating officer, exhibits (images embed in the dossier PDF), and Record Assurance. From the drawer I can open Related, Graph, Network clusters, Priorities, then **Prepare brief**.”

### 2:00–2:30 — Briefing / Trends sections

“Nav **Shift Briefing** and **Crime Trends** load authorised analytics. Trends show month-of-year seasonality and MO co-occurrence — descriptive only, never a forecast.”

### 2:30–2:55 — Report PDF

“Prepare brief opens a **preview modal** before download. Download the Synthetic Investigation Dossier (DRAFT). Optionally use Chat assist phrases like ‘send me PDF’ — they open the same preview, they do not dump Case 360 into endless scroll.”

### 2:55–3:15 — Close

“ANVAYA is fail-closed: timeouts, retries, ErrorBoundary, and deterministic OpenRouter free-model fallback. Strong on conversation assist, decision support, explainability, and governance; partial on network clusters and descriptive trends; intentionally out of scope for sociology, finance, forecasting, and person-risk.”

## Phrases to show on camera

- Form filters: offence `Chain snatching`, status `UNRESOLVED`, then Search
- Nav: Shift Briefing / Crime Trends
- Chat assist: `send me PDF`, `Open case SYN-CASE-0001`
- Language: ಕನ್ನಡ chrome toggle

## Guardrails to say once

“Synthetic data only. No live CCTNS. No guilt, risk, or identity inference. Human review required.”
