# Final submission status — evidence-based

## A. Verified locally

- Frontend TypeScript lint, 50-test full suite, focused browser regression, and production build passed during final verification.
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
- The deployed asset is `index-DNNQcyj7.js`, built from application commit `977a0472437fbcb700a03bc793a14507318ecf7e`.
- The authenticated live golden path passed: public demo → safe demo-query preview → seven-record FIR search → Case 360 → related/graph/cluster/priorities/dossier controls.
- A real Chrome audit also passed the Trends deep-link refresh, Kannada persistence, desktop/mobile action hierarchy, a 390px viewport with no horizontal overflow, and automated WCAG 2.2 A/AA checks with zero landing/Search violations.
- Deployed Docker archive SHA-256: `86BE279F333CF318B2D828005E6D925E2CB331D0645196486925AFFC332447F2`.

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
