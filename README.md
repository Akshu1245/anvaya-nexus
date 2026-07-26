# ANVAYA NEXUS — KSP Datathon 2026, Challenge 01

> **SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE**

ANVAYA NEXUS is an explainable, evidence-first **Investigator Shift Intelligence** prototype for the Challenge 01 conversational crime-database workflow. It answers “what changed, what needs attention, and what evidence supports it?” through a **Karnataka State Police–style portal**: form-first FIR search with visible filters, sectioned Shift Briefing and Crime Trends, Case 360 in a drawer, dossier PDF preview, and a compact chat assist for natural-language commands.

It is not connected to KSP, CCTNS, or any live police system. It does not predict crime, rank people, establish identity, assess guilt, recommend arrest, or use protected attributes for scoring.

## What the prototype demonstrates

- Government-portal chrome with English + Kannada UI toggle; Hindi speech is available only when Sarvam voice is enabled on the server.
- Form-first Search: always-visible FIR filters, optional NL preview, human confirmation before any retrieval.
- Stage-gated journey (Ask → Discover → Verify → Prioritise → Report) mapped to real portal sections and drawers — not infinite chat scroll.
- Shift Intelligence briefing with source health, recorded FIR-volume deltas, unusual-volume flags, quality alerts, network leads, and stored MO co-occurrence labels.
- Optional OpenRouter **free-tier** assisted query interpretation and source-grounded answer phrasing (`openrouter/free` + `:free` fallbacks), with schema validation and automatic deterministic fallback — only when AppSail keys are set.
- Optional Sarvam Kannada/Hindi/English speech-to-text and text-to-speech; browser speech and typing remain progressive fallbacks. The editable confirmation gate remains mandatory.
- Policy, purpose, selected-source, jurisdiction and masking controls enforced by Flask, not the browser.
- FIR Search results list, Case 360 drawer (people including witnesses, statements, investigating officer, exhibits metadata, Record Assurance), source provenance, bounded factual relationship view, related FIR reasons, verification priorities, and candidate network clusters.
- Purpose-scoped descriptive crime trends (including month-of-year seasonality and MO co-occurrence) with small-cell suppression; no forecasting or person scoring.
- **Synthetic investigation dossier**: sectioned brief preview plus multi-page ReportLab PDF with DRAFT · HUMAN REVIEW REQUIRED · SYNTHETIC watermarks. Exhibit images embed in the PDF; Case 360 shows metadata cards (images are not thumbnails in the UI). Decorative offence SVGs are never used as exhibits.
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
React portal UI → Flask policy/evidence boundary → synthetic SQLite fixtures
     │                     ├→ form search, preview, confirmation and retrieval
     │                     ├→ Case 360 drawer / provenance / assurance
     │                     ├→ briefing / descriptive trends / network clusters
     │                     ├→ grounded brief preview / cited dossier PDF
     │                     ├→ OpenRouter (optional; validated, fail-to-fallback)
     └─ chat assist / voice ─└→ Sarvam STT/TTS/translate (optional; server-side keys)
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

1. Open **public demo** (Investigator-only).
2. Confirm portal nav: **Search**, **Shift Briefing**, **Crime Trends**, **Investigation Chat** (assist), plus About / Helplines.
3. On **Search**, set visible FIR filters (e.g. offence Chain snatching, status UNRESOLVED) *or* paste the golden query and click **Preview**, then confirm **Search records**.
4. Review the results list (not an endless chat dump). Click **Open Case 360** — it opens a drawer.
5. In Case 360: people (including witnesses), statements, investigating officer, exhibit metadata (images embed in the dossier PDF), Record Assurance; optional Related / Graph / Network clusters / Priorities.
6. **Prepare brief** → review the dossier preview modal → download the synthetic investigation dossier PDF.
7. Open **Shift Briefing** and **Crime Trends** from nav (seasonality + MO co-occurrence are descriptive only).
8. Optionally toggle **ಕನ್ನಡ | English** chrome; use Chat assist phrases such as `send me PDF` (opens preview, does not dump Case 360 into scroll).
9. State analytical limitations, then logout.

Golden query (optional NL path): `Last three months alli Jayanagar hatra similar unresolved chain-snatching cases show maadi.`

Legacy chat-only and Nexus workspaces remain in the repo for tests/history; they are **not** the mounted main product (`App` → `InvestigationPortal`).

## Known limitations and disclosure

- All records, identifiers and people are synthetic.
- The public AppSail deployment and GitHub source are live at commit `977a047`; the demo video, organiser PPT and final source-ZIP evidence still require owner completion.
- The public demo is an Investigator-only synthetic session; privileged review roles remain private local-review functions.
- OpenRouter AI assist and Sarvam multilingual voice are implemented but activate only after the owner supplies server-side AppSail keys and redeploys. Without keys, query interpretation and answers use the deterministic fallback.
- Live KSP/CCTNS ingestion, production identity/SSO, managed persistent storage, financial transaction analysis, socio-economic correlation, validated crime forecasting, operational monitoring, load testing, retention controls and security certification are not implemented.
- The AppSail prototype uses ephemeral synthetic SQLite workflow state; production persistence and disaster recovery remain required.
- The hotspot panel is descriptive FIR-volume aggregation only. It is not crime forecasting or predictive policing.
- The downloadable **synthetic investigation dossier PDF** is a DRAFT for human review. It is not a BNSS/CrPC charge-sheet and not a live CCTNS export. Exhibit images are generated watermarked placeholders with hashes and source IDs; decorative offence icons are never evidence.
- The repository and final live redeployment are complete; the owner still needs the demo video, organiser PPT, source-ZIP hash and rollback confirmation.

### Remaining owner actions before judging

1. Add `ANVAYA_OPENROUTER_API_KEY` (free-tier key; set `ANVAYA_OPENROUTER_MODEL=openrouter/free`) and `ANVAYA_SARVAM_API_KEY` only in AppSail environment variables; never commit either key. Redeploy after changing keys.
2. Enable the corresponding feature flags and redeploy the latest frontend/backend build.
3. Verify `/api/health` reports the intended AI and voice flags, then complete the public-demo golden journey.
4. Capture safe screenshots/video and complete the remaining organiser submission evidence.

See [FINAL_SUBMISSION_STATUS.md](docs/FINAL_SUBMISSION_STATUS.md), [SUBMISSION_EVIDENCE_TEMPLATE.md](docs/SUBMISSION_EVIDENCE_TEMPLATE.md), and the timed [OWNER_SUBMIT_RUNBOOK.md](docs/OWNER_SUBMIT_RUNBOOK.md) before judging.
