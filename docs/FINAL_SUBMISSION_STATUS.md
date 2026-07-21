# Final submission status — evidence-based

## A. Verified locally

- Frontend TypeScript lint, test suite and production build are local verification gates.
- Backend tests, including public-demo and cited-PDF regressions, are local verification gates.
- The Dockerfile packages the compiled frontend and Flask application together.
- The source is synthetic-only and declares no live KSP/CCTNS connection, predictive policing, risk scoring, guilt finding, or operational recommendation.

## B. Included in this source package

- Ask → Discover → Verify → Prioritise → Report prototype workflow.
- Policy-controlled FIR retrieval, Case 360, source passport, factual relationships, Record Assurance, audit/report lifecycle and native cited Case 360 brief PDF.
- Safe public-demo entry, gated by server-only production configuration.
- Docker Custom Runtime AppSail preparation at `tools/deploy_catalyst_appsail.ps1`.
- Owner action and evidence templates.

## C. Verified live Catalyst evidence

- Public evaluator URL: <https://appsail-50044124045.development.catalystappsail.in/>
- `/api/health` returned `status: ok`, `database: ok`, and `environment: production` on 2026-07-21.
- The landing page exposes the password-free **Open public demo** Investigator path when `ANVAYA_PUBLIC_DEMO_MODE=true`.
- Local verification for the winning upgrade: frontend lint/tests/build green (32 tests); analytics + evaluation harness green; full backend suite green after repository-boundary fix.
- **Redeploy required:** the currently live AppSail revision predates Shift Intelligence, stage-gated UI, comparison, priorities, and grounded brief preview.

## D. Requires owner action

1. Push the exact final commit to a public GitHub repository.
2. Redeploy this final source revision to AppSail.
3. Capture a timestamped browser recording of the complete golden journey using `FINALIST_DEMO_SCRIPT.md`.
4. Record the final commit and source ZIP hashes in `SUBMISSION_EVIDENCE_TEMPLATE.md`.
5. Complete the organiser PPT from `FINALIST_PITCH_OUTLINE.md`.

## E. Requires organiser assets

- Public GitHub URL.
- Public/unlisted demo-video URL.
- Completed official submission PPT/template.

## Deployment truth

**Docker archive → Catalyst AppSail Custom Runtime is the only supported final deployment route.** The deployed prototype uses ephemeral synthetic SQLite workflow state inside the AppSail container. Catalyst Data Store, Catalyst Authentication, API Gateway, and separate frontend hosting are not integrated in this source and must not be claimed.

There is intentionally no `catalyst.json`: it would point to a local generated archive or build folder that cannot be committed safely. No credentials or AppSail archive are committed. The evaluator URL above is the canonical deployment evidence; GitHub, video, screenshots, and final hashes remain owner-supplied.
