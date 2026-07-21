# Restricted Query Language

## Supported intents — P0

SEARCH, DISCOVER, VERIFY, REPORT. Unknown intents are rejected.

## Logical query-plan schema

```json
{
  "intent": "DISCOVER",
  "purpose": "Active Case Investigation",
  "filters": {
    "offence": ["chain_snatching"],
    "location": ["Jayanagar"],
    "date_from": "2026-04-10",
    "date_to": "2026-07-10",
    "status": ["UNRESOLVED"],
    "identifiers": []
  },
  "sources": ["CCTNS_REPLICA", "FORENSICS_REPLICA", "VEHICLE_REPLICA"],
  "relationship_types": ["PHONE", "IMEI", "VEHICLE"],
  "max_hops": 3,
  "limit": 25,
  "uncertain_fields": [],
  "context_investigation_id": null
}
```

## Allowed purposes

Active Case Investigation, Entity Verification, Pattern Research, Supervisor Review, Procedural Review.

## Validation — P0

- Reject raw SQL/ZCQL, unknown keys, intents, sources, purposes, filters, and relationships.
- Enforce source permission, role, purpose, and jurisdiction before retrieval.
- `max_hops` is at most 3; result and graph limits are server-controlled.
- Court/Prosecution are not executable P0 sources.
- FIR numbers, crime numbers, phones, IMEIs, vehicle registrations, and names are protected from translation.
- Uncertain language fields require user confirmation or manual selection.
- Contextual follow-ups inherit only authorised current investigation context.

## AI boundary

AI may interpret paraphrases, normalize Kannada-English text, suggest a supported intent, rank candidates, summarize retrieved facts, and phrase reports. It may not invent records, execute commands, change source data, bypass policy, auto-merge identity, assign guilt/risk, or hide conflicts.

The deterministic parser and editable controls must support the golden workflow without an API key.
