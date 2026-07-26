PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_versions (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);
INSERT OR IGNORE INTO schema_versions(version, applied_at) VALUES (1, CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS source_systems (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, source_tier TEXT NOT NULL, access_class TEXT NOT NULL,
  reliability_role TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('Fresh','Stale','Unavailable')),
  last_successful_sync TEXT, freshness_threshold_hours INTEGER NOT NULL, version TEXT NOT NULL,
  connector_type TEXT NOT NULL, description TEXT NOT NULL, priority TEXT NOT NULL CHECK(priority IN ('P0','P1'))
);
CREATE TABLE IF NOT EXISTS source_records (
  id TEXT PRIMARY KEY, source_system_id TEXT NOT NULL REFERENCES source_systems(id), external_id TEXT NOT NULL,
  version TEXT NOT NULL, source_updated_at TEXT NOT NULL, imported_at TEXT NOT NULL, access_class TEXT NOT NULL,
  reliability_role TEXT NOT NULL, freshness_state TEXT NOT NULL, checksum TEXT NOT NULL,
  payload_json TEXT NOT NULL, UNIQUE(source_system_id, external_id, version)
);
CREATE TRIGGER IF NOT EXISTS source_records_no_update BEFORE UPDATE ON source_records BEGIN SELECT RAISE(ABORT, 'source records are immutable'); END;
CREATE TRIGGER IF NOT EXISTS source_records_no_delete BEFORE DELETE ON source_records BEGIN SELECT RAISE(ABORT, 'source records are immutable'); END;
CREATE TABLE IF NOT EXISTS transformation_events (
  id TEXT PRIMARY KEY, source_record_id TEXT NOT NULL REFERENCES source_records(id), operation TEXT NOT NULL,
  source_field TEXT, target_field TEXT, rule_version TEXT NOT NULL, occurred_at TEXT NOT NULL, outcome TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS locations (
  id TEXT PRIMARY KEY, locality TEXT NOT NULL, station_id TEXT NOT NULL, district_id TEXT NOT NULL,
  latitude REAL NOT NULL, longitude REAL NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id)
);
CREATE TABLE IF NOT EXISTS cases (
  id TEXT PRIMARY KEY, fir_number TEXT NOT NULL, crime_number TEXT NOT NULL, station_id TEXT NOT NULL,
  district_id TEXT NOT NULL, offence TEXT NOT NULL, incident_at TEXT NOT NULL, registered_at TEXT NOT NULL,
  status TEXT NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id)
);
CREATE TABLE IF NOT EXISTS persons (
  id TEXT PRIMARY KEY, display_name TEXT NOT NULL, birth_year INTEGER NOT NULL, address_text TEXT NOT NULL,
  identity_status TEXT NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id)
);
CREATE TABLE IF NOT EXISTS aliases (id TEXT PRIMARY KEY, person_id TEXT NOT NULL REFERENCES persons(id), alias TEXT NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id));
CREATE TABLE IF NOT EXISTS organisations (id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id));
CREATE TABLE IF NOT EXISTS phones (id TEXT PRIMARY KEY, synthetic_number TEXT NOT NULL, number_hash TEXT NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id));
CREATE TABLE IF NOT EXISTS devices (id TEXT PRIMARY KEY, synthetic_imei TEXT NOT NULL, imei_hash TEXT NOT NULL, device_type TEXT NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id));
CREATE TABLE IF NOT EXISTS vehicles (id TEXT PRIMARY KEY, synthetic_registration TEXT NOT NULL, registration_hash TEXT NOT NULL, vehicle_type TEXT NOT NULL, colour TEXT NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id));
CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, case_id TEXT REFERENCES cases(id), document_type TEXT NOT NULL, status TEXT NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id));
CREATE TABLE IF NOT EXISTS evidence_records (id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id), evidence_type TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL, sensitivity TEXT NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id));
CREATE TABLE IF NOT EXISTS forensic_events (id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id), event_type TEXT NOT NULL, occurred_at TEXT NOT NULL, result_status TEXT NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id));
CREATE TABLE IF NOT EXISTS public_context (id TEXT PRIMARY KEY, location_id TEXT NOT NULL REFERENCES locations(id), context_type TEXT NOT NULL, value TEXT NOT NULL, publication_version TEXT NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id));
CREATE TABLE IF NOT EXISTS entity_edges (id TEXT PRIMARY KEY, source_type TEXT NOT NULL, source_id TEXT NOT NULL, target_type TEXT NOT NULL, target_id TEXT NOT NULL, relationship_type TEXT NOT NULL, edge_class TEXT NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id));
CREATE TABLE IF NOT EXISTS case_dna_features (id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id), feature_type TEXT NOT NULL, value TEXT NOT NULL, weight REAL NOT NULL, source_record_id TEXT NOT NULL REFERENCES source_records(id));
CREATE TABLE IF NOT EXISTS trust_issues (id TEXT PRIMARY KEY, case_id TEXT REFERENCES cases(id), issue_type TEXT NOT NULL, severity TEXT NOT NULL, description TEXT NOT NULL, source_record_ids_json TEXT NOT NULL, status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS import_jobs (
  id TEXT PRIMARY KEY, source_system_id TEXT NOT NULL REFERENCES source_systems(id), input_format TEXT NOT NULL,
  checksum TEXT NOT NULL, source_version TEXT NOT NULL, status TEXT NOT NULL, mapped_fields_json TEXT NOT NULL,
  accepted_rows_json TEXT NOT NULL, accepted_count INTEGER NOT NULL, failed_count INTEGER NOT NULL,
  started_at TEXT NOT NULL, completed_at TEXT, committed_at TEXT
);
CREATE TABLE IF NOT EXISTS import_failures (id TEXT PRIMARY KEY, import_job_id TEXT NOT NULL REFERENCES import_jobs(id), row_number INTEGER NOT NULL, category TEXT NOT NULL, safe_reason TEXT NOT NULL);
