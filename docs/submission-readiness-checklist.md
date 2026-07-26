# Submission readiness checklist

## Source-package readiness

- [x] Form-first Investigation Portal mounted as main App (`InvestigationPortal`).
- [x] Editable query interpretation / FIR filters before Search confirmation.
- [x] Aggregate descriptive trends/hotspots + seasonality/MO with methodology disclosure.
- [x] Case 360 drawer with witnesses, statements, IO; network clusters panel; dossier preview before PDF.
- [x] Case DNA / Action Impact / Nexus labeled or excluded from main UI.
- [x] Public-demo CTA gated by `/api/health.public_demo_enabled` (Investigator-only).
- [x] README, judge defense, pitch outline, and demo script aligned to **portal-first** UI.
- [x] Backend pytest suite and frontend vitest + production build verified locally (2026-07-25: frontend **50/50**; backend **379/379**).
- [x] Deployed application commit SHA recorded in `docs/SUBMISSION_EVIDENCE_TEMPLATE.md`.
- [ ] Source ZIP SHA-256 recorded in `docs/SUBMISSION_EVIDENCE_TEMPLATE.md`.
- [x] Synthetic-only and secret-pattern scan expected before push; never commit keys or archives.
- [x] No credentials, archive, database, generated frontend output, caches or real data are committed (`.env.example` is the only tracked environment template).
- [x] Golden journey rehearsed locally: filters → Search → Case 360 drawer → brief preview → PDF; Briefing/Trends load.

## Owner-run live Catalyst evidence

- [x] Live AppSail URL recorded: `https://appsail-50044124045.development.catalystappsail.in/`
- [x] Live AppSail revision matches deployed application commit `977a047` (`index-DNNQcyj7.js`).
- [x] AI/voice are safely left off and are not presented as enabled.
- [x] Live `/api/health` reports `public_demo_enabled=true`, `ai_assist_enabled=false`, and `voice_enabled=false`, matching the UI.
- [ ] Live public-demo golden journey recorded on video (`FINALIST_DEMO_SCRIPT.md`).
- [ ] Rollback/disable action confirmed and recorded.

## Organiser submission completeness

- [x] Public GitHub URL works without authentication.
- [x] Live Catalyst URL shows portal nav (Search / Briefing / Trends / Chat).
- [ ] Public/unlisted demo-video URL works.
- [ ] Official submission PPT/template is completed with all required links.
- [x] Known limitations are disclosed without claiming unimplemented services.

**Do not submit until the video, PPT, source-ZIP hash and rollback confirmation are complete.** See `docs/OWNER_SUBMIT_RUNBOOK.md`.
