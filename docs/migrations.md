# Database Schema Versioning

M2 introduces deterministic, ordered SQL migrations under `backend/anvaya/migrations/`.

- `001_initial.sql` creates the P0 canonical data, source provenance, and import-readiness tables.
- `002_auth_policy_query.sql` adds prototype identities, revocable sessions, investigations, messages, and safe audit events.
- `003_investigation_discovery.sql` adds persisted M4 investigation discovery state.
- `004_reports_review.sql` adds reports, immutable report versions, append-only review decisions, and explicit reviewer assignment.
- `schema_versions` records applied versions.
- Migrations are append-only and idempotent; an existing migration is never edited after release.
- Application startup initializes the local SQLite schema deterministically.
- Source records have database triggers that reject updates and deletes. New source versions are appended instead.
- Transformation events are stored separately from immutable source payloads.

Future schema changes require a new numbered migration and regression tests. This is a local SQLite approach only; Catalyst migration work remains M7.
