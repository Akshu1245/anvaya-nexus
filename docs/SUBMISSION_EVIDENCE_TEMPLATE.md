# Submission evidence template

Verified engineering values are recorded below. Owner-only submission assets remain explicit placeholders.

| Evidence | Value |
| --- | --- |
| Deployed application commit SHA | `977a0472437fbcb700a03bc793a14507318ecf7e` |
| Final source ZIP SHA-256 | `TBD_OWNER_RECORDS` |
| Deployed Docker archive SHA-256 | `86BE279F333CF318B2D828005E6D925E2CB331D0645196486925AFFC332447F2` |
| Public GitHub URL | `https://github.com/Akshu1245/anvaya-nexus` |
| Live Catalyst URL | `https://appsail-50044124045.development.catalystappsail.in/` |
| Health-check timestamp (IST) | `2026-07-25 final redeploy — status ok; database ok; environment production; public demo on; AI assist off; voice off` |
| Demo-video URL | `TBD_OWNER_RECORDS` |
| Official PPT filename | `TBD_OWNER_RECORDS` |
| Local test command/results | `2026-07-25: frontend 50/50; TypeScript/build OK; backend 379/379; production Docker smoke OK; live real-Chrome golden journey OK; automated WCAG 2.2 A/AA audit: 0 violations on landing and Search` |
| Browser and device | `Google Chrome on Windows verification host; desktop 1440px and mobile 390px checked with no horizontal overflow` |
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

- Timestamped demo video following `FINALIST_DEMO_SCRIPT.md`.
- Official PPT using `FINALIST_PITCH_OUTLINE.md`.
- Source ZIP SHA-256 and rollback confirmation.
- Confirm whether the organiser-facing repository should remain `anvaya-nexus` or be mirrored to `anvaya-nexus-final-submission`.
