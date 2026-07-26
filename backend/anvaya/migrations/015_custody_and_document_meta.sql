ALTER TABLE evidence_exhibits ADD COLUMN exhibit_kind TEXT;
CREATE TABLE IF NOT EXISTS evidence_custody_events (
  id TEXT PRIMARY KEY,
  exhibit_id TEXT NOT NULL REFERENCES evidence_exhibits(id),
  sequence INTEGER NOT NULL CHECK(sequence > 0),
  event_type TEXT NOT NULL CHECK(event_type IN ('SEIZED','TRANSFERRED','STORED','VERIFIED')),
  event_at TEXT NOT NULL,
  custodian_ref TEXT,
  seal_ref TEXT,
  source_record_id TEXT NOT NULL UNIQUE REFERENCES source_records(id),
  created_at TEXT NOT NULL,
  UNIQUE(exhibit_id, sequence)
);
CREATE INDEX IF NOT EXISTS idx_custody_exhibit ON evidence_custody_events(exhibit_id, sequence, id);

ALTER TABLE documents ADD COLUMN title TEXT;
ALTER TABLE documents ADD COLUMN issued_at TEXT;
ALTER TABLE documents ADD COLUMN linked_exhibit_id TEXT REFERENCES evidence_exhibits(id);
