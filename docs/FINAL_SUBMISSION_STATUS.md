# Final submission status — evidence-based

## A. Verified locally

- Frontend TypeScript lint, 45-test full suite, focused CSRF/portal regression suite, and production build passed during final verification.
- All 379 backend tests passed, including Case 360 sources, public-demo and cited-PDF regressions.
- The Dockerfile packages the compiled frontend and Flask application together.
- The source is synthetic-only and declares no live KSP/CCTNS connection, predictive policing, risk scoring, guilt finding, or operational recommendation.
- Main App mounts **InvestigationPortal** (form-first Search, section nav, Case 360 drawer, dossier preview).

## B. Included in this source package

- Portal Ask → Discover → Verify → Prioritise → Report workflow (sections + drawers, not infinite chat scroll).
- Policy-controlled FIR retrieval, Case 360, source passport, factual relationships, network clusters, Record Assurance, and native cited dossier PDF.
- Safe public-demo entry (Investigator-only), gated by server-only production configuration.
- Docker Custom Runtime AppSail preparation at `tools/deploy_catalyst_appsail.ps1`.
- Owner action, submit runbook, and evidence templates.

## C. Verified live Catalyst evidence

- Public evaluator URL: <https://appsail-50044124045.development.catalystappsail.in/>
- `/api/health` returned `status: ok`, `database: ok`, and `environment: production` after the final 2026-07-25 IST redeploy.
- The landing page exposes the password-free **Open public demo** Investigator path when `ANVAYA_PUBLIC_DEMO_MODE=true`.
- The deployed asset contains the mounted conversation-PDF, contextual follow-up, and Catalyst CSRF fixes.
- The authenticated live golden path passed: public demo → investigation → preview → one-record FIR search → Case 360 → case dossier PDF (50,491 bytes) → conversation PDF (2,349 bytes).
- Deployed Docker archive SHA-256: `09281344EC05BE55AAF176A1AC7BDD5EC3A001D4BB9784F557AAC793177FEC4E`.

## D. Requires owner action

1. Capture a timestamped browser recording of the complete golden journey using `FINALIST_DEMO_SCRIPT.md`.
2. Record the final source ZIP hash in `SUBMISSION_EVIDENCE_TEMPLATE.md`.
3. Complete the organiser PPT from `FINALIST_PITCH_OUTLINE.md`.
4. Confirm whether the organiser-facing repository should remain `anvaya-nexus` or be mirrored to `anvaya-nexus-final-submission`.

## E. Requires organiser assets

- Public GitHub URL.
- Public/unlisted demo-video URL.
- Completed official submission PPT/template.

## Deployment truth

AppSail Custom Runtime with ephemeral synthetic SQLite is the supported demo path. Do not claim Catalyst Data Store / Auth / API Gateway integration. Optional OpenRouter and Sarvam activate only when AppSail keys and flags are set; otherwise deterministic fallback is the honest story.
