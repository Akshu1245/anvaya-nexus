# API Contract

This document fixes resource behavior, not implementation routes. Exact paths may be refined in M1 without changing semantics.

## Common envelope — P0

Successful responses include `request_id`, `data`, `source_status`, `warnings`, and `audit_reference` where applicable. Errors include `request_id`, stable `code`, safe `message`, and `retryable`; never stack traces, SQL, credentials, or unauthorised values.

## Resource families

| Resource | P0 behavior |
|---|---|
| Health | Local service and dependency status |
| Authentication | Login/logout/current session for predefined accounts |
| Sources | Permitted sources, presets, freshness, availability |
| Imports | Validate/commit synthetic CCTNS CSV/JSON and inspect readiness result |
| Investigations | Create, resume, select purpose and sources |
| Query preview | Parse and validate restricted plan without retrieval |
| Query execute | Enforce policy then run SEARCH/DISCOVER/VERIFY/REPORT |
| Cases | Permission-scoped Case 360 |
| Case DNA | Explainable comparison and band |
| Graph | Bounded path and textual fallback |
| Assurance | Five checks and challenge information |
| Action Impact | Ranked authorised verification gaps |
| Reports | Generate/view print-ready watermarked HTML |
| Supervisor | Authorised reports, audits, denials, source health |

## Enforcement order

Authenticate, validate schema/purpose, enforce role and jurisdiction, restrict sources, retrieve bounded data, apply masking, calculate derived results, attach provenance, audit.

## Contract invariants

- Client-supplied role, jurisdiction, mask state, score, or source status is never trusted.
- Query endpoints accept only the restricted plan in `query-language.md`.
- Every factual object supplies at least one Source Passport reference.
- Unavailable/stale source information is returned explicitly.
- External AI output cannot directly populate factual fields.
