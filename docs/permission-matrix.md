# Permission Matrix

Classification: **P0**. Enforcement is backend-only; UI hiding is not authorization.

## Purposes

| Purpose | Investigator | Analyst | Supervisor |
|---|---:|---:|---:|
| Active Case Investigation | Assigned scope | No detailed case use unless separately authorised | Review only |
| Entity Verification | Assigned scope | Pattern-safe masked verification | Review only |
| Pattern Research | Aggregated/assigned scope | Broader masked patterns | Review aggregates |
| Supervisor Review | No | No | Reports, audits, denials, source health |
| Procedural Review | Assigned-case references; no general legal advice | Aggregated references | Authorised review |

## Jurisdiction hierarchy

Assigned station → assigned district → external jurisdiction.

| Role/scope | Cases | Sensitive identifiers | Reports/audit |
|---|---|---|---|
| Investigator, assigned station | Full permitted case detail | Full only when purpose/source permits | Own authorised work |
| Investigator, assigned district outside station | Permitted district candidates | Mask unless explicit assignment permits detail | Own authorised work |
| Investigator, external | Candidate summary only | Masked | No unrelated audit |
| Analyst | Broader pattern/aggregate access | Masked | Analysis outputs only |
| Supervisor | Authorised reviewed cases | Report-scoped, least privilege | Reports, audit events, denials, source health |

## Source permissions

Every request intersects account role, purpose, jurisdiction, connector permission, source availability, and requested fields. A denied dimension blocks or masks the result and creates an audit event.

## P0 denial demonstration

An Investigator requests an external-jurisdiction person record. The backend returns only a masked candidate summary, explains the scope limitation without leaking values, and logs the denial/masking decision.

## Prohibitions

No client-controlled role/purpose override; no silent source expansion; no bulk unrestricted browsing; no automatic identity merge; no policy bypass by optional AI.
