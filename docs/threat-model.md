# Security, Privacy and Threat Model

## P0 controls

Backend role/purpose/jurisdiction/source enforcement; field masking; read-only connectors; immutable sources; no client/model SQL; bounded rows and graph; session expiry/revocation; rate limits; audit; import quarantine/checksum; no secrets or real personal data; synthetic data only.

| Threat | Control | Test milestone |
|---|---|---|
| Prompt injection inside record | Treat record text as inert data; templates never execute it | M3/M8 |
| Cross-jurisdiction access | Policy gate before retrieval; mask or deny | M3/M8 |
| Client role/purpose tampering | Derive authorization from session/backend policy | M3/M8 |
| Invented source/FIR ID | Factual templates accept retrieved IDs only | M4/M8 |
| Insider bulk browsing | Purpose logging, rate/row limits, audit review | M3/M8 |
| Malicious import | Schema validation, quarantine, checksum, failure report | M2/M8 |
| Report leakage | Session-linked authorization, watermark, export audit | M6/M8 |
| Entity false positive | Candidate class, conflict display, no auto-merge | M5/M8 |
| Stale/unavailable source | Visible freshness and claim limitation | M2/M8 |
| Secret exposure | `.gitignore`, `.env.example` placeholders, repository scan | M0/M8 |
| Optional AI bypass | AI cannot enforce policy or create facts; validate all output | M3/M8 |

## Privacy statement

The prototype demonstrates privacy- and security-by-design controls. It does not claim DPDP, evidentiary, legal, or departmental certification. Production requires KSP legal, security, policy, and operational approval.

## OUT security shortcuts

No live police data, credentials in Git, facial recognition, person-risk scores, automatic identity merge, social scraping, autonomous recommendations, or raw database commands.
