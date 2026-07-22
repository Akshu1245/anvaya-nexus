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

CREATE INDEX IF NOT EXISTS idx_identity_link_cases ON identity_link_suggestions(left_case_id, right_case_id);
CREATE INDEX IF NOT EXISTS idx_investigation_briefs_case ON investigation_briefs(case_id, created_at);
