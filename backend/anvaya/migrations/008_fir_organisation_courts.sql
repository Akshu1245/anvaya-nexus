CREATE TABLE IF NOT EXISTS states (
  id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  active INTEGER NOT NULL CHECK(active IN (0,1)), source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id)
);
CREATE TABLE IF NOT EXISTS districts (
  id TEXT PRIMARY KEY, state_id TEXT NOT NULL REFERENCES states(id), code TEXT NOT NULL, name TEXT NOT NULL,
  active INTEGER NOT NULL CHECK(active IN (0,1)), source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id), UNIQUE(state_id,code)
);
CREATE TABLE IF NOT EXISTS police_unit_types (
  id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  active INTEGER NOT NULL CHECK(active IN (0,1)), source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id)
);
CREATE TABLE IF NOT EXISTS police_units (
  id TEXT PRIMARY KEY, district_id TEXT NOT NULL REFERENCES districts(id), unit_type_id TEXT NOT NULL REFERENCES police_unit_types(id),
  code TEXT NOT NULL, name TEXT NOT NULL, active INTEGER NOT NULL CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id), UNIQUE(district_id,code)
);
CREATE TABLE IF NOT EXISTS police_ranks (
  id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  active INTEGER NOT NULL CHECK(active IN (0,1)), source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id)
);
CREATE TABLE IF NOT EXISTS police_designations (
  id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  active INTEGER NOT NULL CHECK(active IN (0,1)), source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id)
);
CREATE TABLE IF NOT EXISTS police_employees (
  id TEXT PRIMARY KEY, employee_code TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL,
  rank_id TEXT REFERENCES police_ranks(id), designation_id TEXT REFERENCES police_designations(id),
  unit_id TEXT NOT NULL REFERENCES police_units(id), active INTEGER NOT NULL CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id)
);
CREATE TABLE IF NOT EXISTS courts (
  id TEXT PRIMARY KEY, district_id TEXT NOT NULL REFERENCES districts(id), code TEXT NOT NULL, name TEXT NOT NULL,
  active INTEGER NOT NULL CHECK(active IN (0,1)), source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id), UNIQUE(district_id,code)
);

ALTER TABLE cases ADD COLUMN state_id TEXT REFERENCES states(id);
ALTER TABLE cases ADD COLUMN canonical_district_id TEXT REFERENCES districts(id);
ALTER TABLE cases ADD COLUMN police_unit_id TEXT REFERENCES police_units(id);
ALTER TABLE cases ADD COLUMN registering_officer_id TEXT REFERENCES police_employees(id);
ALTER TABLE cases ADD COLUMN court_id TEXT REFERENCES courts(id);
ALTER TABLE arrest_surrender_events ADD COLUMN state_id TEXT REFERENCES states(id);
ALTER TABLE arrest_surrender_events ADD COLUMN district_id TEXT REFERENCES districts(id);
ALTER TABLE arrest_surrender_events ADD COLUMN police_unit_id TEXT REFERENCES police_units(id);
ALTER TABLE arrest_surrender_events ADD COLUMN investigating_officer_id TEXT REFERENCES police_employees(id);
ALTER TABLE arrest_surrender_events ADD COLUMN court_id TEXT REFERENCES courts(id);
ALTER TABLE chargesheets ADD COLUMN filing_officer_id TEXT REFERENCES police_employees(id);

CREATE TRIGGER IF NOT EXISTS validate_case_organisation BEFORE UPDATE OF state_id,canonical_district_id,police_unit_id,registering_officer_id,court_id ON cases
WHEN NEW.state_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NEW.canonical_district_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM districts WHERE id=NEW.canonical_district_id AND state_id=NEW.state_id) THEN RAISE(ABORT,'case district/state mismatch') END;
 SELECT CASE WHEN NEW.police_unit_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM police_units WHERE id=NEW.police_unit_id AND district_id=NEW.canonical_district_id) THEN RAISE(ABORT,'case unit/district mismatch') END;
 SELECT CASE WHEN NEW.registering_officer_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM police_employees WHERE id=NEW.registering_officer_id AND unit_id=NEW.police_unit_id) THEN RAISE(ABORT,'case officer/unit mismatch') END;
 SELECT CASE WHEN NEW.court_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM courts WHERE id=NEW.court_id AND district_id=NEW.canonical_district_id) THEN RAISE(ABORT,'case court/district mismatch') END;
END;
CREATE TRIGGER IF NOT EXISTS validate_arrest_organisation BEFORE UPDATE OF state_id,district_id,police_unit_id,investigating_officer_id,court_id ON arrest_surrender_events
WHEN NEW.state_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NEW.district_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM districts WHERE id=NEW.district_id AND state_id=NEW.state_id) THEN RAISE(ABORT,'arrest district/state mismatch') END;
 SELECT CASE WHEN NEW.police_unit_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM police_units WHERE id=NEW.police_unit_id AND district_id=NEW.district_id) THEN RAISE(ABORT,'arrest unit/district mismatch') END;
 SELECT CASE WHEN NEW.investigating_officer_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM police_employees WHERE id=NEW.investigating_officer_id AND unit_id=NEW.police_unit_id) THEN RAISE(ABORT,'arrest officer/unit mismatch') END;
 SELECT CASE WHEN NEW.court_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM courts WHERE id=NEW.court_id AND district_id=NEW.district_id) THEN RAISE(ABORT,'arrest court/district mismatch') END;
END;
CREATE INDEX IF NOT EXISTS idx_district_state ON districts(state_id,code);
CREATE INDEX IF NOT EXISTS idx_unit_district ON police_units(district_id,code);
CREATE INDEX IF NOT EXISTS idx_employee_unit ON police_employees(unit_id,employee_code);
CREATE INDEX IF NOT EXISTS idx_court_district ON courts(district_id,code);
CREATE INDEX IF NOT EXISTS idx_cases_organisation ON cases(state_id,canonical_district_id,police_unit_id,registering_officer_id,court_id);
