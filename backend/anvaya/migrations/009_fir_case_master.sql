ALTER TABLE cases ADD COLUMN case_number TEXT;
ALTER TABLE cases ADD COLUMN incident_from_at TEXT;
ALTER TABLE cases ADD COLUMN incident_to_at TEXT;
ALTER TABLE cases ADD COLUMN information_received_at TEXT;
ALTER TABLE cases ADD COLUMN latitude REAL CHECK(latitude IS NULL OR (latitude>=-90 AND latitude<=90));
ALTER TABLE cases ADD COLUMN longitude REAL CHECK(longitude IS NULL OR (longitude>=-180 AND longitude<=180));
ALTER TABLE cases ADD COLUMN brief_facts TEXT;
CREATE TRIGGER IF NOT EXISTS validate_case_master BEFORE UPDATE OF case_number,incident_from_at,incident_to_at,information_received_at,latitude,longitude,brief_facts ON cases BEGIN
 SELECT CASE WHEN NEW.case_number IS NOT NULL AND length(trim(NEW.case_number))=0 THEN RAISE(ABORT,'case number required') END;
 SELECT CASE WHEN (NEW.latitude IS NULL) <> (NEW.longitude IS NULL) THEN RAISE(ABORT,'coordinate pair required') END;
 SELECT CASE WHEN NEW.incident_from_at IS NOT NULL AND NEW.incident_to_at IS NOT NULL AND NEW.incident_from_at>NEW.incident_to_at THEN RAISE(ABORT,'incident chronology invalid') END;
 SELECT CASE WHEN NEW.incident_to_at IS NOT NULL AND NEW.information_received_at IS NOT NULL AND NEW.incident_to_at>NEW.information_received_at THEN RAISE(ABORT,'information chronology invalid') END;
 SELECT CASE WHEN NEW.information_received_at IS NOT NULL AND NEW.registered_at<NEW.information_received_at THEN RAISE(ABORT,'registration chronology invalid') END;
 SELECT CASE WHEN NEW.brief_facts IS NOT NULL AND (length(NEW.brief_facts)>2000 OR NEW.brief_facts LIKE '%<%' OR NEW.brief_facts LIKE '%>%') THEN RAISE(ABORT,'brief facts invalid') END;
END;
CREATE UNIQUE INDEX IF NOT EXISTS uq_case_crime_unit_year ON cases(police_unit_id,crime_number,substr(registered_at,1,4)) WHERE police_unit_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_case_number_unit_year ON cases(police_unit_id,case_number,substr(registered_at,1,4)) WHERE police_unit_id IS NOT NULL AND case_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_cases_incident_range ON cases(incident_from_at,incident_to_at);
CREATE INDEX IF NOT EXISTS idx_cases_registered_at ON cases(registered_at);
