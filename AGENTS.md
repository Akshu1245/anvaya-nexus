# AGENTS.md

## Cursor Cloud specific instructions

ANVAYA NEXUS is a synthetic police-FIR investigation demo: a **Flask** backend (`backend/`, Python) plus a **React + Vite + TypeScript** frontend (`frontend/`). In dev they run as two processes; Vite proxies `/api` → `http://127.0.0.1:5000`. Standard commands live in the root `package.json` scripts and `README.md` — refer to those rather than duplicating them.

### Python venv is required and must be activated before running/seeding
- Backend deps are installed into `.venv` (created by the update script). The npm `dev:backend`/`seed:*` scripts invoke `python` (not `python3`), which only resolves inside the activated venv. Always `source .venv/bin/activate` before running `npm run dev`, `npm run test:backend`, or any `python -m scripts.seed_data`.
- The base VM snapshot already has the `python3.12-venv` apt package installed; the update script does not reinstall it.

### Seed the SQLite database before using the app
- The app needs data to be useful. Seed with `python -m scripts.seed_data --scale test --reset` (creates gitignored `anvaya_local.db` with 30 synthetic FIR cases). Seeding is intentionally NOT in the update script; run it once after setup (the DB file persists in the VM snapshot). Use `--scale full` for 900 cases.

### Running and logging in
- `npm run dev` starts backend (`:5000`) + frontend (`:5173`) together. App: http://localhost:5173, backend health: http://localhost:5000/api/health.
- Local demo login (shown on the login page): Officer ID `investigator.demo`, password `ANVAYA-DEMO-ONLY-2026`. This is a synthetic dev-only credential.
- The mounted main product routes live under `/app/*` (AI Home chat+search, Dashboard, Case detail, Analytics = Shift Briefing + Crime Trends, Reports, Supervisor, Settings, Evidence). The AI-chat search at `/app` reads the generator-seeded `cases` table via the `m3` API (`/api/investigations/...`): type a natural-language query (e.g. "chain snatching FIR records"), submit, then click "Search records"; results feed the Case 360 drawer.

### Non-obvious gotchas
- The `/api/fir/*` "official FIR" (Nexus) endpoints read `fir_case_details`, which the normal seeder does NOT populate (it stays 0, and `/api/fir/readiness` reports `ready: false`). That table is only seeded inside tests via `seed_official_fir_fixture`. This is a separate/legacy feature — the mounted main product uses the `m3` search described above, so an empty `fir_case_details` is expected in normal dev.
- `backend/tests/test_production_frontend.py` requires a production frontend build to exist. Run `npm run build` (creates `frontend/dist/`) before the full backend test suite or that one test fails; all other backend tests pass without it.
- `frontend/src/test/ConversationExperience.test.tsx` (5 tests) is currently failing on `main` (legacy conversation experience). This is pre-existing and unrelated to environment setup; the main-product suites (`InvestigationPortal`, `InvestigationExperience`, etc.) and the full backend suite pass.
- OpenRouter/Gemini AI and Sarvam voice are optional and key-gated; without keys the app uses deterministic fallbacks and works fully offline.

### Lint / test / build (from repo root, venv active)
- Lint (frontend type-check): `npm --prefix frontend run lint`
- Backend tests: `npm run test:backend` (pytest; ~4 min)
- Frontend tests: `npm --prefix frontend run test -- --run` (vitest)
- Production build: `npm run build`
