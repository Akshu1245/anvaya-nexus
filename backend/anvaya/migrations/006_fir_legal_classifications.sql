CREATE TABLE IF NOT EXISTS legal_acts (
  id TEXT PRIMARY KEY,
  act_code TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL,
  short_name TEXT,
  active INTEGER NOT NULL CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS legal_sections (
  id TEXT PRIMARY KEY,
  act_id TEXT NOT NULL REFERENCES legal_acts(id),
  section_code TEXT NOT NULL,
  description TEXT NOT NULL,
  active INTEGER NOT NULL CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(act_id, section_code),
  UNIQUE(id, act_id)
);

CREATE TABLE IF NOT EXISTS case_legal_sections (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  act_id TEXT NOT NULL REFERENCES legal_acts(id),
  section_id TEXT NOT NULL,
  act_order INTEGER CHECK(act_order IS NULL OR act_order > 0),
  section_order INTEGER CHECK(section_order IS NULL OR section_order > 0),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id),
  created_at TEXT NOT NULL,
  UNIQUE(case_id, section_id),
  FOREIGN KEY(section_id, act_id) REFERENCES legal_sections(id, act_id)
);

CREATE TABLE IF NOT EXISTS case_categories (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  active INTEGER NOT NULL CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id)
);
CREATE TABLE IF NOT EXISTS gravity_offences (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  active INTEGER NOT NULL CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id)
);
CREATE TABLE IF NOT EXISTS crime_heads (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  active INTEGER NOT NULL CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id)
);
CREATE TABLE IF NOT EXISTS crime_subheads (
  id TEXT PRIMARY KEY,
  crime_head_id TEXT NOT NULL REFERENCES crime_heads(id),
  name TEXT NOT NULL,
  sequence INTEGER CHECK(sequence IS NULL OR sequence > 0),
  active INTEGER NOT NULL CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id),
  UNIQUE(crime_head_id, name)
);
CREATE TABLE IF NOT EXISTS case_statuses (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  active INTEGER NOT NULL CHECK(active IN (0,1)),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id)
);

ALTER TABLE cases ADD COLUMN case_category_id TEXT REFERENCES case_categories(id);
ALTER TABLE cases ADD COLUMN gravity_offence_id TEXT REFERENCES gravity_offences(id);
ALTER TABLE cases ADD COLUMN crime_major_head_id TEXT REFERENCES crime_heads(id);
ALTER TABLE cases ADD COLUMN crime_minor_head_id TEXT REFERENCES crime_subheads(id);
ALTER TABLE cases ADD COLUMN case_status_id TEXT REFERENCES case_statuses(id);

CREATE INDEX IF NOT EXISTS idx_case_legal_sections_case_order ON case_legal_sections(case_id, act_order, section_order);
CREATE INDEX IF NOT EXISTS idx_case_legal_sections_section ON case_legal_sections(section_id);
CREATE INDEX IF NOT EXISTS idx_legal_sections_act_code ON legal_sections(act_id, section_code);
CREATE INDEX IF NOT EXISTS idx_crime_subheads_head_order ON crime_subheads(crime_head_id, sequence, name);
CREATE INDEX IF NOT EXISTS idx_cases_fir_classifications ON cases(case_category_id, gravity_offence_id, crime_major_head_id, crime_minor_head_id, case_status_id);
