# ANVAYA NEXUS — KSP Datathon 2026, Challenge 01

> **SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE**

ANVAYA NEXUS is an explainable, evidence-first **Investigator Shift Intelligence** prototype for the Challenge 01 conversational crime-database workflow. It answers “what changed, what needs attention, and what evidence supports it?”, turns a bounded English, Kannada, or code-mixed question into an editable interpretation, retrieves only authorised synthetic FIR records, and guides a user through **Ask → Discover → Verify → Prioritise → Report**.

It is not connected to KSP, CCTNS, or any live police system. It does not predict crime, rank people, establish identity, assess guilt, recommend arrest, or use protected attributes for scoring.

## What the prototype demonstrates

- Stage-gated Shift Intelligence briefing with source health, recorded FIR-volume deltas, unusual-volume flags, quality alerts, network leads, and stored MO co-occurrence labels.
- Editable query preview before any search executes; the golden query is: `Last three months alli Jayanagar hatra similar unresolved chain-snatching cases show maadi.`
- Optional OpenRouter **free-tier** assisted query interpretation and source-grounded answer phrasing (`openrouter/free` + `:free` fallbacks), with schema validation and automatic deterministic fallback.
- Optional Sarvam Kannada/Hindi/English speech-to-text and text-to-speech; browser speech and typing remain progressive fallbacks. The editable confirmation gate remains mandatory.
- Policy, purpose, selected-source, jurisdiction and masking controls enforced by Flask, not the browser.
- FIR Search, Case 360, source provenance, bounded factual relationship view with path highlight, related FIR reasons, side-by-side comparison, verification priorities, timeline and deterministic Record Assurance findings.
- Purpose-scoped descriptive crime trends and recorded police-unit hotspots with small-cell suppression; no forecasting or person scoring.
- Chat-only **synthetic investigation dossier**: sectioned Case 360 preview (FIR, people, acts/sections, officers, arrests, chargesheets, property identifiers, evidence/documents, watermarked synthetic exhibits, timeline, provenance, assurance) plus a multi-page **ReportLab dossier PDF** with DRAFT · HUMAN REVIEW REQUIRED · SYNTHETIC watermarks. Decorative offence SVGs are never used as exhibits.
- Short-lived, HttpOnly, SameSite synthetic sessions. The production public-demo button always grants only the Investigator role and still uses all server-side controls.
- Safe offline resilience: static shell caching only; FIR/API responses are never cached or stored offline.

## Preloaded synthetic case catalogue

ANVAYA ships with a deterministic synthetic fixture (`seed 20260711`). The public-demo deployment and normal local setup use the **test scale: 30 FIR cases across 4 offence types**:

| Offence type | Preloaded cases |
| --- | ---: |
| Chain snatching (`CHAIN_SNATCHING`) | 10 |
| Housebreaking (`HOUSEBREAKING`) | 7 |
| Vehicle theft (`VEHICLE_THEFT`) | 7 |
| Robbery (`ROBBERY`) | 6 |
| **Total** | **30** |

Each offence type has a matching **illustrative SVG icon** shown on landing and FIR result cards (`frontend/public/offence-icons/`). These are symbolic government-style graphics only. No real crime-scene photographs, victim images or live operational media are used, which matches Indian government website image guidance and common police-dashboard practice of colour-coded offence markers.

The 30-case fixture also includes:

- 90 synthetic people, with complainant, victim and accused roles.
- 14 vehicles, 14 phones and 14 devices.
- 12 locations, 20 evidence records, watermarked synthetic exhibits (PNG assets with exhibit ID / SHA-256 / chain status), documents, and 12 forensic events.
- 20 arrest/surrender events and 16 chargesheet/final-report records.
- 6 legal acts, 24 legal sections, 4 case-category records, 3 gravity records and 3 status records (including deliberately inactive references used by assurance tests).
- 2 synthetic states, 4 districts, 8 police units, 12 officers and 5 courts.
- 6 controlled evaluation stories:
  1. Two cases sharing one synthetic IMEI (hard-identifier link).
  2. Two behaviourally similar cases that are intentionally unconfirmed.
  3. A conflicting vehicle-colour record.
  4. A duplicate crime identifier.
  5. An invalid chronology record.
  6. A candidate-person identity conflict.
- Additional seeded assurance conditions including a deliberately missing source.

All identifiers use `SYN-*`; none represents a real FIR, person, officer, police unit or court. The optional **full scale** produces **900 cases**: 228 chain-snatching, 224 housebreaking, 224 vehicle-theft and 224 robbery cases. It is intended for local performance demonstrations, not the default public demo:

```powershell
python -m scripts.seed_data --scale full --reset
```

The fixture source is `backend/anvaya/services/generator.py`; controlled ground truth is described in `data/ground_truth/manifest.json`.

## Architecture

```text
React chat UI → Flask policy/evidence boundary → synthetic SQLite fixtures
     │                     ├→ query preview, confirmation and retrieval
     │                     ├→ Case 360 / provenance / assurance
     │                     ├→ grounded answer / cited brief PDF
     │                     ├→ OpenRouter (optional; validated, fail-to-fallback)
     └─ voice input ───────└→ Sarvam STT/TTS/translate (optional; server-side keys)
```

The final hosting route packages both frontend and backend in one Docker image and deploys it as a Zoho Catalyst AppSail **Custom Runtime**. The final prototype deliberately uses ephemeral synthetic SQLite workflow state inside the container; Catalyst Data Store, Catalyst Authentication, API Gateway and separate frontend hosting are not integrated.

