# Field Masking Matrix

Classification: **P0**. Masking occurs in the backend before serialization.

| Field | Investigator assigned permitted scope | Investigator district candidate | External candidate | Analyst | Supervisor review |
|---|---|---|---|---|---|
| Name | Full when purpose/source permits | Partial name | Initials/partial | Pseudonymous or masked | Report-scoped as authorised |
| Phone | Full only for permitted verification | Last 4 digits | Last 2–4 digits | Mask/hash reference | Masked unless report need permits |
| IMEI | Full only for permitted verification | Last 4 digits | Last 4 digits | Mask/hash reference | Masked unless report need permits |
| Vehicle registration | Full when permitted | Partial registration | Partial registration | Partial/hash reference | Report-scoped as authorised |
| Address | Full when permitted | Locality only | District/locality only | Aggregated locality | Report-scoped as authorised |
| Sensitive evidence reference | Full reference when permitted | Category/status | Category/status | Category/status | Report-scoped reference |

## Rules

- Full values are never sent to an unauthorised client.
- Search matching may occur on protected hashes/normalized values inside the authorised backend path.
- Masked values remain stable enough within an investigation to compare candidates without revealing identity.
- Unmask attempts require an authorised purpose and create an audit event.
- Reports apply the viewer’s authorization and retain masking metadata.
- Logs never store raw sensitive values when a stable internal reference suffices.
