# Submission evidence template

All values below are owner-provided placeholders. Do not invent any value.

| Evidence | Value |
| --- | --- |
| Final Git commit SHA | `a33378f` |
| Final source ZIP SHA-256 | `TBD_OWNER_RECORDS` |
| Public GitHub URL | `https://github.com/Akshu1245/anvaya-nexus` |
| Live Catalyst URL | `https://appsail-50044124045.development.catalystappsail.in/` |
| Health-check timestamp (IST) | `TBD_OWNER_AFTER_REDEPLOY — must show status ok, database ok; record ai_assist_enabled / voice_enabled honestly` |
| Demo-video URL | `TBD_OWNER_RECORDS` |
| Official PPT filename | `TBD_OWNER_RECORDS` |
| Local test command/results | `2026-07-22 portal revision: frontend vitest 43/43 + production build OK; backend key suites green; full backend inventory ~377 tests` |
| Browser and device | `Windows verification host; owner to record final demo browser/version` |
| Known limitations acknowledged | `Synthetic-only; EN+KN UI chrome (Hindi via voice when Sarvam on); deterministic fallback without keys; descriptive trends only; exhibit images in dossier PDF (metadata in Case 360 UI); no forecasting, live KSP/CCTNS, person risk or guilt scoring; AppSail SQLite ephemeral` |
| Rollback confirmation | `TBD_OWNER_RECORDS` |

## Verified product beats for the portal build

1. Landing loads; `/api/health` returns ok.
2. Password-free public demo when enabled (Investigator only).
3. Portal nav: Search / Shift Briefing / Crime Trends / Chat assist.
4. Form filters or Preview → Search records → results list → Case 360 drawer → Prepare brief → dossier PDF.
5. Briefing + trends (seasonality / MO) load from nav.
6. ಕನ್ನಡ | English chrome toggle works; AI/voice only when health flags true.

## Owner still must record

- Redeploy this portal revision to AppSail so the live URL matches the demo script.
- Public GitHub URL and exact commit SHA.
- Timestamped demo video following `FINALIST_DEMO_SCRIPT.md`.
- Official PPT using `FINALIST_PITCH_OUTLINE.md`.
- ZIP SHA-256 and rollback confirmation.
