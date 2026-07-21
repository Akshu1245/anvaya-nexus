CREATE TRIGGER IF NOT EXISTS immutable_report_version_update
BEFORE UPDATE ON report_versions WHEN OLD.immutable=1
BEGIN SELECT RAISE(ABORT, 'immutable report version'); END;

CREATE TRIGGER IF NOT EXISTS immutable_report_version_delete
BEFORE DELETE ON report_versions
BEGIN SELECT RAISE(ABORT, 'report version history is append-only'); END;

CREATE TRIGGER IF NOT EXISTS immutable_report_review_update
BEFORE UPDATE ON report_reviews
BEGIN SELECT RAISE(ABORT, 'report review history is append-only'); END;

CREATE TRIGGER IF NOT EXISTS immutable_report_review_delete
BEFORE DELETE ON report_reviews
BEGIN SELECT RAISE(ABORT, 'report review history is append-only'); END;

CREATE TRIGGER IF NOT EXISTS immutable_audit_event_update
BEFORE UPDATE ON audit_events
BEGIN SELECT RAISE(ABORT, 'audit history is append-only'); END;

CREATE TRIGGER IF NOT EXISTS immutable_audit_event_delete
BEFORE DELETE ON audit_events
BEGIN SELECT RAISE(ABORT, 'audit history is append-only'); END;
