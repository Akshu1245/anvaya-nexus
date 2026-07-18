from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Literal

from backend.anvaya.repositories.base import Repository


class SQLiteRepository(Repository):
    def __init__(self, database: str):
        self.database = database
        self._connection = sqlite3.connect(database, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")

    @classmethod
    def from_url(cls, database_url: str) -> "SQLiteRepository":
        prefix = "sqlite:///"
        if not database_url.startswith(prefix):
            raise ValueError("M1 supports sqlite:/// database URLs only")
        database = database_url.removeprefix(prefix)
        if database != ":memory:":
            path = Path(database)
            path.parent.mkdir(parents=True, exist_ok=True)
            database = str(path)
        return cls(database)

    def health_check(self) -> Literal["ok"]:
        self._connection.execute("SELECT 1").fetchone()
        return "ok"

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def initialize(self) -> None:
        migrations = Path(__file__).resolve().parents[1] / "migrations"
        for migration in sorted(migrations.glob("[0-9][0-9][0-9]_*.sql")):
            version = int(migration.name[:3])
            try:
                applied = self._connection.execute("SELECT 1 FROM schema_versions WHERE version=?", (version,)).fetchone()
            except sqlite3.OperationalError:
                applied = None
            if applied:
                continue
            script = migration.read_text(encoding="utf-8")
            if version == 3:
                self._add_column_if_missing("investigation_messages", "parent_message_id TEXT REFERENCES investigation_messages(id)")
                self._add_column_if_missing("investigation_messages", "execution_intent TEXT")
                self._add_column_if_missing("investigation_messages", "result_count INTEGER")
                self._add_column_if_missing("investigation_messages", "request_id TEXT")
            elif version == 4:
                self._connection.executescript(script.split("ALTER TABLE reports ADD COLUMN", 1)[0])
                self._add_column_if_missing("reports", "assigned_reviewer_id TEXT REFERENCES users(id)")
            else:
                self._connection.executescript(script)
            self._connection.execute("INSERT OR IGNORE INTO schema_versions(version, applied_at) VALUES (?, CURRENT_TIMESTAMP)", (version,))
        self._connection.commit()

    def _add_column_if_missing(self, table: str, definition: str) -> None:
        column = definition.split()[0]
        known = {row[1] for row in self._connection.execute(f"PRAGMA table_info({table})")}
        if column not in known:
            self._connection.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")

    def table_count(self, table: str) -> int:
        allowed = {
            "source_systems", "source_records", "transformation_events", "cases", "persons",
            "aliases", "organisations", "phones", "devices", "vehicles", "locations", "documents",
            "evidence_records", "forensic_events", "public_context", "entity_edges", "case_dna_features",
            "trust_issues", "import_jobs", "import_failures",
            "users", "sessions", "investigations", "investigation_messages", "audit_events",
            "fir_case_details", "case_person_roles", "legal_acts", "legal_sections",
            "case_legal_sections", "police_units", "police_employees", "courts",
            "arrest_surrender_events", "chargesheets",
            "identity_link_suggestions", "investigation_briefs",
        }
        if table not in allowed:
            raise ValueError("Unknown canonical table")
        return int(self._connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    def close(self) -> None:
        self._connection.close()
