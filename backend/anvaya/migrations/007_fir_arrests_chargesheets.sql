CREATE TABLE IF NOT EXISTS arrest_surrender_events (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  event_type TEXT NOT NULL CHECK(event_type IN ('ARREST','SURRENDER')),
  event_at TEXT NOT NULL CHECK(event_at GLOB '????-??-??T??:??:??*'),
  state_code TEXT,
  district_code TEXT,
  police_unit_code TEXT,
  investigating_officer_ref TEXT,
  court_ref TEXT,
  remarks TEXT,
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS arrest_accused_links (
  id TEXT PRIMARY KEY,
  arrest_event_id TEXT NOT NULL REFERENCES arrest_surrender_events(id),
  person_id TEXT NOT NULL REFERENCES persons(id),
  case_person_role_id TEXT NOT NULL REFERENCES case_person_roles(id),
  sequence INTEGER CHECK(sequence IS NULL OR sequence > 0),
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id),
  created_at TEXT NOT NULL,
  UNIQUE(arrest_event_id, person_id),
  UNIQUE(arrest_event_id, case_person_role_id)
);

CREATE TABLE IF NOT EXISTS chargesheets (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  filed_at TEXT NOT NULL CHECK(filed_at GLOB '????-??-??T??:??:??*'),
  report_type TEXT NOT NULL CHECK(report_type IN ('A_CHARGESHEET','B_FALSE','C_UNDETECTED')),
  filing_officer_ref TEXT,
  summary TEXT,
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

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

CREATE INDEX IF NOT EXISTS idx_arrest_events_case_time ON arrest_surrender_events(case_id,event_at,event_type,id);
CREATE INDEX IF NOT EXISTS idx_arrest_links_event_order ON arrest_accused_links(arrest_event_id,sequence,person_id,id);
CREATE INDEX IF NOT EXISTS idx_chargesheets_case_filed ON chargesheets(case_id,filed_at,report_type,id);
