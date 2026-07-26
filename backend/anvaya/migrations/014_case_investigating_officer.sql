ALTER TABLE cases ADD COLUMN investigating_officer_id TEXT REFERENCES police_employees(id);