## Local setup

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements-dev.txt
npm install
npm --prefix frontend ci
python -m scripts.seed_data --scale test
```

Start local development:

```powershell
npm run dev
```

Frontend: `http://localhost:5173`  
Backend health: `http://localhost:5000/api/health`

## Local development credentials only

The local development password is the clearly synthetic value in `.env.example` under `ANVAYA_DEMO_PASSWORD`. It is for local development only. Never reuse it for a deployed instance, show it in a video, or place it in Git history.

Local review roles:

- `investigator.demo`
- `analyst.demo`
- `supervisor.demo`

For a public Catalyst demo, set `ANVAYA_PUBLIC_DEMO_MODE=true` and a private random 24+ character `ANVAYA_DEMO_PASSWORD` in AppSail configuration. The browser never receives that password; **Open public demo** creates a normal short-lived Investigator session.

## Verification

```powershell
python -m pytest backend/tests -q
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build
npm run test
npm run build
```

## Production container check

Use unique local values; do not commit them.

```powershell
docker build -t anvaya-nexus:submission .
docker run --rm -d --name anvaya-submission-test -p 8000:5000 `
  -e ANVAYA_ENV=production `
  -e ANVAYA_SESSION_SECRET='replace-with-a-random-32-plus-character-value' `
  -e ANVAYA_DEMO_PASSWORD='replace-with-a-random-24-plus-character-value' `
  -e ANVAYA_PUBLIC_DEMO_MODE=true `
  -e ANVAYA_ALLOWED_ORIGINS=https://localhost `
  -e ANVAYA_HTTPS_ENABLED=true `
  -e ANVAYA_TRUST_PROXY=true `
  anvaya-nexus:submission
Invoke-RestMethod http://localhost:8000/api/health
Invoke-WebRequest http://localhost:8000/
docker rm -f anvaya-submission-test
```

## Catalyst deployment

**Docker archive → Catalyst AppSail Custom Runtime is the only supported final route.**

```powershell
.\tools\deploy_catalyst_appsail.ps1 -DryRun
.\tools\deploy_catalyst_appsail.ps1 -ArchiveOnly
# After confirming the intended Catalyst target:
.\tools\deploy_catalyst_appsail.ps1 -Deploy
```

The generated `*.tar` archive is local-only and ignored by Git. Review [the deployment guide](docs/CATALYST_CUSTOM_RUNTIME_DEPLOYMENT.md), [owner actions](docs/OWNER_FINAL_ACTIONS.md), and [evidence template](docs/SUBMISSION_EVIDENCE_TEMPLATE.md) before submission.

Live evaluator deployment: <https://appsail-50044124045.development.catalystappsail.in/>

## Exact demo journey

1. Open public demo.
2. Ask the golden code-mixed question in the single chat interface.
3. Inspect and, if required, edit the interpreted scope before confirming.
4. Review the grounded answer and bounded FIR result cards.
5. Open Case 360, Source Passport, related cases, relationship view and Record Assurance inside the conversation.
6. Ask for shift briefing or recorded crime trends in the same chat.
7. Ask for a grounded brief / dossier in chat, review the sectioned preview and synthetic exhibit cards, then download the complete case dossier PDF.
8. State the analytical limitations, then logout.

## Known limitations and disclosure

- All records, identifiers and people are synthetic.
- The public AppSail deployment is live; GitHub, video, final commit and organiser PPT evidence still require owner completion.
- The public demo is an Investigator-only synthetic session; privileged review roles remain private local-review functions.
- OpenRouter AI assist and Sarvam multilingual voice are implemented but activate only after the owner supplies server-side AppSail keys and redeploys. Without keys, query interpretation and answers use the deterministic fallback.
- Live KSP/CCTNS ingestion, production identity/SSO, managed persistent storage, financial transaction analysis, socio-economic correlation, validated crime forecasting, operational monitoring, load testing, retention controls and security certification are not implemented.
- The AppSail prototype uses ephemeral synthetic SQLite workflow state; production persistence and disaster recovery remain required.
- The hotspot panel is descriptive FIR-volume aggregation only. It is not crime forecasting or predictive policing.
- The downloadable **synthetic investigation dossier PDF** is a DRAFT for human review. It is not a BNSS/CrPC charge-sheet and not a live CCTNS export. Exhibit images are generated watermarked placeholders with hashes and source IDs; decorative offence icons are never evidence.
- The repository still requires an owner-created final Git commit/public GitHub history, final live redeployment, demo video, organiser PPT and submission evidence hashes.

### Remaining owner actions before judging

1. Add `ANVAYA_OPENROUTER_API_KEY` (free-tier key; set `ANVAYA_OPENROUTER_MODEL=openrouter/free`) and `ANVAYA_SARVAM_API_KEY` only in AppSail environment variables; never commit either key. Redeploy after changing keys.
2. Enable the corresponding feature flags and redeploy the latest frontend/backend build.
3. Verify `/api/health` reports the intended AI and voice flags, then complete the public-demo golden journey.
4. Create and push the final Git commit, record its SHA, capture safe screenshots/video and complete the organiser submission evidence.

See [FINAL_SUBMISSION_STATUS.md](docs/FINAL_SUBMISSION_STATUS.md) and [SUBMISSION_EVIDENCE_TEMPLATE.md](docs/SUBMISSION_EVIDENCE_TEMPLATE.md) for the evidence-based status.
