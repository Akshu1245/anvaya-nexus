CREATE TABLE IF NOT EXISTS evidence_exhibits (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  evidence_id TEXT REFERENCES evidence_records(id),
  exhibit_code TEXT NOT NULL,
  filename TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  byte_size INTEGER NOT NULL,
  collected_at TEXT NOT NULL,
  collected_by_ref TEXT,
  chain_status TEXT NOT NULL,
  caption TEXT NOT NULL,
  sensitivity TEXT NOT NULL,
  content_blob BLOB NOT NULL,
  source_record_id TEXT NOT NULL REFERENCES source_records(id),
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_exhibits_case ON evidence_exhibits(case_id);
