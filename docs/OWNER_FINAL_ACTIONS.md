# Owner final actions

1. Treat `https://appsail-50044124045.development.catalystappsail.in/` as the canonical evaluator deployment.
2. Set the following AppSail environment variables (values from your own accounts, never from this repo):
   - `ANVAYA_AI_ASSIST_ENABLED=true` + `ANVAYA_OPENROUTER_API_KEY=<your OpenRouter free-tier key>` — enables LLM-assisted query understanding and grounded NL answers.
   - `ANVAYA_OPENROUTER_MODEL=openrouter/free` (default) and optional `ANVAYA_OPENROUTER_FALLBACK_MODELS` with `:free` models only.
   - `ANVAYA_VOICE_ENABLED=true` + `ANVAYA_SARVAM_API_KEY=<your Sarvam AI key>` — enables Sarvam `saaras:v3` STT, `bulbul:v3` TTS, and `mayura:v1` translation for Kannada/Hindi/English voice.
   - See `deploy/catalyst/env.example` for all placeholder names. Never commit real key values.
   - If you cannot set keys: leave AI/voice flags off. The UI must not claim they are active (landing notices are health-gated).
3. Redeploy **this** portal revision so live AppSail includes: form-first Search, section nav (Briefing / Trends / Chat assist), Case 360 drawer, dossier preview before PDF, network clusters panel, seasonal/MO trends, EN/KN chrome, and Case 360 sources wiring.
4. Commit/push the exact final contents to a **public** GitHub repository and record the commit SHA.
5. Run `.\tools\deploy_catalyst_appsail.ps1 -DryRun`, then `.\tools\deploy_catalyst_appsail.ps1 -ArchiveOnly` in Windows PowerShell.
6. Confirm the generated Docker archive is local-only and ignored by Git.
7. Preserve the private AppSail variables from `deploy/catalyst/env.example`; never copy their values into source or evidence.
8. After deploy, verify `/api/health` and the golden public-demo journey:
   Open public demo → Search filters (or Preview golden query) → Search records → Open Case 360 drawer → Prepare brief → download dossier PDF → Shift Briefing → Crime Trends → ಕನ್ನಡ toggle → logout.
9. Capture safe screenshots of the live URL and health result; never capture secrets, tokens, source payloads or private configuration.
10. Record and publish/unlist the 4–5 minute demo video using `FINALIST_DEMO_SCRIPT.md`.
11. Complete the organiser’s official PPT/template with the GitHub, Catalyst and video links using `FINALIST_PITCH_OUTLINE.md`.
12. Record the final commit SHA and ZIP SHA-256 in `SUBMISSION_EVIDENCE_TEMPLATE.md` before submitting.

See also: `docs/OWNER_SUBMIT_RUNBOOK.md` for a timed checklist.
