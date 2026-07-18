# Complete Application Flow

## Golden path — P0

1. Investigator logs in and sees assigned station/district.
2. Investigator starts an investigation with purpose **Active Case Investigation**.
3. Source Control Centre selects the Case Investigation preset. P0 searches CCTNS, Forensics, Vehicle, and Context where permitted; Court/Prosecution appear only as unavailable/future.
4. Investigator types: `Last three months alli Jayanagar hatra similar unresolved chain-snatching cases show maadi.`
5. Query Preview shows DISCOVER intent, offence, location, date range, status, protected identifiers, and sources.
6. Investigator edits or confirms the plan.
7. Backend applies role, purpose, jurisdiction, source permission, row limits, and masking before retrieval.
8. Four result cards show match reason, jurisdiction/masking status, assurance state, and Source Passport.
9. Follow-up: `Phone, IMEI athava vehicle connection iruva cases matra.`
10. Case DNA identifies two candidate cases without claiming a common offender.
11. Evidence Graph shows source-backed IMEI and vehicle paths; text fallback is always available.
12. Record Assurance shows IMEI support, vehicle-colour conflict, and missing complaint source.
13. Challenge panel shows supporting, weakening, conflicting, missing, and alternative explanation.
14. Action Impact ranks CCTV review highest because it addresses vehicle colour and number-of-offenders gaps.
15. Investigator generates and reviews the watermarked HTML brief.
16. Supervisor reviews report, audit events, denial evidence, and source health.

## Degraded paths — P0

| Condition | Required behavior |
|---|---|
| Kannada uncertainty | Highlight uncertain fields and require confirmation/manual selection |
| Optional LLM unavailable | Deterministic parser and standard controls |
| Source unavailable | Continue with authorised available sources and limitation banner |
| Source stale | Show last sync and qualify claims |
| Graph too large | Shortest path first; capped expansion |
| Graph renderer fails | Text path, source list, source-record references |
| PDF fails/unavailable | Print-ready HTML |
| Catalyst unavailable | Local packaged application and synthetic snapshot |
| Permission denied | Block detail, explain scope safely, create audit event |
| Cost ceiling reached | Deterministic evidence summary |

## Decision boundary

ANVAYA proposes leads and verification priorities. The officer decides whether and how to proceed under applicable authority and procedure.
