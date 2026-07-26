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

CREATE TABLE IF NOT EXISTS identity_link_suggestions (
  id TEXT PRIMARY KEY,
  left_case_id TEXT NOT NULL REFERENCES cases(id),
  right_case_id TEXT NOT NULL REFERENCES cases(id),
  shared_person_id TEXT NOT NULL REFERENCES persons(id),
  status TEXT NOT NULL CHECK(status IN ('PENDING','CONFIRMED','REJECTED','NEEDS_REVIEW')) DEFAULT 'PENDING',
  reviewed_by_user_id TEXT REFERENCES users(id),
  reviewed_at TEXT,
  review_note TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  UNIQUE(left_case_id, right_case_id, shared_person_id)
);

CREATE TABLE IF NOT EXISTS investigation_briefs (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  generated_by_user_id TEXT NOT NULL REFERENCES users(id),
  content_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

ALTER TABLE arrest_surrender_events ADD COLUMN accused_person_id TEXT REFERENCES persons(id);
ALTER TABLE arrest_surrender_events ADD COLUMN occurred_at TEXT;

ALTER TABLE chargesheets ADD COLUMN final_report_type TEXT;
ALTER TABLE chargesheets ADD COLUMN status TEXT;

CREATE INDEX IF NOT EXISTS idx_fir_details_category ON fir_case_details(case_category_code);
CREATE INDEX IF NOT EXISTS idx_identity_link_cases ON identity_link_suggestions(left_case_id, right_case_id);
CREATE INDEX IF NOT EXISTS idx_investigation_briefs_case ON investigation_briefs(case_id, created_at);
CREATE INDEX IF NOT EXISTS idx_arrest_accused_person ON arrest_surrender_events(accused_person_id);
