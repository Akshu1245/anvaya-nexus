# Final submission status — evidence-based

## A. Verified locally

- Frontend TypeScript lint, test suite (43 tests) and production build are local verification gates.
- Backend tests, including Case 360 sources, public-demo and cited-PDF regressions, are local verification gates.
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
- `/api/health` returned `status: ok`, `database: ok`, and `environment: production` on 2026-07-21 (pre-portal).
- The landing page exposes the password-free **Open public demo** Investigator path when `ANVAYA_PUBLIC_DEMO_MODE=true`.
- **Redeploy required:** live AppSail must match this portal package before submission. Until then, treat live URL as stale.

## D. Requires owner action

1. Push the exact final commit to a public GitHub repository.
2. Redeploy this portal revision to AppSail (`docs/OWNER_SUBMIT_RUNBOOK.md`).
3. Capture a timestamped browser recording of the complete golden journey using `FINALIST_DEMO_SCRIPT.md`.
4. Record the final commit and source ZIP hashes in `SUBMISSION_EVIDENCE_TEMPLATE.md`.
5. Complete the organiser PPT from `FINALIST_PITCH_OUTLINE.md`.

## E. Requires organiser assets

- Public GitHub URL.
- Public/unlisted demo-video URL.
- Completed official submission PPT/template.

## Deployment truth

AppSail Custom Runtime with ephemeral synthetic SQLite is the supported demo path. Do not claim Catalyst Data Store / Auth / API Gateway integration. Optional OpenRouter and Sarvam activate only when AppSail keys and flags are set; otherwise deterministic fallback is the honest story.
