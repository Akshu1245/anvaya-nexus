# Submission readiness checklist

## Source-package readiness

- [x] Editable query interpretation gate mounted in the main investigation journey.
- [x] Aggregate descriptive trends/hotspots implemented with methodology disclosure.
- [x] Case DNA / Action Impact labeled as deterministic fixture demo, excluded from main UI.
- [x] Public-demo CTA gated by `/api/health.public_demo_enabled`.
- [x] Final demo scope, README, judge defense, pitch outline, and demo script aligned to shipped UI.
- [x] Full backend suite (338/338), frontend lint, frontend suite (27/27), and production build verified on 2026-07-21.
- [ ] Final commit SHA recorded in `docs/SUBMISSION_EVIDENCE_TEMPLATE.md`.
- [ ] Source ZIP SHA-256 recorded in `docs/SUBMISSION_EVIDENCE_TEMPLATE.md`.
- [x] Synthetic-only and secret-pattern scan run; findings were test fixtures, placeholders, and dependency constants only.
- [ ] No credentials, archive, database, generated frontend output, caches or real data are committed.
- [x] Golden journey rehearsed locally: 7 results; Case 360, related, graph, assurance, trends and PDF returned 200; PDF was `application/pdf` (8,768 bytes); logout returned 200.

## Owner-run live Catalyst evidence

- [x] Live AppSail URL recorded: `https://appsail-50044124045.development.catalystappsail.in/`
- [x] Live `/api/health` result recorded (`status: ok`, `database: ok`, `environment: production`).
- [ ] Confirm the currently live AppSail revision matches this final source package; redeploy if needed.
- [ ] Environment variables set without exposing secrets.
- [ ] Live public-demo golden journey recorded on video.
- [ ] Rollback/disable action confirmed and recorded.

## Organiser submission completeness

- [ ] Public GitHub URL works without authentication.
- [x] Live Catalyst URL works in a clean browser session (landing + health verified).
- [ ] Public/unlisted demo-video URL works.
- [ ] Official submission PPT/template is completed with all required links.
- [x] Known limitations are disclosed without claiming unimplemented services.

Live video, public GitHub, and organiser-template evidence remain owner actions. Source-package and live URL evidence are substantially complete.

This extracted workspace is not yet a Git repository, so commit-level hygiene cannot be proven until the owner initializes/pushes the public repository and reviews `git status`.
