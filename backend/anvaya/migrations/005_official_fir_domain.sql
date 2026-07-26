PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS fir_case_details (
  case_id TEXT PRIMARY KEY REFERENCES cases(id),
  case_category_code TEXT NOT NULL,
  gravity_code TEXT,
  crime_major_head TEXT,
  crime_minor_head TEXT,
  court_id TEXT,
  registering_officer_id TEXT,
  incident_from_at TEXT NOT NULL,
  incident_to_at TEXT,
  information_received_at TEXT,
  latitude REAL,
  longitude REAL,
  brief_facts TEXT NOT NULL DEFAULT '',
  source_record_id TEXT NOT NULL REFERENCES source_records(id)
);

CREATE TABLE IF NOT EXISTS case_person_roles (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  person_id TEXT NOT NULL REFERENCES persons(id),
  role_type TEXT NOT NULL CHECK(role_type IN ('COMPLAINANT','VICTIM','ACCUSED')),
  role_order INTEGER NOT NULL DEFAULT 1,
  source_record_id TEXT NOT NULL REFERENCES source_records(id),
  UNIQUE(case_id, person_id, role_type)
);

CREATE TABLE IF NOT EXISTS legal_acts (
  id TEXT PRIMARY KEY,
  act_code TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL,
  short_name TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL REFERENCES source_records(id)
);

CREATE TABLE IF NOT EXISTS legal_sections (
  id TEXT PRIMARY KEY,
  act_id TEXT NOT NULL REFERENCES legal_acts(id),
  section_code TEXT NOT NULL,
  description TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL REFERENCES source_records(id),
  UNIQUE(act_id, section_code)
);

CREATE TABLE IF NOT EXISTS case_legal_sections (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  act_id TEXT NOT NULL REFERENCES legal_acts(id),
  section_id TEXT NOT NULL REFERENCES legal_sections(id),
  act_order INTEGER NOT NULL DEFAULT 1,
  section_order INTEGER NOT NULL DEFAULT 1,
  source_record_id TEXT NOT NULL REFERENCES source_records(id),
  UNIQUE(case_id, section_id)
);

CREATE TABLE IF NOT EXISTS police_units (
  id TEXT PRIMARY KEY,
  unit_code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  unit_type TEXT NOT NULL,
  district_id TEXT NOT NULL,
  state_code TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL REFERENCES source_records(id)
);

CREATE TABLE IF NOT EXISTS police_employees (
  id TEXT PRIMARY KEY,
  employee_code TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  rank_name TEXT NOT NULL,
  designation TEXT NOT NULL,
  unit_id TEXT REFERENCES police_units(id),
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL REFERENCES source_records(id)
);

CREATE TABLE IF NOT EXISTS courts (
  id TEXT PRIMARY KEY,
  court_code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  district_id TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL REFERENCES source_records(id)
);

CREATE TABLE IF NOT EXISTS arrest_surrender_events (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  accused_person_id TEXT NOT NULL REFERENCES persons(id),
  event_type TEXT NOT NULL CHECK(event_type IN ('ARREST','SURRENDER')),
  occurred_at TEXT NOT NULL,
  state_code TEXT NOT NULL,
  district_id TEXT NOT NULL,
  police_unit_id TEXT REFERENCES police_units(id),
  investigating_officer_id TEXT REFERENCES police_employees(id),
  court_id TEXT REFERENCES courts(id),
  source_record_id TEXT NOT NULL REFERENCES source_records(id)
);

CREATE TABLE IF NOT EXISTS chargesheets (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  filed_at TEXT NOT NULL,
  final_report_type TEXT NOT NULL,
  status TEXT NOT NULL,
  source_record_id TEXT NOT NULL REFERENCES source_records(id)
);

CREATE INDEX IF NOT EXISTS idx_case_person_roles_case_role ON case_person_roles(case_id, role_type);
CREATE INDEX IF NOT EXISTS idx_case_person_roles_person ON case_person_roles(person_id);
CREATE INDEX IF NOT EXISTS idx_case_legal_sections_case ON case_legal_sections(case_id);
CREATE INDEX IF NOT EXISTS idx_arrest_events_case ON arrest_surrender_events(case_id);
CREATE INDEX IF NOT EXISTS idx_chargesheets_case ON chargesheets(case_id);
CREATE INDEX IF NOT EXISTS idx_fir_details_category ON fir_case_details(case_category_code);
