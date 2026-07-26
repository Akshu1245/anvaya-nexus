ALTER TABLE investigation_messages ADD COLUMN parent_message_id TEXT REFERENCES investigation_messages(id);
ALTER TABLE investigation_messages ADD COLUMN execution_intent TEXT;
ALTER TABLE investigation_messages ADD COLUMN result_count INTEGER;
ALTER TABLE investigation_messages ADD COLUMN request_id TEXT;
