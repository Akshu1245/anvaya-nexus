# ANVAYA NEXUS — Karnataka State Police Datathon 2026

ANVAYA NEXUS is a permission-aware, FIR-focused investigation and data-integrity prototype. The final synthetic demo supports structured FIR search, FIR Case 360, evidence-grounded investigation briefs, factual related cases with counter-evidence, human-reviewed identity links, deterministic assurance findings, source-cited report drafts, and audited report/review workflow. It has no predictive policing, live police-system integration, or required external AI dependency.

> **SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE**

## Final NEXUS demo

The primary UI is the FIR-focused NEXUS workspace. Sign in with a synthetic demo account, search by crime number/person/Act/section, open Case 360, then load the cited Brief, Related Cases, Identity Suggestions, Assurance Radar, factual Graph and printable report draft.

The detailed product boundary is in [`docs/NEXUS_FINAL_SCOPE.md`](docs/NEXUS_FINAL_SCOPE.md). For the live Catalyst gates that cannot be truthfully completed without the authenticated sandbox and official CLI, use [`docs/DEPLOYMENT_AND_SUBMISSION_GATES.md`](docs/DEPLOYMENT_AND_SUBMISSION_GATES.md).

## Prerequisites

- Python 3.11
- Node.js 20+ and npm

No API key or external service is required.

## First-time setup

```bash
python -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements-dev.txt
npm install
npm --prefix frontend install
```

Optionally copy `.env.example` to `.env` and change only local, non-secret values. Defaults use local SQLite.

## Start frontend and backend together

```bash
npm run dev
```

Frontend: `http://localhost:5173`  
Backend health: `http://localhost:5000/api/health`

## Start separately

```bash
python -m flask --app backend.wsgi run --debug --port 5000
npm --prefix frontend run dev
```

Vite proxies `/api` to Flask. Database credentials are never sent to the browser.

## Production-style local build

```bash
npm run build
ANVAYA_ENV=production python -m flask --app backend.wsgi run --port 5000
```

Flask serves `frontend/dist` and the API from port 5000.

## Tests

```bash
npm run test
npm --prefix frontend run lint
npm run build
python -m pytest backend/tests/test_production_frontend.py
```

Or run `sh scripts/check_foundation.sh`.

## M2 synthetic data

All generated identifiers, names, phones, IMEIs, registrations, addresses, cases, and source records are explicitly synthetic.

Small deterministic test dataset:

```bash
npm run seed:test
```

Full target-scale dataset:

```bash
npm run seed:full
```

Reset the local database to a small dataset:

```bash
npm run db:reset
```

The generator uses fixed seed `20260711` unless `python -m scripts.seed_data --scale test --seed NUMBER` is supplied. Generated summaries and the separate test-only ground-truth manifest are written under ignored `data/generated/`.

## Data Readiness

Open the local frontend and select a synthetic `.csv` or `.json` file. Validation is a separate phase: rejected rows are quarantined and no case rows are committed until **Commit accepted rows** is selected.

Example files:

- `data/fixtures/cctns_import_sample.csv`
- `data/fixtures/cctns_import_sample.json`

Equivalent API example:

```bash
curl -F "file=@data/fixtures/cctns_import_sample.csv" http://localhost:5000/api/imports/validate
curl -X POST http://localhost:5000/api/imports/SYN-IMPORT-JOB-ID/commit
```

## M3 demo authentication

Synthetic demo usernames:

- `investigator.demo` — assigned to `SYN-STN-01`, `SYN-DST-01`
- `analyst.demo` — broader pattern scope with masked identifiers
- `supervisor.demo` — Supervisor Review purpose only; no unrestricted SEARCH

The local-only demonstration password comes from `ANVAYA_DEMO_PASSWORD`. `.env.example` contains a clearly synthetic default for local demonstration; replace it outside Git when needed. Passwords are hashed before storage. Authentication uses an expiring, revocable, HttpOnly, SameSite server-side session token. There is no registration or password-reset workflow.

## Access model

Approved purposes are Active Case Investigation, Entity Verification, Pattern Research, Supervisor Review, and Procedural Review. The backend validates role, purpose, jurisdiction, source, operation, masking, and row limit centrally. Client-supplied role, station, district, or masking state is ignored.

- Investigator: full permitted station detail; district candidates are restricted; external candidates are masked.
- Crime Analyst: broader SEARCH with direct identifiers masked.
- Supervisor: authorised review boundary only; M6 Supervisor Review UI is not implemented.
- Court and Prosecution remain unavailable, non-selectable P1 metadata.

