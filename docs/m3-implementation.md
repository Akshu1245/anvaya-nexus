# M3 Authentication, Policy and Query Implementation

M3 implements the approved prototype controls without changing the M0 product boundary.

## Credentials and sessions

Three synthetic users are deterministically seeded. The local demo password is configuration-driven and stored only as a Werkzeug password hash. Session tokens are random, stored as SHA-256 hashes, sent only in HttpOnly SameSite cookies, expire after a configurable TTL, and can be revoked. Registration and password reset are intentionally absent.

## Central policy order

Authenticate → validate purpose → validate operation → validate selected sources → set row cap → determine station/district/external jurisdiction → apply masking → serialize → audit.

Policy decisions return allowed, denial code, safe explanation, masking level, permitted sources, row limit, and audit-ready metadata. The client cannot set identity or masking state.

## Query safety

`QueryPlan` uses Pydantic with `extra=forbid`, four approved intents, typed filters, a maximum limit of 25, uncertainty metadata, and protected identifiers. SQL, ZCQL, comments, semicolons, and database-expression keywords are rejected before storage. Only SEARCH executes in M3.

## Audit foundation

Minimal events cover login success/failure, logout, session expiry, investigation create/open, preview, SEARCH, and denial. Metadata excludes passwords, tokens, raw query text, and unmasked sensitive values. The audit UI remains M6.

## D-7 FIR Search and Related Cases

The visible search workflow uses bounded structured FIR filters and requires at least one meaningful filter. Search summaries expose case, classification, organisation, people-count, legal, operational-event, freshness, and masking metadata only. The investigation-scoped Related Cases route returns fixed stored factual reasons and applies policy before reason display. It records `FIR_SEARCH_EXECUTED`, compatible `SEARCH_EXECUTION`, and `RELATED_CASES_VIEWED` events without raw display values or response payloads. Legacy DISCOVER remains available for compatibility; Case DNA is not used by this workflow.
