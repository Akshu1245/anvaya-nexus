# HISTORICAL DESIGN MATERIAL — NOT FINAL DEPLOYMENT INSTRUCTIONS

# Catalyst Phase 2 Integration Preparation

Status: code preparation only on `feat/m7-zoho-catalyst-deployment`.

No AppSail deployment, API Gateway enablement, Catalyst Authentication configuration, data seeding, Production access, merge, or `main` modification is authorized or performed by this phase.

## Added integration seams

- `backend/anvaya/repositories/catalyst_schema.py`
  - allows only the seven Development tables validated in Phase 1;
  - maps Catalyst `source_priority` back to canonical `priority`;
  - removes Catalyst system columns (`ROWID`, `CREATORID`, `CREATEDTIME`, `MODIFIEDTIME`) from application records;
  - excludes protected `payload_json` and `brief_facts` fields by default;
  - fails closed for unknown tables and unsafe projection names.
- `backend/anvaya/repositories/catalyst_read_client.py`
  - provides an injected, read-only transport seam;
  - contains no credential acquisition, network SDK initialization, write methods, deployment hooks, or SQLite fallback;
  - uses fixed bounded queries against the unprefixed table names created in the Development sandbox;
  - validates canonical identifiers and limits before transport execution;
  - returns empty results without switching storage backends.

## Tests added

- live table allowlist and provider/canonical mapping;
- `source_priority` aliasing;
- provider system-column removal;
- protected field exclusion and explicit inclusion;
- fail-closed behavior for unknown tables and unsafe columns;
- fixed query table names/order/bounds;
- empty-result behavior with no SQLite fallback;
- invalid ID and limit rejection before transport execution.

## Deliberately not wired

`create_app` continues to reject `STORAGE_BACKEND=catalyst`. SQLite remains the default and only active runtime repository. A future separately authorized phase must provide the official Catalyst SDK/HTTP transport, approved runtime secret handling, live query compatibility tests, and a complete `Repository` implementation before Catalyst can be selected.

## Required local verification

From the repository root:

```powershell
python -m pytest backend/tests/test_catalyst_schema_mapping.py backend/tests/test_catalyst_read_client.py -q
python -m pytest backend/tests -q
npm --prefix frontend run build

git status --short
```

Do not add `.catalystrc`, credentials, project IDs, organization IDs, access tokens, cookies, or console exports to Git.
