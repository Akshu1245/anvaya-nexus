# Safe offline resilience

ANVAYA provides a **safe connection-resilience layer**, not an offline FIR database.

- The application shell and static interface can be cached by the service worker.
- `/api/*` responses are never cached by the service worker.
- FIR records, people, evidence, source passports, audit events and report contents are never written to browser storage.
- When the connection is lost, the UI makes this visible, leaves the current typed text on-screen and blocks all data requests.
- On reconnection, the user must explicitly retry. ANVAYA never executes a query, change or report automatically.

This design avoids silently treating stale or locally retained records as current evidence. It is appropriate for the synthetic prototype and is not a replacement for an authorised encrypted field-device and sync design.
