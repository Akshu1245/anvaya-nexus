# Owner submit runbook (24–48h)

Timed checklist for the person with GitHub + AppSail + API keys. Do not invent secrets into the repo.

## Hour 0–2 — Lock the package

1. `git status` — confirm portal files are present (`frontend/src/features/portal/`, `App.tsx`, i18n, Case 360/PDF backend).
2. Local smoke: `npm --prefix frontend run test -- --run` and `npm --prefix frontend run build`.
3. Optional: `python -m pytest backend/tests -q` (full suite is long; at least Case 360 / chat / PDF tests).
4. Commit with a clear message (e.g. `portal realism + submission honesty polish`).
5. Push to **public** GitHub; copy the commit SHA into `docs/SUBMISSION_EVIDENCE_TEMPLATE.md`.

## Hour 2–4 — Redeploy AppSail

1. Set AppSail env from `deploy/catalyst/env.example` (session secret, demo password, public demo, origins).
2. Prefer enabling OpenRouter free + Sarvam; if not possible, leave flags **false** and verify landing does not claim AI/voice are live.
3. `.\tools\deploy_catalyst_appsail.ps1 -DryRun` then `-ArchiveOnly` then `-Deploy` (see `docs/CATALYST_CUSTOM_RUNTIME_DEPLOYMENT.md`).
4. Confirm archive `*.tar` is gitignored and not uploaded to GitHub.

## Hour 4–5 — Live verify

1. `GET /api/health` — `status: ok`, `database: ok`; note `ai_assist_enabled` / `voice_enabled` / `public_demo_enabled`.
2. Clean browser (incognito): open live URL.
3. Confirm **portal nav** (Search / Shift Briefing / Crime Trends / Investigation Chat) — if you still see chat-only as the only workspace, redeploy failed.
4. Golden path: public demo → set offence/status filters → Search records → Open Case 360 → Prepare brief → PDF download → Briefing → Trends → ಕನ್ನಡ toggle → logout.
5. Screenshot health + one portal Search + Case 360 drawer (no secrets).

## Hour 5–8 — Video + PPT + evidence

1. Record 4–5 min video exactly to `docs/FINALIST_DEMO_SCRIPT.md` (100% zoom, no DevTools, no passwords).
2. Publish unlisted/public; paste URL into evidence template.
3. Fill organiser PPT from `docs/FINALIST_PITCH_OUTLINE.md` (GitHub, AppSail, video).
4. Compute ZIP SHA-256 of the submission archive the organiser requires; record it.
5. Dry-run judge Q&A from `docs/JUDGE_DEFENSE.md` once out loud.
6. Tick every box in `docs/submission-readiness-checklist.md`.

## Stop rules

- Do **not** start new ML, Hindi full UI, or CCTNS work after Hour 0.
- Do **not** submit if live URL ≠ this SHA’s portal UI.
- Do **not** show Supervisor login on camera (public demo is Investigator-only; role review hides Supervisor from the picker).
