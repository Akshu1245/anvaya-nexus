# Submission evidence template

All values below are owner-provided placeholders. Do not invent any value.

| Evidence | Value |
| --- | --- |
| Deployed application commit SHA | `49e6e54` |
| Final source ZIP SHA-256 | `TBD_OWNER_RECORDS` |
| Deployed Docker archive SHA-256 | `E852C7B4B3B3970A717EF2AF3202338BE3C5D46C2DAB9C21202D42DBFDE28C83` |
| Public GitHub URL | `https://github.com/Akshu1245/anvaya-nexus` |
| Live Catalyst URL | `https://appsail-50044124045.development.catalystappsail.in/` |
| Health-check timestamp (IST) | `2026-07-25 final redeploy — status ok; database ok; environment production; public demo on; AI assist off; voice off` |
| Demo-video URL | `TBD_OWNER_RECORDS` |
| Official PPT filename | `TBD_OWNER_RECORDS` |
| Local test command/results | `2026-07-25: frontend 47/47; TypeScript/build OK; affected backend integration/repository tests 27/27; earlier full backend 379/379; production Docker smoke and real-Chrome live audit OK` |
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

- Timestamped demo video following `FINALIST_DEMO_SCRIPT.md`.
- Official PPT using `FINALIST_PITCH_OUTLINE.md`.
- Source ZIP SHA-256 and rollback confirmation.
- Confirm whether the organiser-facing repository should remain `anvaya-nexus` or be mirrored to `anvaya-nexus-final-submission`.
