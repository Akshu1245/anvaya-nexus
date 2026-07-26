# HISTORICAL DESIGN MATERIAL — NOT FINAL DEPLOYMENT INSTRUCTIONS

# M7 Catalyst Phase 4 — AppSail Runtime Preparation

## Scope

This phase prepares a provider-specific, read-only Catalyst Python SDK transport and a Development-only AppSail runtime template. It does not deploy an AppSail service, enable API Gateway, configure Catalyst Authentication, seed rows, access Production, merge, or modify `main`.

## Runtime design

- SQLite remains the default backend.
- Catalyst mode still requires explicit `ANVAYA_STORAGE_BACKEND=catalyst`.
- AppSail runtime selection requires `ANVAYA_CATALYST_RUNTIME=appsail`.
- Catalyst Python SDK initialization occurs from the incoming Flask request before each request.
- The SDK application object is stored only in Flask request context.
- The datastore client accepts only server-owned read requests.
- Writes, row mutation helpers, and unverified query templates fail closed.
- Provider exception details are replaced with safe Catalyst error categories.
- No credential file, token, service-account secret, project ID, or `.catalystrc` value is committed.

## Currently enabled live read slice

Only these source-system operations are rendered into executable ZCQL:

1. bounded source-system list
2. source-system lookup by canonical ID
3. bounded health probe against `source_systems`

The transport maps the live column `source_priority` back to the canonical application field `priority`.

All other repository templates remain unverified and return `CATALYST_CAPABILITY_UNVERIFIED`. In particular, the current live `cases` table schema does not yet satisfy the older broad Case 360 repository contract, so Phase 4 does not claim full application functionality against Catalyst.

## AppSail template

`deploy/catalyst/appsail/app-config.template.json` is a non-deploying template. Before any later authorized deployment:

- copy it to the AppSail source directory as `app-config.json`
- replace the Development project ID placeholder locally
- keep `catalyst_auth` set to `false`
- keep the provider environment as `Development`
- verify the Python 3.11 stack name through the installed CLI
- build the frontend before packaging
- install `backend/requirements.txt` into the AppSail build directory
- confirm no local `.env`, `.catalystrc`, tokens, or credentials are in the build path

The startup command binds Gunicorn to `X_ZOHO_CATALYST_LISTEN_PORT` and starts `backend.anvaya.wsgi:app`.

## Environment variables

Required Development values:

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
- `ANVAYA_CATALYST_PROJECT_ID=<set locally>`
- `ANVAYA_CATALYST_API_BASE=sdk-request-context`

No Production values are authorized.

## Rollback

Because this phase creates no remote resource, rollback is a Git revert of the Phase 4 commits. A later AppSail deployment can be disabled or deleted from the Catalyst console, but that action is outside this phase.

## Test commands

```powershell
py -3.11 -m pytest backend/tests/test_catalyst_sdk_client.py backend/tests/test_catalyst_appsail_runtime.py -q
py -3.11 -m pytest backend/tests -q
```

## Remaining gate before deployment

A later phase must validate the template with the installed Catalyst CLI, package dependencies and the frontend build, perform a Development-only dry inspection, and obtain explicit deployment authorization. No deploy command is authorized by this document.
