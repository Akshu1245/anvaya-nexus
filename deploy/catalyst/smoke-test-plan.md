# Catalyst Smoke-Test Plan — Do Not Execute in D-12A

Run this list only after the live-validation checklist authorization gate.

1. Start the AppSail revision; verify safe public `/api/health` and authenticated detailed health.
2. Confirm incomplete explicit Catalyst configuration fails closed and does not select SQLite.
3. Validate mapped login/logout, denied unmapped user, secure cookie, source list, and selected-source enforcement.
4. Execute only fixed, approved reads: FIR Search, Case 360, Related Cases, Relationship Graph, Record Assurance, report creation/preview, Supervisor review, and audit.
5. Confirm masked/restricted/stale/unavailable/empty/partial states are safe.
6. Validate write categories one at a time only after transaction/idempotency checks: investigation/history, audit, reports/reviews, assurance status.
7. Disable the revision and perform the rollback checklist.

Record only safe statuses, counts, template IDs, request IDs, and timestamps. Never paste credentials, endpoints, headers, raw payloads, or real data into evidence.
