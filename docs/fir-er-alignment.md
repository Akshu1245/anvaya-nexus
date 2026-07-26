# Synthetic FIR ER alignment

## Scope and safety boundary

This is a synthetic, offline field-alignment contract for ANVAYA NEXUS. It is not an official schema publication, certification, connector, live FIR integration, or claim of compatibility with any police system. The adapter accepts only records explicitly marked `synthetic_data_only: true`, requires `SYN-` identifiers, performs no I/O, and writes nothing to a database. Real FIR, police, or citizen data must never be supplied.

The mapping describes current ANVAYA canonical concepts after migrations 001–010. “Directly aligned” means the concept has a native canonical field; it does not mean official equivalence.

## Alignment matrix

| FIR ER concept | Synthetic input | Current ANVAYA target | Classification | Notes |
|---|---|---|---|---|
| FIR number | `fir_number` | `cases.fir_number` | directly aligned | Required synthetic identifier. |
| Police station | `police_station.id` | `cases.police_unit_id`; legacy `station_id` | partially aligned | Canonical unit hierarchy supports station-type units, but the adapter receives an existing synthetic unit ID rather than resolving official codes. |
| District | `district.id` | `cases.canonical_district_id`; legacy `district_id` | directly aligned | Existing synthetic reference ID; hierarchy resolution is outside this pure adapter. |
| State | `state.id` | `cases.state_id` | directly aligned | Existing synthetic reference ID. |
| Registration date/time | `registered_at` | `cases.registered_at` | directly aligned | ISO 8601 with timezone; required. |
| Occurrence date/time | `occurrence.from_at`, `to_at` | `cases.incident_from_at`, `incident_to_at`; legacy `incident_at` | directly aligned | ISO 8601 with timezone; chronology is validated. |
| Sections of law | `sections[].act_id`, `section_id` | `case_legal_sections.act_id`, `section_id` | directly aligned | References existing synthetic canonical Act/Section IDs; no free-text legal inference. |
| Complainant | `people[].role=COMPLAINANT` | `persons`; `case_person_roles` | directly aligned | Display name and role only; source record retained. |
| Victim | `people[].role=VICTIM` | `persons`; `case_person_roles` | directly aligned | Same bounded person model. |
| Accused/suspect | `people[].role=ACCUSED` | `persons`; `case_person_roles` | partially aligned | Canonical role is factual `ACCUSED`; a generic “suspect” label is not inferred or stored. |
| Incident location | `occurrence.location` | `locations`; case coordinates where present | partially aligned | A location row is produced only when a valid coordinate pair is supplied; a native case-to-location FK is not currently available. |
| Brief facts/narrative | `brief_facts` | `cases.brief_facts` | directly aligned | Synthetic narrative only; existing database limits remain authoritative on persistence. |
| Vehicle identifiers | `vehicles[].registration` | `vehicles.synthetic_registration` | transformed/derived | Synthetic registration is retained; canonical hashing and case entity-edge persistence occur outside this adapter. |
| Property identifiers | `properties[]` | `evidence_records` with `SYNTHETIC_PROPERTY_REFERENCE` | partially aligned | No dedicated property table currently exists. |
| Investigation status | `investigation_status` | legacy `cases.status` | partially aligned | Canonical `case_status_id` needs reference resolution not performed here. |
| Source system | `source.system_id` | `source_records.source_system_id` | directly aligned | Required synthetic source reference. |
| Source record ID | `source.record_id` | `source_records.id`; all mapped row `source_record_id` fields | directly aligned | Per-item synthetic source IDs override the parent when supplied. |
| Provenance | `source.external_id`, version and timestamps | immutable `source_records`, checksum and row source links | transformed/derived | Adapter builds deterministic safe payload JSON and checksum; it does not persist transformation events. |
| Synthetic-data marker | `synthetic_data_only` | adapter result and source payload marker | transformed/derived | Must be exactly `true`; all identifiers accepted by the adapter must start with `SYN-`. |
| Property ownership/value | not accepted | none | not currently available | Deliberately not inferred. |
| Witness role | not accepted | none in `case_person_roles` | not currently available | Current allowlist is complainant, victim, accused. |
| Biometric, caste, religion, full DOB, real contact/address data | not accepted | none | not currently available | Unsupported sensitive fields are ignored and reported. |

## Adapter contract

`backend.anvaya.importers.fir_er_adapter.adapt_fir_er(record)` returns deterministic row groups for `case`, optional `location`, `people`, `case_person_roles`, `case_legal_sections`, `vehicles`, `evidence_records`, and `source_record`. It rejects missing required identifiers, non-synthetic identifiers, missing synthetic marker, duplicate IDs within collections, malformed or timezone-free dates, invalid chronology, malformed collection shapes, invalid coordinate pairs, and unsupported person roles.

Unknown top-level fields are not copied. Their names are returned in `unsupported_fields` so callers can safely report alignment gaps without exposing their values. Persistence, reference lookup, hashing of vehicle registrations, entity-edge creation, policy checks, masking, and database uniqueness constraints remain responsibilities of existing repository/import workflows.

## Unsupported or intentionally deferred

- No live source, network request, official endpoint, Catalyst resource, authentication, or deployment configuration.
- No official code-list resolution or certification against a particular published ER version.
- No dedicated property entity, suspect/witness role, statement/deposition model, biometric data, or citizen identity resolution.
- No silent person deduplication, legal inference, guilt/risk scoring, or transformation of real identifiers.
- No database writes: the adapter produces validated canonical-shaped dictionaries only.
