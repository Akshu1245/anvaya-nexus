# HISTORICAL DESIGN MATERIAL — NOT FINAL DEPLOYMENT INSTRUCTIONS

# M7 Catalyst Phase 3 — Read-only application wiring

## Scope

This phase wires the existing fixed-template Catalyst read-only repository into the Flask application factory. It does not deploy AppSail, create or seed data, enable API Gateway, configure Catalyst Authentication, access Production, or add provider write operations.

## Selection rules

- SQLite remains the default storage backend.
- Catalyst is selected only when `ANVAYA_STORAGE_BACKEND=catalyst` and the Catalyst feature flags are explicitly enabled.
- The provider environment must be explicitly non-production (`Development`, `dev`, or `sandbox`).
- Project and API-base metadata must be present.
- A trusted bootstrap layer must inject an object implementing the Catalyst datastore client protocol.
- The application does not read provider credentials or construct a live client from environment variables.
- Missing or invalid Catalyst configuration stops startup; there is no SQLite fallback.

## Runtime behavior

- Catalyst mode instantiates `CatalystReadOnlyRepository` through `CatalystReadGateway`.
- Local source-registry and prototype-user seeding are skipped.
- Health checks use the injected client.
- Fixed, server-owned read templates remain the only query path.
- Unsupported lifecycle and write operations fail with a service error.
- Catalyst Authentication remains unavailable and fails closed if selected.
- Production Catalyst mode remains prohibited.

## Test coverage

`backend/tests/test_catalyst_app_wiring.py` covers:

- SQLite remaining the default;
- explicit read-only repository selection;
- empty provider results;
- health integration;
- missing-client failure;
- Production and provider-environment rejection;
- unsupported write failure; and
- Catalyst Authentication rejection.

## Deferred

- official live provider client/bootstrap implementation;
- AppSail deployment;
- live table read smoke testing;
- Catalyst Authentication;
- API Gateway;
- write repository and sessions;
- schema bootstrap or migration;
- data seeding; and
- Production.
