# Submission readiness checklist

## Source-package readiness

- [x] Form-first Investigation Portal mounted as main App (`InvestigationPortal`).
- [x] Editable query interpretation / FIR filters before Search confirmation.
- [x] Aggregate descriptive trends/hotspots + seasonality/MO with methodology disclosure.
- [x] Case 360 drawer with witnesses, statements, IO; network clusters panel; dossier preview before PDF.
- [x] Case DNA / Action Impact / Nexus labeled or excluded from main UI.
- [x] Public-demo CTA gated by `/api/health.public_demo_enabled` (Investigator-only).
- [x] README, judge defense, pitch outline, and demo script aligned to **portal-first** UI.
- [x] Backend pytest suite and frontend vitest + production build verified locally (2026-07-22 portal revision: frontend **43** tests; backend suite **377** collected in CI inventory).
- [ ] Final commit SHA recorded in `docs/SUBMISSION_EVIDENCE_TEMPLATE.md`.
- [ ] Source ZIP SHA-256 recorded in `docs/SUBMISSION_EVIDENCE_TEMPLATE.md`.
- [x] Synthetic-only and secret-pattern scan expected before push; never commit keys or archives.
- [ ] No credentials, archive, database, generated frontend output, caches or real data are committed.
- [x] Golden journey rehearsed locally: filters → Search → Case 360 drawer → brief preview → PDF; Briefing/Trends load.

## Owner-run live Catalyst evidence

- [x] Live AppSail URL recorded: `https://appsail-50044124045.development.catalystappsail.in/`
- [ ] Confirm live AppSail revision matches **this** portal package; **redeploy required** if hero is still chat-only.
- [ ] Environment variables set without exposing secrets (or AI/voice left off and not claimed).
- [ ] Live `/api/health` flags match UI claims (`ai_assist_enabled` / `voice_enabled`).
- [ ] Live public-demo golden journey recorded on video (`FINALIST_DEMO_SCRIPT.md`).
- [ ] Rollback/disable action confirmed and recorded.

## Organiser submission completeness

- [ ] Public GitHub URL works without authentication.
- [ ] Live Catalyst URL shows portal nav (Search / Briefing / Trends / Chat).
- [ ] Public/unlisted demo-video URL works.
- [ ] Official submission PPT/template is completed with all required links.
- [x] Known limitations are disclosed without claiming unimplemented services.

**Do not submit until redeploy + SHA + video + PPT + evidence template are complete.** See `docs/OWNER_SUBMIT_RUNBOOK.md`.
