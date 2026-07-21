# HISTORICAL DESIGN MATERIAL — NOT FINAL DEPLOYMENT INSTRUCTIONS

# Catalyst Rollback Plan

Status: offline D-12A plan. Explicit Catalyst mode must never fall back to SQLite.

| Failure | Immediate action | Preserve | Recovery gate |
|---|---|---|---|
| Schema/table creation fails | Stop creation; record failed object names and safe console evidence. | Manifest version, console error category, completed order. | Correct only after sandbox confirmation; remove/disable incomplete resources manually. |
| Seed batch partially fails | Stop the batch; do not continue dependent rows. | Batch ID, counts, rejected synthetic rows, safe diagnostics. | Use documented idempotency key or manually remove the incomplete batch. |
| AppSail start/health fails | Disable the AppSail route; do not route traffic to it. | Build revision and safe health evidence. | Validate port/runtime/start command in sandbox. |
| Frontend/API mismatch | Disable frontend route or point only to validated revision. | Frontend build SHA and safe response status. | Validate CORS, SPA fallback, API base, and response contract. |
| Authentication mapping fails | Disable Catalyst auth integration; deny unmapped users. | Provider subject mapping error category and audit. | Validate canonical role/jurisdiction mapping. |
| Gateway rejects/overexposes a route | Remove the affected allowlist rule. | Rule configuration and safe request ID. | Re-test exact method/auth/header/rate policy. |
| Data Store template mismatch | Disable the repository route; return safe unavailable response. | Template ID and safe error category. | Validate only the fixed template in sandbox. |
| Masking/policy/report regression | Disable Catalyst traffic; do not serve unmasked output. | Request ID, safe audit metadata, rendered version ID. | Run the complete policy/masking smoke set. |

## Local recovery

SQLite local mode remains the working development/runtime backend. It is a separate explicit configuration choice, not a fallback for an attempted Catalyst deployment. Preserve incomplete Catalyst evidence for debugging; do not delete source data blindly, do not reuse real data, and do not deploy a correction without a fresh authorization and validation record.
