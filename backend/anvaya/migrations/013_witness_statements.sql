-- Expand case-person roles to include synthetic WITNESS and statement summaries.
-- Rebuild case_person_roles CHECK allowlist; drop dependent triggers first so SQLite
-- does not leave validate_arrest_accused_link pointing at a dropped table.

DROP TRIGGER IF EXISTS validate_arrest_accused_link;

CREATE TABLE IF NOT EXISTS case_person_roles_v2 (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  person_id TEXT NOT NULL REFERENCES persons(id),
  role TEXT NOT NULL CHECK(role IN ('COMPLAINANT','VICTIM','ACCUSED','WITNESS')),
  role_sequence INTEGER CHECK(role_sequence IS NULL OR role_sequence > 0),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id),
  created_at TEXT NOT NULL
);
INSERT OR IGNORE INTO case_person_roles_v2
  SELECT id, case_id, person_id, role, role_sequence, source_record_id, created_at FROM case_person_roles;
DROP TABLE case_person_roles;
ALTER TABLE case_person_roles_v2 RENAME TO case_person_roles;
CREATE UNIQUE INDEX IF NOT EXISTS idx_case_person_role_unique
  ON case_person_roles(case_id, person_id, role, COALESCE(role_sequence, 0));
CREATE INDEX IF NOT EXISTS idx_case_person_roles_case_order
  ON case_person_roles(case_id, role, role_sequence, person_id);
CREATE INDEX IF NOT EXISTS idx_case_person_roles_person
  ON case_person_roles(person_id);

CREATE TRIGGER IF NOT EXISTS validate_arrest_accused_link
BEFORE INSERT ON arrest_accused_links
FOR EACH ROW
BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1
    FROM arrest_surrender_events event
    JOIN case_person_roles role ON role.id=NEW.case_person_role_id
    WHERE event.id=NEW.arrest_event_id
      AND role.case_id=event.case_id
      AND role.person_id=NEW.person_id
      AND role.role='ACCUSED'
  ) THEN RAISE(ABORT, 'arrest accused link must reference this case''s accused role') END;
END;

CREATE TABLE IF NOT EXISTS case_person_statements (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  case_person_role_id TEXT NOT NULL REFERENCES case_person_roles(id),
  statement_type TEXT NOT NULL CHECK(statement_type IN ('COMPLAINT','WITNESS','ACCUSED')),
  recorded_at TEXT NOT NULL,
  body_text TEXT NOT NULL,
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id),
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_case_statements_case ON case_person_statements(case_id, recorded_at, id);
