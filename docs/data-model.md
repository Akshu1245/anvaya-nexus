# Canonical Data Model

## P0 entities

CASE, PERSON, ALIAS, ORGANISATION, PHONE, DEVICE, VEHICLE, LOCATION, DOCUMENT, EVIDENCE, FORENSIC_EVENT, PUBLIC_CONTEXT, SOURCE_SYSTEM, SOURCE_RECORD, TRANSFORMATION_EVENT, ENTITY_EDGE, CASE_DNA_FEATURE, TRUST_ISSUE, INVESTIGATION, INVESTIGATION_MESSAGE, AUDIT_EVENT, REPORT, IMPORT_JOB, IMPORT_FAILURE.

COURT_EVENT, PROSECUTION_EVENT and LEGAL_REFERENCE are **P1**. CUSTODY_EVENT and operational specialist entities are **FUTURE**.

## Essential P0 tables

| Table | Important fields |
|---|---|
| source_systems | id, name, tier, access_class, threshold, status, last_successful_sync |
| source_records | id, source_system_id, external_id, version, updated_at, imported_at, freshness_status, checksum |
| transformation_events | id, source_record_id, operation, source_field, target_field, rule_version, occurred_at, outcome |
| cases | id, fir_number, crime_number, station_id, district_id, offence, incident_at, registered_at, status |
| persons | id, display_name, birth_year, address_id, identity_status |
| phones | id, number_hash, masked_number |
| devices | id, imei_hash, masked_imei, type |
| vehicles | id, registration_hash, masked_registration, type, colour |
| locations | id, locality, station_id, district_id, latitude, longitude |
| evidence_records | id, case_id, type, description, source_record_id, status, sensitivity |
| entity_edges | source_type/id, target_type/id, relationship_type, edge_class, source_record_id |
| case_dna_features | case_id, feature_type, value, weight, source_record_id |
| trust_issues | case_id, issue_type, severity, description, source_record_ids, status |
| investigations | id, title, created_by, jurisdiction_id, purpose, selected_sources, status |
| investigation_messages | investigation_id, original_text, query_plan_json, response_json |
| audit_events | user, role, purpose, action, resources, request_id, timestamp, decision |
| reports | investigation_id, generated_by, source_snapshot_hash, file_reference, watermark_version |
| import_jobs | id, source_system_id, format, checksum, status, started_at, completed_at |
| import_failures | import_job_id, row_reference, category, safe_reason |

## Edge classes

DIRECT_EVIDENCE, RECORDED_ASSOCIATION, CALCULATED_SIMILARITY, CANDIDATE_MATCH. Every edge has a source-record reference; similarity edges additionally retain calculation version and factors.

## Immutability

Imported source records are append/version based. ANVAYA stores canonical mappings, transformations, derived features, edges, and findings separately and never silently overwrites a source value.
