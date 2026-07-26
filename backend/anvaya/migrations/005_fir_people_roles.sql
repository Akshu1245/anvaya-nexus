ALTER TABLE persons ADD COLUMN age_years INTEGER CHECK(age_years IS NULL OR age_years BETWEEN 0 AND 130);
ALTER TABLE persons ADD COLUMN gender_code TEXT;
ALTER TABLE persons ADD COLUMN created_at TEXT;
ALTER TABLE persons ADD COLUMN updated_at TEXT;

UPDATE persons
SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS case_person_roles (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  person_id TEXT NOT NULL REFERENCES persons(id),
  role TEXT NOT NULL CHECK(role IN ('COMPLAINANT','VICTIM','ACCUSED')),
  role_sequence INTEGER CHECK(role_sequence IS NULL OR role_sequence > 0),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id),
  created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_case_person_role_unique
  ON case_person_roles(case_id, person_id, role, COALESCE(role_sequence, 0));
CREATE INDEX IF NOT EXISTS idx_case_person_roles_case_order
  ON case_person_roles(case_id, role, role_sequence, person_id);
CREATE INDEX IF NOT EXISTS idx_case_person_roles_person
  ON case_person_roles(person_id);