## Query Preview and deterministic SEARCH

Create an investigation in the M3 screen, choose permitted sources, enter a query, review/edit its restricted plan, and run SEARCH. Examples:

```text
Find unresolved chain snatching at SYN-STN-01
ಬಗೆಹರಿಯದ ಸರಗಳ್ಳತನ ಜಯನಗರ ತೋರಿಸಿ
Last three months alli Jayanagar hatra similar unresolved chain-snatching cases show maadi.
Find SYN-FIR-000001
Find SYN-IMEI-000000000001
```

The parser uses rules and dictionaries, protects identifiers before normalisation, flags uncertainty, and requires confirmation for ambiguous fields. It does not use an external AI API or generate database commands. SEARCH supports offence, location/station, date, status, FIR/case, phone, IMEI, and vehicle-registration filters.

DISCOVER, VERIFY, and REPORT may be previewed, but execution returns a later-milestone response.

## M3 boundaries

M3 excludes Base44 integration, Case 360, Case DNA, Record Assurance, Evidence Graph, Hypothesis Challenge, Action Impact, reports, Supervisor Review UI, Catalyst, external AI, working Court/Prosecution adapters, real police data, automatic identity merging, and guilt/risk/offender prediction.

## M4 investigation workflow

1. Log in with a synthetic demo account and create or resume an investigation.
2. Use Source Control Centre presets (Case Investigation, Vehicle Verification, Forensic Review, or Custom). The backend revalidates every selection; unavailable Court and Prosecution metadata stays disabled.
3. Enter English, Kannada, or code-mixed text, inspect the editable deterministic Query Preview, then run SEARCH or candidate-only DISCOVER.
4. Use a follow-up inside the same investigation. It inherits applicable date, location, offence, and status constraints; it cannot widen sources, jurisdiction, or limits.
5. Open a result’s Case 360 and source-backed Source Passport. Relationship paths are capped at three hops and 20 nodes.

DISCOVER returns source-backed candidate relationships such as shared IMEI/device, phone, or vehicle. It is not identity confirmation, a Case DNA score, an assurance decision, or an offender/guilt/risk prediction. Seeded/imported trust issues are displayed in Case 360 but are not re-detected in M4.

Degraded mode visibly retains stale/unavailable-source limitations, partial results, permission denials, and bounded-path warnings. The uploaded Base44 prototype remains a visual reference only; its HTML is not part of this application.

## M4 boundaries

M4 excludes Case DNA scoring, Record Assurance detection, Hypothesis Challenge, Action Impact, a full Evidence Graph, reports/PDF export, Supervisor Review UI, Catalyst deployment, voice input, live or Court/Prosecution adapters, external AI, automatic identity merge, and guilt/risk/offender prediction.

## M5 intelligence and assurance

Case DNA uses versioned deterministic weights and reports source-backed factor contributions, conflicts, missing-data limitations, and a 0–100 candidate-similarity band. It is never an identity, guilt, offender, or risk probability. Evidence Graph returns a bounded source-backed subgraph (maximum three hops and 20 nodes) with a textual fallback. Record Assurance displays separate non-mutating findings. Hypothesis Challenge is template-based and does not decide truth. Action Impact is a reversible preview only; it never executes an operational action. VERIFY returns matches, conflicts, missing fields, provenance, masking and confidence limitations without automatic merge. No external AI API is required.

## M6 reports, review, audit, and health

M6 adds an investigator-owned report lifecycle: **DRAFT → IN_REVIEW → CHANGES_REQUESTED → new DRAFT version → IN_REVIEW → APPROVED/REJECTED**. Submitted and approved versions are immutable; review history is append-only. A report owner chooses allowed deterministic sections and can add clearly labelled investigator notes. Report HTML is escaped, source-policy-filtered, print-friendly, and contains the mandatory synthetic prototype watermark.

The selectable sections are Cover, Investigation Summary, Purpose and Scope, Selected Sources, Search Criteria, Retrieved Cases, Candidate Relationships, Case DNA Comparisons, Evidence Graph Summary, Record Assurance Findings, Hypothesis Challenge, Action Impact Preview, VERIFY Findings, Source Limitations, Jurisdiction and Masking Notes, Provenance Appendix, Audit Reference, Reviewer Notes, and Disclaimer.

Assign an eligible synthetic Supervisor before submission. The assigned Supervisor can view only the report-scoped material, request changes, approve, or reject. Changes requested and rejection require a comment; an investigator cannot approve their own report. Supervisor access remains report-scoped and does not grant unrestricted raw-record access.

