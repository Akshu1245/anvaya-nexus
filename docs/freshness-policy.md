# Source Freshness Policy

Classification: **P0**.

## States

- **Fresh:** available and age is within its configured threshold.
- **Stale:** available but age exceeds its threshold.
- **Unavailable:** disabled, failed health/readiness check, absent, or import failed.

## Configuration

Each source stores a threshold duration, timestamp basis, last successful synchronization/import, current status, and status reason. Thresholds are configuration, not hardcoded UI values.

## Initial prototype defaults

| Source | Timestamp basis | Proposed default |
|---|---|---:|
| CCTNS replica | Dataset/import timestamp | 30 days |
| Forensics replica | Dataset/import timestamp | 14 days |
| Vehicle replica | Dataset/import timestamp | 30 days |
| Offline context fixture | Fixture publication/version date | 180 days |

Defaults are synthetic-demo policy, not claims about operational update requirements.

## Behavior

Fresh sources support normal qualified claims. Stale sources remain searchable when permitted but show last-sync time and a limitation. Unavailable sources are not searched; the workflow continues with remaining authorised sources and lists the limitation in results and reports. No connector failure silently disappears.

Court and Prosecution remain **Unavailable — P1 synthetic adapter** throughout P0.
