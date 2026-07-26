# HISTORICAL DESIGN MATERIAL — NOT FINAL DEPLOYMENT INSTRUCTIONS

# Historical Catalyst-managed AppSail pre-deployment validation — not the final deployment route

> **Superseded for final submission.** Do not use this document's standalone Python command together with the final Docker Custom Runtime deployment. The only supported final route is `tools/deploy_catalyst_appsail.ps1`, documented in `FINAL_SUBMISSION_STATUS.md`.

Status: preparation only. No AppSail deployment, Production access, API Gateway enablement, Authentication configuration, or data seeding is authorized by this phase.

## Locked deployment shape

- Catalyst environment: Development only.
- Runtime: Catalyst-managed Python 3.11.
- Build path: repository root.
- WSGI entry point: `backend.anvaya.wsgi:app`.
- Storage: Catalyst read-only.
- Authentication: existing prototype mode only.
- Frontend: production build generated into `frontend/dist` before packaging.
- Provider credentials and CLI state remain local and untracked.

## Official CLI syntax verified for later use

Catalyst CLI supports both regular AppSail deployment and standalone AppSail deployment. The standalone form accepts `--name`, `--build-path`, `--stack`, and `--command`. The actual deployment command is intentionally recorded but must not be run without a separate deployment authorization.

From the repository root, the later Development-only standalone command is:

```powershell
catalyst deploy appsail standalone --name anvaya-development --build-path (Get-Location).Path --stack "Python 3.11" --command 'gunicorn --bind 0.0.0.0:${X_ZOHO_CATALYST_LISTEN_PORT} --workers 2 --threads 4 --timeout 60 backend.anvaya.wsgi:app'
```

Before any deployment, inspect the installed CLI's accepted values without changing remote resources:

```powershell
catalyst deploy appsail standalone --help
```

If the CLI displays a different exact spelling for the Python 3.11 stack, use the value printed by the installed official CLI. Do not guess or deploy until it is confirmed.

## Local package preparation

Run these commands from the repository root:

```powershell
cd frontend
npm ci
npm run build
cd ..
Copy-Item deploy\catalyst\appsail\app-config.template.json app-config.json
```

Edit only the local `app-config.json` and replace:

```text
REPLACE_LOCALLY_WITH_DEVELOPMENT_PROJECT_ID
```

with the already selected non-production Catalyst Development project ID. Never commit `app-config.json` after inserting a real identifier or environment-specific value.

The historical validator and generated-staging scripts referenced by this archived plan are intentionally not included in the final source package. Use the Docker Custom Runtime route and the regular frontend/backend checks instead.

The validator fails closed when:

- the frontend production build is absent;
- the root or backend requirements entry points are absent;
- the AppSail JSON uses the wrong key names;
- the startup command does not bind `X_ZOHO_CATALYST_LISTEN_PORT`;
- Catalyst mode is not explicitly Development-only and read-only;
- the Development project placeholder remains;
- credential-like files are tracked.

## Local startup smoke test

This uses SQLite by default and does not contact Catalyst:

```powershell
$env:ANVAYA_ENV = "development"
$env:ANVAYA_STORAGE_BACKEND = "sqlite"
$env:X_ZOHO_CATALYST_LISTEN_PORT = "9000"
py -3.11 -m gunicorn --bind 127.0.0.1:9000 backend.anvaya.wsgi:app
```

On Windows, Gunicorn may not run locally because it is a Unix server. In that case use the Flask development server only for local startup validation:

```powershell
$env:FLASK_APP = "backend.anvaya.wsgi:app"
py -3.11 -m flask run --host 127.0.0.1 --port 9000
```

Validate `GET /api/health`, then stop the server. This does not replace AppSail runtime validation.

## Environment-variable checklist

The AppSail Development configuration must contain only these non-secret application settings:

- `ANVAYA_ENV=development`
- `ANVAYA_STORAGE_BACKEND=catalyst`
- `ANVAYA_AUTH_BACKEND=prototype`
- `ANVAYA_ARTIFACT_STORAGE=local`
- `ANVAYA_CATALYST_ENABLED=true`
- `ANVAYA_CATALYST_DATASTORE_ENABLED=true`
- `ANVAYA_CATALYST_AUTH_ENABLED=false`
- `ANVAYA_CATALYST_FILE_STORAGE_ENABLED=false`
- `ANVAYA_CATALYST_RUNTIME=appsail`
- `ANVAYA_CATALYST_ENVIRONMENT=Development`
- Development project ID configured locally
- `ANVAYA_CATALYST_API_BASE=sdk-request-context`
- `ANVAYA_TRUST_PROXY=true`
- `ANVAYA_HTTPS_ENABLED=true`

No token, password, service-account key, private key, `.env`, or `.catalystrc` belongs in the deployable package or Git.

## Rollback and removal plan

After a separately authorized Development deployment:

1. Smoke-test only the Development URL.
2. If startup or health validation fails, disable the AppSail app from the Development console using the app menu and the `DISABLE` confirmation.
3. Preserve logs without copying credentials or request headers into Git.
4. Correct the branch, retest locally, and redeploy only after authorization.
5. If the service must be removed entirely, delete it from the AppSail Development console using the `DELETE` confirmation. Re-creation requires a new deployment.

No Production rollback action is in scope.

## Phase 5 exit criteria

- AppSail package validator tests pass.
- Phase 4 runtime tests pass.
- Full backend suite passes.
- Frontend production build succeeds locally.
- Preflight validator passes against a local, untracked `app-config.json` with the Development project identifier.
- Git working tree is clean after generated artifacts and local configuration remain ignored or untracked outside commits.
- No deployment command has been executed.