The Report Console also provides an Audit Dashboard (safe, paginated metadata only) and an authenticated System Health view. Audit events are append-only and exclude passwords, session tokens, and unnecessary raw identifiers. System Health exposes source freshness, the migration version, export capability, and degraded-mode notices without exposing paths, connection strings, environment values, or secrets.

HTML preview is authenticated. Native server PDF generation is deliberately not included; use the visible browser **Print to PDF** control. The export filename is deterministic and sanitised.

## Production and container deployment

Build the frontend first, then start the production server locally:

```bash
npm --prefix frontend run build
export ANVAYA_ENV=production
export ANVAYA_SESSION_SECRET='replace-with-a-unique-32-plus-character-secret-outside-git'
export ANVAYA_ALLOWED_ORIGINS='https://your-host.example'
export ANVAYA_HTTPS_ENABLED=true
gunicorn --bind 0.0.0.0:5000 --workers 2 backend.wsgi:app
```

Production startup fails closed if the session secret is missing/too short or allowed origins are not comma-separated HTTPS origins. Cookies are HttpOnly, Secure when HTTPS is enabled, and SameSite=Strict. The prototype uses same-site cookie APIs rather than cross-site credentialed requests; keep the frontend and API on the same approved origin. Set `ANVAYA_TRUST_PROXY=true` only behind a trusted reverse proxy that supplies correct forwarded headers.

The app applies a 1 MiB default request limit, a separately documented 512 KiB upload limit, and a configurable login-attempt limit. All API errors use structured envelopes and do not expose stack traces. Start-up applies ordered SQLite migrations deterministically. For a container build:

```bash
docker build -t anvaya-m6 .
docker run --rm -p 5000:5000 \
  -e ANVAYA_ENV=production \
  -e ANVAYA_SESSION_SECRET='replace-outside-git-with-32-plus-characters' \
  -e ANVAYA_ALLOWED_ORIGINS='https://your-host.example' \
  -e ANVAYA_DATABASE_URL='sqlite:////data/anvaya.db' \
  -v "$(pwd)/data:/data" anvaya-m6
```

Public health is available at `GET /api/health`; authenticated detail is at `GET /api/system-health`. A non-zero startup exit is intentional for invalid production configuration.

### SQLite backup and restore

Stop the process before copying the database. Back up the configured SQLite file with `cp anvaya_local.db backups/anvaya-$(date +%F).db`; restore with `cp backups/anvaya-YYYY-MM-DD.db anvaya_local.db`. For a deterministic demo reset instead of restoring data, run `npm run db:reset`. Never include generated ground truth, local databases, or secrets in Git.

## Verified M6 acceptance demo

The automated acceptance path seeds the verified test-scale synthetic fixture and uses these actual fixture IDs: `SYN-FIR-000001`, `SYN-CASE-0001`, and `SYN-CASE-0002`.

1. Log in as `investigator.demo`, create an investigation, and select CCTNS, Forensics, and Vehicle sources.
2. Preview the golden Kannada-English query: `Last three months alli Jayanagar hatra similar unresolved chain-snatching cases show maadi.` Then SEARCH `SYN-FIR-000001` and run candidate-only DISCOVER.
3. Open Case 360 and its Source Passport for `SYN-CASE-0001`; inspect Case DNA, Evidence Graph, Record Assurance, Hypothesis Challenge, Action Impact Preview, and VERIFY against `SYN-CASE-0002`.
4. Create a report, assign `supervisor.demo`, submit it, request changes as that Supervisor, create a new version as the Investigator, resubmit, and approve as the assigned Supervisor.
5. Open the authenticated printable report, audit events, and System Health. Degraded-source warnings remain visible. Re-run as the Analyst to observe masked identifiers, and use `SYN-FIR-000002` to observe external-jurisdiction masking.

## Troubleshooting and limitations

- If Flask says the frontend is unavailable, run `npm --prefix frontend run build`.
- If production start-up fails, set a unique 32+ character `ANVAYA_SESSION_SECRET` and HTTPS-only `ANVAYA_ALLOWED_ORIGINS` outside Git.
- Use `npm run db:reset` for deterministic synthetic demo data; no real police data is supported.
- Court and Prosecution are unavailable P1 metadata only; no working adapter exists.
- Prototype authentication is for the datathon only. Action Impact is preview-only. Reports retain current masking, purpose, jurisdiction, and source-policy restrictions.
- Case DNA is similarity—not identity or guilt probability. The product has no facial recognition, automatic identity merge, guilt/risk/offender score, predictive policing, automatic operational action, or external-AI requirement.
