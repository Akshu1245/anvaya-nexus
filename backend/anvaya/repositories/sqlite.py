from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

from backend.anvaya.api.errors import ApiError
from backend.anvaya.repositories.base import Repository
from backend.anvaya.repositories.discovery_requests import DiscoveryRequest, RelationshipPathRequest
from backend.anvaya.repositories.intelligence_requests import CaseDnaRequest, EvidenceGraphRequest
from backend.anvaya.repositories.audit_requests import AuditEventFilter, AuditEventInput
from backend.anvaya.repositories.search_filter import CaseSearchFilter
from backend.anvaya.repositories.person_roles import CASE_PERSON_ROLES


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

    def schema_version(self) -> int:
        return int(self._connection.execute("SELECT MAX(version) FROM schema_versions").fetchone()[0] or 0)

    def seed_predefined_users(self, users: Sequence[Mapping[str, Any]]) -> None:
        for user in users:
            self._connection.execute(
                """INSERT INTO users VALUES (?,?,?,?,?,?,1)
                   ON CONFLICT(id) DO UPDATE SET
                     username=excluded.username,
                     password_hash=excluded.password_hash,
                     role=excluded.role,
                     assigned_station=excluded.assigned_station,
                     assigned_district=excluded.assigned_district,
                     active=1""",
                (
                    user["id"], user["username"], user["password_hash"], user["role"],
                    user.get("assigned_station"), user.get("assigned_district"),
                ),
            )
        self._connection.commit()

    def find_active_user_by_username(self, username: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT * FROM users WHERE username=? AND active=1", (username,)
        ).fetchone()
        return dict(row) if row else None

    def find_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def create_session(
        self,
        session_id: str,
        user_id: str,
        token_hash: str,
        created_at: str,
        expires_at: str,
    ) -> None:
        self._connection.execute(
            "INSERT INTO sessions VALUES (?,?,?,?,?,NULL)",
            (session_id, user_id, token_hash, created_at, expires_at),
        )
        self._connection.commit()

    def find_session_with_user(self, token_hash: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT u.*,s.id session_id,s.expires_at,s.revoked_at "
            "FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?",
            (token_hash,),
        ).fetchone()
        return dict(row) if row else None

    def revoke_session(self, session_id: str, revoked_at: str) -> None:
        self._connection.execute("UPDATE sessions SET revoked_at=? WHERE id=?", (revoked_at, session_id))
        self._connection.commit()

    def upsert_source_systems(self, sources: Sequence[Mapping[str, Any]]) -> None:
        for source in sources:
            self._connection.execute(
                """INSERT INTO source_systems
                (id,name,source_tier,access_class,reliability_role,status,last_successful_sync,freshness_threshold_hours,version,connector_type,description,priority)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET status=excluded.status,last_successful_sync=excluded.last_successful_sync,
                freshness_threshold_hours=excluded.freshness_threshold_hours,version=excluded.version""",
                (
                    source["id"], source["name"], source["source_tier"], source["access_class"],
                    source["reliability_role"], source["status"], source["last_successful_sync"],
                    source["freshness_threshold_hours"], source["version"], source["connector_type"],
                    source["description"], source["priority"],
                ),
            )
        self._connection.commit()

    def list_source_systems(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute("SELECT * FROM source_systems ORDER BY priority, id")]

    def find_source_system(self, source_id: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM source_systems WHERE id=?", (source_id,)).fetchone()
        return dict(row) if row else None

    def source_external_ids(self, source_system_id: str) -> set[str]:
        rows = self._connection.execute(
            "SELECT external_id FROM source_records WHERE source_system_id=?", (source_system_id,)
        )
        return {str(row[0]) for row in rows}

    def create_import_job(self, job: Mapping[str, Any], failures: Sequence[Mapping[str, Any]]) -> None:
        self._connection.execute(
            "INSERT INTO import_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                job["id"], job["source_system_id"], job["input_format"], job["checksum"],
                job["source_version"], job["status"], job["mapped_fields_json"],
                job["accepted_rows_json"], job["accepted_count"], job["failed_count"],
                job["started_at"], job["completed_at"], job.get("committed_at"),
            ),
        )
        for failure in failures:
            self._connection.execute(
                "INSERT INTO import_failures VALUES (?,?,?,?,?)",
                (failure["id"], job["id"], failure["row_number"], failure["category"], failure["safe_reason"]),
            )
        self._connection.commit()

    def find_import_job(self, job_id: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM import_jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None

    def list_import_failures(self, job_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute(
            "SELECT * FROM import_failures WHERE import_job_id=? ORDER BY row_number", (job_id,)
        )]

    def commit_import_rows(
        self, job_id: str, imported_at: str, canonical_rows: Sequence[Mapping[str, Any]]
    ) -> None:
        try:
            with self._connection:
                for row in canonical_rows:
                    self._connection.execute(
                        "INSERT INTO source_records VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            row["source_record_id"], "CCTNS_REPLICA", row["external_id"], row["source_version"],
                            row["source_updated_at"], imported_at, "RESTRICTED", "Primary operational record",
                            "Fresh", row["checksum"], row["payload_json"],
                        ),
                    )
                    self._connection.execute(
                        "INSERT INTO transformation_events VALUES (?,?,?,?,?,?,?,?)",
                        (
                            row["transformation_event_id"], row["source_record_id"], "CSV_JSON_CANONICAL_MAP",
                            "*", "cases", "M2-1.0", imported_at, "ACCEPTED",
                        ),
                    )
                    self._connection.execute(
                        "INSERT INTO cases (id,fir_number,crime_number,station_id,district_id,offence,incident_at,registered_at,status,source_record_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (
                            row["external_id"], row["fir_number"], row["crime_number"], row["station_id"],
                            row["district_id"], row["offence"], row["incident_at"], row["registered_at"],
                            row["status"], row["source_record_id"],
                        ),
                    )
                self._connection.execute(
                    "UPDATE import_jobs SET status='COMMITTED', committed_at=? WHERE id=?", (imported_at, job_id)
                )
        except sqlite3.DatabaseError as error:
            raise ApiError("IMPORT_COMMIT_FAILED", "Accepted synthetic rows could not be committed.", 409, False) from error

    def create_investigation(self, investigation: Mapping[str, Any]) -> None:
        self._connection.execute(
            "INSERT INTO investigations VALUES (?,?,?,?,?,?,?,?,?)",
            (
                investigation["id"], investigation["user_id"], investigation["title"], investigation["purpose"],
                investigation["selected_sources_json"], investigation.get("assigned_station"),
                investigation.get("assigned_district"), investigation["created_at"], investigation["updated_at"],
            ),
        )
        self._connection.commit()

    def find_investigation(self, investigation_id: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM investigations WHERE id=?", (investigation_id,)).fetchone()
        return dict(row) if row else None

    def list_investigations_for_user(self, user_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        if limit is None:
            rows = self._connection.execute(
                "SELECT * FROM investigations WHERE user_id=? ORDER BY updated_at DESC", (user_id,)
            )
        else:
            rows = self._connection.execute(
                "SELECT * FROM investigations WHERE user_id=? ORDER BY updated_at DESC LIMIT ?",
                (user_id, max(1, min(int(limit), 10))),
            )
        return [dict(row) for row in rows]

    def replace_investigation_sources(
        self, investigation_id: str, selected_sources_json: str, updated_at: str
    ) -> None:
        self._connection.execute(
            "UPDATE investigations SET selected_sources_json=?,updated_at=? WHERE id=?",
            (selected_sources_json, updated_at, investigation_id),
        )
        self._connection.commit()

    def create_investigation_message(self, message: Mapping[str, Any]) -> None:
        self._connection.execute(
            """INSERT INTO investigation_messages
            (id,investigation_id,original_text,query_plan_json,confirmed,created_at,parent_message_id,execution_intent,result_count,request_id)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                message["id"], message["investigation_id"], message["original_text"], message["query_plan_json"],
                message.get("confirmed", 0), message["created_at"], message.get("parent_message_id"),
                message.get("execution_intent"), message.get("result_count"), message.get("request_id"),
            ),
        )
        self._connection.commit()

    def find_investigation_message(
        self, investigation_id: str, message_id: str
    ) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT id,original_text,query_plan_json,confirmed,parent_message_id,execution_intent,result_count,request_id,created_at "
            "FROM investigation_messages WHERE id=? AND investigation_id=?",
            (message_id, investigation_id),
        ).fetchone()
        return dict(row) if row else None

    def list_investigation_messages(self, investigation_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute(
            "SELECT id,original_text,query_plan_json,confirmed,parent_message_id,execution_intent,result_count,request_id,created_at "
            "FROM investigation_messages WHERE investigation_id=? ORDER BY created_at", (investigation_id,)
        )]

    def confirm_investigation_message(
        self, investigation_id: str, message_id: str, query_plan_json: str
    ) -> bool:
        cursor = self._connection.execute(
            "UPDATE investigation_messages SET query_plan_json=?,confirmed=1 WHERE id=? AND investigation_id=?",
            (query_plan_json, message_id, investigation_id),
        )
        self._connection.commit()
        return cursor.rowcount == 1

    def search_case_candidates(self, filters: CaseSearchFilter) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if filters.offence:
            normalized = filters.offence.upper().replace(" ", "_")
            clauses.append("(upper(c.offence)=? OR upper(c.offence)=?)")
            parameters.extend([filters.offence.upper(), normalized])
        if filters.status:
            clauses.append("upper(c.status)=?")
            parameters.append(filters.status.upper())
        if filters.date_from:
            clauses.append("date(c.incident_at)>=?")
            parameters.append(filters.date_from)
        if filters.date_to:
            clauses.append("date(c.incident_at)<=?")
            parameters.append(filters.date_to)
        if filters.case_identifier:
            clauses.append("(c.id=? OR c.fir_number=? OR c.crime_number=?)")
            parameters.extend([filters.case_identifier] * 3)
        if filters.crime_number: clauses.append("c.crime_number=?"); parameters.append(filters.crime_number)
        if filters.case_number: clauses.append("c.case_number=?"); parameters.append(filters.case_number)
        if filters.registration_date_from: clauses.append("date(c.registered_at)>=?"); parameters.append(filters.registration_date_from)
        if filters.registration_date_to: clauses.append("date(c.registered_at)<=?"); parameters.append(filters.registration_date_to)
        if filters.location and filters.location != "JAYANAGAR":
            clauses.append("(lower(c.station_id)=lower(?) OR lower(c.district_id)=lower(?))")
            parameters.extend([filters.location, filters.location])
        if filters.source_system_ids:
            clauses.append("sr.source_system_id IN (" + ",".join("?" for _ in filters.source_system_ids) + ")")
            parameters.extend(filters.source_system_ids)
        for value, table, case_column, code_column in (
            (filters.state, "states", "state_id", "code"), (filters.district, "districts", "canonical_district_id", "code"),
            (filters.police_unit, "police_units", "police_unit_id", "code"), (filters.registering_officer, "police_employees", "registering_officer_id", "employee_code"),
            (filters.court, "courts", "court_id", "code"),
        ):
            if value:
                clauses.append(f"EXISTS (SELECT 1 FROM {table} org WHERE org.id=c.{case_column} AND (org.id=? OR org.{code_column}=?))")
                parameters.extend([value, value])
        if filters.person_name or filters.person_role:
            person_clauses = ["cpr.case_id=c.id"]
            person_parameters: list[Any] = []
            if filters.person_name:
                person_clauses.append("lower(p.display_name) LIKE lower(?) ESCAPE '\\'")
                person_parameters.append("%" + self._escaped_like(filters.person_name) + "%")
            if filters.person_role:
                person_clauses.append("cpr.role=?")
                person_parameters.append(filters.person_role)
            if filters.source_system_ids:
                person_clauses.append("role_source.source_system_id IN (" + ",".join("?" for _ in filters.source_system_ids) + ")")
                person_parameters.extend(filters.source_system_ids)
            clauses.append(
                "EXISTS (SELECT 1 FROM case_person_roles cpr JOIN persons p ON p.id=cpr.person_id "
                "JOIN source_records role_source ON role_source.id=cpr.source_record_id WHERE "
                + " AND ".join(person_clauses) + ")"
            )
            parameters.extend(person_parameters)
        for value, table, column, case_column in (
            (filters.act_id, "legal_acts", "id", ""),
            (filters.act_code, "legal_acts", "act_code", ""),
            (filters.section_id, "legal_sections", "id", ""),
            (filters.section_code, "legal_sections", "section_code", ""),
        ):
            if value:
                join = "JOIN legal_acts la ON la.id=cls.act_id" if table == "legal_acts" else "JOIN legal_sections ls ON ls.id=cls.section_id"
                source_filter = ""
                source_parameters: list[Any] = []
                if filters.source_system_ids:
                    source_filter = " JOIN source_records legal_source ON legal_source.id=cls.source_record_id WHERE legal_source.source_system_id IN (" + ",".join("?" for _ in filters.source_system_ids) + ") AND "
                    source_parameters.extend(filters.source_system_ids)
                else:
                    source_filter = " WHERE "
                alias = "la" if table == "legal_acts" else "ls"
                clauses.append("EXISTS (SELECT 1 FROM case_legal_sections cls " + join + source_filter + "cls.case_id=c.id AND " + alias + "." + column + "=?)")
                parameters.extend([*source_parameters, value])
        for value, table, column in (
            (filters.case_category, "case_categories", "case_category_id"),
            (filters.gravity_offence, "gravity_offences", "gravity_offence_id"),
            (filters.crime_major_head, "crime_heads", "crime_major_head_id"),
            (filters.crime_minor_head, "crime_subheads", "crime_minor_head_id"),
            (filters.canonical_case_status, "case_statuses", "case_status_id"),
        ):
            if value:
                code_column = "name" if table in {"crime_heads", "crime_subheads"} else "code"
                clauses.append("EXISTS (SELECT 1 FROM " + table + " reference WHERE reference.id=c." + column + " AND (reference.id=? OR reference." + code_column + "=?))")
                parameters.extend([value, value])
        if filters.arrest_event_type:
            source_clause = ""
            if filters.source_system_ids:
                source_clause = " AND event_source.source_system_id IN (" + ",".join("?" for _ in filters.source_system_ids) + ")"
            clauses.append("EXISTS (SELECT 1 FROM arrest_surrender_events event JOIN source_records event_source ON event_source.id=event.source_record_id WHERE event.case_id=c.id AND event.event_type=?" + source_clause + ")")
            parameters.extend([filters.arrest_event_type, *filters.source_system_ids])
        if filters.chargesheet_report_type:
            source_clause = ""
            if filters.source_system_ids:
                source_clause = " AND chargesheet_source.source_system_id IN (" + ",".join("?" for _ in filters.source_system_ids) + ")"
            clauses.append("EXISTS (SELECT 1 FROM chargesheets chargesheet JOIN source_records chargesheet_source ON chargesheet_source.id=chargesheet.source_record_id WHERE chargesheet.case_id=c.id AND chargesheet.report_type=?" + source_clause + ")")
            parameters.extend([filters.chargesheet_report_type, *filters.source_system_ids])
        for present, table in ((filters.has_arrest_event, "arrest_surrender_events"), (filters.has_chargesheet, "chargesheets")):
            if present is not None:
                source_alias = "event_source"
                source_join = ""
                source_clause = ""
                if filters.source_system_ids:
                    source_join = " JOIN source_records " + source_alias + " ON " + source_alias + ".id=event_presence.source_record_id"
                    source_clause = " AND " + source_alias + ".source_system_id IN (" + ",".join("?" for _ in filters.source_system_ids) + ")"
                clauses.append(("EXISTS" if present else "NOT EXISTS") + " (SELECT 1 FROM " + table + " event_presence" + source_join + " WHERE event_presence.case_id=c.id" + source_clause + ")")
                parameters.extend(filters.source_system_ids)
        for value, table, entity_type, column in (
            (filters.imei, "devices d", "DEVICE", "d.synthetic_imei"),
            (filters.phone, "phones p", "PHONE", "p.synthetic_number"),
            (filters.vehicle_registration, "vehicles v", "VEHICLE", "v.synthetic_registration"),
        ):
            if value:
                clauses.append(
                    "EXISTS (SELECT 1 FROM entity_edges e JOIN " + table + " ON e.target_id="
                    + column.split(".")[0] + ".id WHERE e.source_type='CASE' AND e.source_id=c.id "
                    + "AND e.target_type='" + entity_type + "' AND " + column + "=?)"
                )
                parameters.append(value)
        sql = (
            "SELECT c.id,c.fir_number,c.crime_number,c.station_id,c.district_id,c.offence,c.incident_at,c.registered_at,c.status,c.source_record_id,"
            "sr.freshness_state,sr.source_system_id,sr.reliability_role,sr.access_class "
            "FROM cases c JOIN source_records sr ON sr.id=c.source_record_id"
            + (" WHERE " + " AND ".join(clauses) if clauses else "")
            + " ORDER BY c.incident_at DESC LIMIT ? OFFSET ?"
        )
        parameters.extend([filters.limit, filters.offset])
        return [dict(row) for row in self._connection.execute(sql, parameters)]

    def list_related_case_facts(
        self, case_id: str, source_system_ids: Sequence[str], limit: int = 25
    ) -> list[dict[str, Any]]:
        """Fixed, source-scoped factual links; comparison semantics stay in service."""
        sources = tuple(dict.fromkeys(source_system_ids))
        if not sources or not 1 <= limit <= 25:
            raise ValueError("Related-case scope or limit is invalid")
        placeholders = ",".join("?" for _ in sources)
        sql = """
        WITH base AS (SELECT * FROM cases WHERE id=?), facts AS (
          SELECT candidate.case_id candidate_id,'SHARED_' || base_role.role reason_type,
                 base_role.person_id matched_record_id,person.display_name matched_value,
                 candidate.source_record_id reason_source_record_id
          FROM case_person_roles base_role
          JOIN case_person_roles candidate ON candidate.person_id=base_role.person_id AND candidate.role=base_role.role
          JOIN persons person ON person.id=base_role.person_id
          WHERE base_role.case_id=? AND candidate.case_id<>?
          UNION ALL
          SELECT candidate.case_id,'SHARED_ACT_SECTION',base_link.section_id,
                 act.act_code || ' Section ' || section.section_code,candidate.source_record_id
          FROM case_legal_sections base_link
          JOIN case_legal_sections candidate ON candidate.section_id=base_link.section_id AND candidate.act_id=base_link.act_id
          JOIN legal_acts act ON act.id=base_link.act_id
          JOIN legal_sections section ON section.id=base_link.section_id
          WHERE base_link.case_id=? AND candidate.case_id<>?
          UNION ALL
          SELECT candidate.id,'SHARED_POLICE_UNIT',candidate.police_unit_id,unit.name,candidate.source_record_id
          FROM base JOIN cases candidate ON candidate.police_unit_id=base.police_unit_id
          JOIN police_units unit ON unit.id=candidate.police_unit_id WHERE candidate.id<>?
          UNION ALL
          SELECT candidate.id,'SHARED_COURT',candidate.court_id,court.name,candidate.source_record_id
          FROM base JOIN cases candidate ON candidate.court_id=base.court_id
          JOIN courts court ON court.id=candidate.court_id WHERE candidate.id<>?
          UNION ALL
          SELECT candidate.id,'SHARED_REGISTERING_OFFICER',candidate.registering_officer_id,employee.display_name,candidate.source_record_id
          FROM base JOIN cases candidate ON candidate.registering_officer_id=base.registering_officer_id
          JOIN police_employees employee ON employee.id=candidate.registering_officer_id WHERE candidate.id<>?
          UNION ALL
          SELECT candidate.id,'SHARED_CRIME_MINOR_HEAD',candidate.crime_minor_head_id,subhead.name,candidate.source_record_id
          FROM base JOIN cases candidate ON candidate.crime_minor_head_id=base.crime_minor_head_id
          JOIN crime_subheads subhead ON subhead.id=candidate.crime_minor_head_id WHERE candidate.id<>?
          UNION ALL
          SELECT candidate.id,'SHARED_CRIME_MAJOR_HEAD',candidate.crime_major_head_id,head.name,candidate.source_record_id
          FROM base JOIN cases candidate ON candidate.crime_major_head_id=base.crime_major_head_id
          JOIN crime_heads head ON head.id=candidate.crime_major_head_id WHERE candidate.id<>?
          UNION ALL
          SELECT candidate.id,'SHARED_CASE_CATEGORY',candidate.case_category_id,category.name,candidate.source_record_id
          FROM base JOIN cases candidate ON candidate.case_category_id=base.case_category_id
          JOIN case_categories category ON category.id=candidate.case_category_id WHERE candidate.id<>?
          UNION ALL
          SELECT candidate.id,'SHARED_GRAVITY',candidate.gravity_offence_id,gravity.name,candidate.source_record_id
          FROM base JOIN cases candidate ON candidate.gravity_offence_id=base.gravity_offence_id
          JOIN gravity_offences gravity ON gravity.id=candidate.gravity_offence_id WHERE candidate.id<>?
          UNION ALL
          SELECT candidate.id,'SHARED_CANONICAL_STATUS',candidate.case_status_id,status.name,candidate.source_record_id
          FROM base JOIN cases candidate ON candidate.case_status_id=base.case_status_id
          JOIN case_statuses status ON status.id=candidate.case_status_id WHERE candidate.id<>?
          UNION ALL
          SELECT candidate_event.case_id,'SHARED_ARREST_ACCUSED',base_link.person_id,person.display_name,candidate_link.source_record_id
          FROM arrest_surrender_events base_event
          JOIN arrest_accused_links base_link ON base_link.arrest_event_id=base_event.id
          JOIN arrest_accused_links candidate_link ON candidate_link.person_id=base_link.person_id
          JOIN arrest_surrender_events candidate_event ON candidate_event.id=candidate_link.arrest_event_id
          JOIN persons person ON person.id=base_link.person_id
          WHERE base_event.case_id=? AND candidate_event.case_id<>?
          UNION ALL
          SELECT candidate.id,'TEMPORAL_OVERLAP',NULL,'Incident dates overlap or are within 7 days',candidate.source_record_id
          FROM base JOIN cases candidate
          WHERE candidate.id<>? AND base.incident_from_at IS NOT NULL AND candidate.incident_from_at IS NOT NULL
            AND (candidate.incident_from_at<=COALESCE(base.incident_to_at,base.incident_from_at)
              AND COALESCE(candidate.incident_to_at,candidate.incident_from_at)>=base.incident_from_at
              OR abs(julianday(candidate.incident_from_at)-julianday(base.incident_from_at))<=7)
        )
        SELECT facts.candidate_id,facts.reason_type,facts.matched_record_id,facts.matched_value,facts.reason_source_record_id,
          c.fir_number,c.crime_number,c.case_number,c.station_id,c.district_id,c.incident_from_at,c.incident_to_at,c.registered_at,c.status,c.source_record_id,
          source.source_system_id,source.freshness_state,source.reliability_role,source.access_class
        FROM facts JOIN cases c ON c.id=facts.candidate_id
        JOIN source_records source ON source.id=c.source_record_id
        WHERE source.source_system_id IN (""" + placeholders + ") ORDER BY c.registered_at DESC,c.id,facts.reason_type,facts.matched_record_id LIMIT ?"
        parameters = [case_id, case_id, case_id, case_id, case_id, case_id, case_id, case_id, case_id, case_id, case_id, case_id, case_id, case_id, case_id, case_id, *sources, limit * 16]
        return [dict(row) for row in self._connection.execute(sql, parameters)]

    @staticmethod
    def _escaped_like(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def list_discovery_candidates(self, request: DiscoveryRequest) -> list[dict[str, Any]]:
        seed_placeholders = ",".join("?" for _ in request.seed_case_ids)
        source_placeholders = ",".join("?" for _ in request.source_system_ids)
        source_filter = (
            " AND candidate_source.source_system_id IN (" + source_placeholders + ")"
            " AND edge_source.source_system_id IN (" + source_placeholders + ")"
            " AND link_source.source_system_id IN (" + source_placeholders + ")"
        )
        sql = (
            "SELECT e.source_id AS base_case_id,e.target_type,e.relationship_type,e.source_record_id AS edge_source_record_id,"
            "link.source_id AS candidate_id,link.source_record_id AS link_source_record_id,"
            "c.id,c.fir_number,c.crime_number,c.station_id,c.district_id,c.offence,c.incident_at,c.registered_at,c.status,c.source_record_id,"
            "candidate_source.freshness_state,candidate_source.source_system_id,"
            "candidate_source.reliability_role,candidate_source.access_class "
            "FROM entity_edges e JOIN entity_edges link ON link.target_type=e.target_type AND link.target_id=e.target_id "
            "AND link.source_type='CASE' AND link.source_id<>e.source_id "
            "JOIN cases c ON c.id=link.source_id "
            "JOIN source_records candidate_source ON candidate_source.id=c.source_record_id "
            "JOIN source_records edge_source ON edge_source.id=e.source_record_id "
            "JOIN source_records link_source ON link_source.id=link.source_record_id "
            "WHERE e.source_type='CASE' AND e.relationship_type IN ('RECORDED_DEVICE','SHARED_IMEI','RECORDED_PHONE','RECORDED_VEHICLE') "
            "AND e.source_id IN (" + seed_placeholders + ")" + source_filter
            + " ORDER BY c.incident_at DESC,c.id,e.id,link.id LIMIT ? OFFSET ?"
        )
        parameters = [*request.seed_case_ids, *request.source_system_ids, *request.source_system_ids, *request.source_system_ids, request.limit, request.offset]
        return [dict(row) for row in self._connection.execute(sql, parameters)]

    def list_relationship_edges(self, request: RelationshipPathRequest) -> list[dict[str, Any]]:
        relationship_placeholders = ",".join("?" for _ in request.relationship_types)
        source_placeholders = ",".join("?" for _ in request.source_system_ids)
        sql = (
            "SELECT e.*,sr.freshness_state,sr.reliability_role,sr.access_class,sr.source_system_id "
            "FROM entity_edges e JOIN source_records sr ON sr.id=e.source_record_id "
            "WHERE e.relationship_type IN (" + relationship_placeholders + ") "
            "AND sr.source_system_id IN (" + source_placeholders + ") ORDER BY e.id LIMIT ?"
        )
        parameters = [*request.relationship_types, *request.source_system_ids, request.edge_limit]
        return [dict(row) for row in self._connection.execute(sql, parameters)]

    def find_case_360_case(self, case_id: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT id,fir_number,crime_number,case_number,station_id,district_id,offence,incident_at,incident_from_at,incident_to_at,information_received_at,registered_at,latitude,longitude,brief_facts,status,source_record_id FROM cases WHERE id=?", (case_id,)).fetchone()
        return dict(row) if row else None

    def list_case_360_entities(self, case_id: str) -> list[dict[str, Any]]:
        # The CASE expressions are a fixed allowlist matching the existing Case
        # 360 entity sections. They deliberately cannot select arbitrary tables.
        sql = """
        SELECT e.id AS edge_id,e.target_type,e.target_id,e.source_record_id AS edge_source_record_id,
          CASE e.target_type
            WHEN 'PERSON' THEN p.display_name WHEN 'PHONE' THEN ph.synthetic_number
            WHEN 'DEVICE' THEN d.synthetic_imei WHEN 'VEHICLE' THEN v.synthetic_registration
            WHEN 'LOCATION' THEN l.locality END AS value,
          CASE e.target_type
            WHEN 'PERSON' THEN p.source_record_id WHEN 'PHONE' THEN ph.source_record_id
            WHEN 'DEVICE' THEN d.source_record_id WHEN 'VEHICLE' THEN v.source_record_id
            WHEN 'LOCATION' THEN l.source_record_id END AS entity_source_record_id
        FROM entity_edges e
        LEFT JOIN persons p ON e.target_type='PERSON' AND p.id=e.target_id
        LEFT JOIN phones ph ON e.target_type='PHONE' AND ph.id=e.target_id
        LEFT JOIN devices d ON e.target_type='DEVICE' AND d.id=e.target_id
        LEFT JOIN vehicles v ON e.target_type='VEHICLE' AND v.id=e.target_id
        LEFT JOIN locations l ON e.target_type='LOCATION' AND l.id=e.target_id
        WHERE e.source_type='CASE' AND e.source_id=?
          AND e.target_type IN ('PERSON','PHONE','DEVICE','VEHICLE','LOCATION')
        ORDER BY e.id
        """
        return [dict(row) for row in self._connection.execute(sql, (case_id,)) if row["value"] is not None]

    def list_case_360_evidence(self, case_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute(
            "SELECT * FROM evidence_records WHERE case_id=? ORDER BY id", (case_id,)
        )]

    def list_case_360_documents(self, case_id: str) -> list[dict[str, Any]]:
        try:
            return [dict(row) for row in self._connection.execute(
                "SELECT id,case_id,document_type,status,source_record_id,title,issued_at,linked_exhibit_id FROM documents WHERE case_id=? ORDER BY id",
                (case_id,),
            )]
        except Exception:
            return [dict(row) for row in self._connection.execute(
                "SELECT id,case_id,document_type,status,source_record_id FROM documents WHERE case_id=? ORDER BY id",
                (case_id,),
            )]

    def list_case_360_exhibits(self, case_id: str, include_blob: bool = False) -> list[dict[str, Any]]:
        columns = "id,case_id,evidence_id,exhibit_code,filename,mime_type,sha256,byte_size,collected_at,collected_by_ref,chain_status,caption,sensitivity,source_record_id,created_at"
        if include_blob:
            columns += ",content_blob"
        try:
            kind_columns = columns.replace("created_at", "exhibit_kind,created_at") if "exhibit_kind" not in columns else columns
            return [dict(row) for row in self._connection.execute(
                f"SELECT {kind_columns} FROM evidence_exhibits WHERE case_id=? ORDER BY exhibit_code,id",
                (case_id,),
            )]
        except Exception:
            return [dict(row) for row in self._connection.execute(
                f"SELECT {columns} FROM evidence_exhibits WHERE case_id=? ORDER BY exhibit_code,id",
                (case_id,),
            )]

    def find_case_exhibit(self, exhibit_id: str) -> dict[str, Any] | None:
        try:
            row = self._connection.execute(
                "SELECT id,case_id,evidence_id,exhibit_code,filename,mime_type,sha256,byte_size,collected_at,collected_by_ref,chain_status,caption,sensitivity,source_record_id,created_at,exhibit_kind,content_blob FROM evidence_exhibits WHERE id=?",
                (exhibit_id,),
            ).fetchone()
        except Exception:
            row = self._connection.execute(
                "SELECT id,case_id,evidence_id,exhibit_code,filename,mime_type,sha256,byte_size,collected_at,collected_by_ref,chain_status,caption,sensitivity,source_record_id,created_at,content_blob FROM evidence_exhibits WHERE id=?",
                (exhibit_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_case_360_forensics(self, case_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute(
            "SELECT * FROM forensic_events WHERE case_id=? ORDER BY id", (case_id,)
        )]

    def list_case_360_trust_issues(self, case_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute(
            "SELECT id,case_id,issue_type,severity,description,source_record_ids_json,status FROM trust_issues WHERE case_id=? ORDER BY id", (case_id,)
        )]

    def find_person(self, person_id: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT id,display_name,age_years,gender_code,source_record_id,created_at,updated_at FROM persons WHERE id=?",
            (person_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_case_person_roles(
        self, case_id: str, role: str | None = None, source_system_ids: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        if role is not None and role not in CASE_PERSON_ROLES:
            raise ValueError("Case person role is not allowed")
        clauses = ["cpr.case_id=?"]
        parameters: list[Any] = [case_id]
        if role is not None:
            clauses.append("cpr.role=?")
            parameters.append(role)
        if source_system_ids is not None:
            source_ids = tuple(dict.fromkeys(source_system_ids))
            if not source_ids:
                return []
            clauses.append("role_source.source_system_id IN (" + ",".join("?" for _ in source_ids) + ")")
            parameters.extend(source_ids)
        sql = (
            "SELECT cpr.id,cpr.case_id,cpr.person_id,cpr.role,cpr.role_sequence,cpr.source_record_id,cpr.created_at,"
            "p.display_name,p.age_years,p.gender_code,p.source_record_id AS person_source_record_id "
            "FROM case_person_roles cpr JOIN persons p ON p.id=cpr.person_id "
            "JOIN source_records role_source ON role_source.id=cpr.source_record_id WHERE "
            + " AND ".join(clauses)
            + " ORDER BY cpr.role,COALESCE(cpr.role_sequence,0),cpr.person_id,cpr.id"
        )
        return [dict(row) for row in self._connection.execute(sql, parameters)]

    def list_case_people(
        self, case_id: str, source_system_ids: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        return self.list_case_person_roles(case_id, source_system_ids=source_system_ids)

    def list_case_person_statements(self, case_id: str) -> list[dict[str, Any]]:
        if not self._has_column("case_person_statements", "id"):
            return []
        sql = (
            "SELECT s.id,s.case_id,s.case_person_role_id,s.statement_type,s.recorded_at,s.body_text,"
            "s.source_record_id,s.created_at,cpr.role,cpr.role_sequence,cpr.person_id,p.display_name "
            "FROM case_person_statements s JOIN case_person_roles cpr ON cpr.id=s.case_person_role_id "
            "JOIN persons p ON p.id=cpr.person_id WHERE s.case_id=? ORDER BY s.recorded_at,s.id LIMIT 50"
        )
        return [dict(row) for row in self._connection.execute(sql, (case_id,))]

    def list_exhibit_custody_events(self, exhibit_id: str) -> list[dict[str, Any]]:
        if not self._has_column("evidence_custody_events", "id"):
            return []
        return [dict(row) for row in self._connection.execute(
            "SELECT id,exhibit_id,sequence,event_type,event_at,custodian_ref,seal_ref,source_record_id,created_at "
            "FROM evidence_custody_events WHERE exhibit_id=? ORDER BY sequence,id LIMIT 20",
            (exhibit_id,),
        )]

    def _has_column(self, table: str, column: str) -> bool:
        try:
            return column in {row[1] for row in self._connection.execute(f"PRAGMA table_info({table})")}
        except sqlite3.OperationalError:
            return False

    def search_case_people_name(
        self, name: str, role: str | None, source_system_ids: Sequence[str], limit: int
    ) -> list[dict[str, Any]]:
        if role is not None and role not in CASE_PERSON_ROLES:
            raise ValueError("Case person role is not allowed")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise ValueError("Person name search is invalid")
        if any(value in name for value in ("%", "_")):
            raise ValueError("Person name search is invalid")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 25:
            raise ValueError("Person search limit is invalid")
        source_ids = tuple(dict.fromkeys(source_system_ids))
        if not source_ids:
            return []
        clauses = ["lower(p.display_name) LIKE lower(?) ESCAPE '\\'", "role_source.source_system_id IN (" + ",".join("?" for _ in source_ids) + ")"]
        parameters: list[Any] = ["%" + self._escaped_like(name.strip()) + "%", *source_ids]
        if role is not None:
            clauses.append("cpr.role=?")
            parameters.append(role)
        sql = (
            "SELECT DISTINCT c.id,c.fir_number,c.crime_number,c.station_id,c.district_id,c.offence,c.incident_at,c.registered_at,c.status,c.source_record_id "
            "FROM case_person_roles cpr JOIN persons p ON p.id=cpr.person_id JOIN cases c ON c.id=cpr.case_id "
            "JOIN source_records role_source ON role_source.id=cpr.source_record_id WHERE "
            + " AND ".join(clauses)
            + " ORDER BY c.incident_at DESC,c.id LIMIT ?"
        )
        return [dict(row) for row in self._connection.execute(sql, (*parameters, limit))]

    @staticmethod
    def _active_only(active_only: bool) -> bool:
        if not isinstance(active_only, bool):
            raise ValueError("Active filter must be a boolean")
        return active_only

    def find_legal_act(self, act_id: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM legal_acts WHERE id=?", (act_id,)).fetchone()
        return dict(row) if row else None

    def find_legal_section(self, section_id: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM legal_sections WHERE id=?", (section_id,)).fetchone()
        return dict(row) if row else None

    def list_legal_acts(self, active_only: bool = True) -> list[dict[str, Any]]:
        active = self._active_only(active_only)
        sql = "SELECT * FROM legal_acts" + (" WHERE active=1" if active else "") + " ORDER BY COALESCE(short_name,act_code),act_code,id LIMIT 50"
        return [dict(row) for row in self._connection.execute(sql)]

    def list_legal_sections(self, act_id: str | None = None, active_only: bool = True) -> list[dict[str, Any]]:
        active = self._active_only(active_only)
        clauses: list[str] = []
        parameters: list[Any] = []
        if act_id is not None:
            clauses.append("act_id=?")
            parameters.append(act_id)
        if active:
            clauses.append("active=1")
        sql = "SELECT * FROM legal_sections" + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY section_code,id LIMIT 100"
        return [dict(row) for row in self._connection.execute(sql, parameters)]

    def list_case_legal_sections(
        self, case_id: str, source_system_ids: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        clauses = ["cls.case_id=?"]
        parameters: list[Any] = [case_id]
        if source_system_ids is not None:
            source_ids = tuple(dict.fromkeys(source_system_ids))
            if not source_ids:
                return []
            clauses.append("link_source.source_system_id IN (" + ",".join("?" for _ in source_ids) + ")")
            parameters.extend(source_ids)
        sql = (
            "SELECT cls.id,cls.case_id,cls.act_id,cls.section_id,cls.act_order,cls.section_order,cls.source_record_id,cls.created_at,"
            "la.act_code,la.description AS act_description,la.short_name,la.active AS act_active,la.source_record_id AS act_source_record_id,"
            "ls.section_code,ls.description AS section_description,ls.active AS section_active,ls.source_record_id AS section_source_record_id "
            "FROM case_legal_sections cls JOIN legal_acts la ON la.id=cls.act_id "
            "JOIN legal_sections ls ON ls.id=cls.section_id AND ls.act_id=cls.act_id "
            "JOIN source_records link_source ON link_source.id=cls.source_record_id WHERE "
            + " AND ".join(clauses)
            + " ORDER BY COALESCE(cls.act_order,2147483647),COALESCE(cls.section_order,2147483647),la.act_code,ls.section_code,cls.id"
        )
        return [dict(row) for row in self._connection.execute(sql, parameters)]

    def find_case_classifications(self, case_id: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT c.id,"
            "cat.id category_id,cat.code category_code,cat.name category_name,cat.active category_active,cat.source_record_id category_source_record_id,"
            "go.id gravity_id,go.code gravity_code,go.name gravity_name,go.active gravity_active,go.source_record_id gravity_source_record_id,"
            "head.id crime_major_head_id,head.name crime_major_head_name,head.active crime_major_head_active,head.source_record_id crime_major_head_source_record_id,"
            "sub.id crime_minor_head_id,sub.name crime_minor_head_name,sub.sequence crime_minor_head_sequence,sub.active crime_minor_head_active,sub.source_record_id crime_minor_head_source_record_id,"
            "status.id case_status_id,status.code case_status_code,status.name case_status_name,status.active case_status_active,status.source_record_id case_status_source_record_id "
            "FROM cases c LEFT JOIN case_categories cat ON cat.id=c.case_category_id "
            "LEFT JOIN gravity_offences go ON go.id=c.gravity_offence_id "
            "LEFT JOIN crime_heads head ON head.id=c.crime_major_head_id "
            "LEFT JOIN crime_subheads sub ON sub.id=c.crime_minor_head_id "
            "LEFT JOIN case_statuses status ON status.id=c.case_status_id WHERE c.id=?",
            (case_id,),
        ).fetchone()
        if not row:
            return None
        values = dict(row)
        def reference(prefix: str, fields: tuple[str, ...]) -> dict[str, Any] | None:
            identifier = values.get(prefix + "_id")
            return None if identifier is None else {field: values.get(prefix + "_" + field) for field in fields} | {"id": identifier}
        return {
            "category": reference("category", ("code", "name", "active", "source_record_id")),
            "gravity": reference("gravity", ("code", "name", "active", "source_record_id")),
            "crime_major_head": reference("crime_major_head", ("name", "active", "source_record_id")),
            "crime_minor_head": reference("crime_minor_head", ("name", "sequence", "active", "source_record_id")),
            "canonical_status": reference("case_status", ("code", "name", "active", "source_record_id")),
        }

    def list_case_categories(self, active_only: bool = True) -> list[dict[str, Any]]:
        active = self._active_only(active_only)
        return [dict(row) for row in self._connection.execute("SELECT * FROM case_categories" + (" WHERE active=1" if active else "") + " ORDER BY code,name,id LIMIT 50")]

    def list_gravity_offences(self, active_only: bool = True) -> list[dict[str, Any]]:
        active = self._active_only(active_only)
        return [dict(row) for row in self._connection.execute("SELECT * FROM gravity_offences" + (" WHERE active=1" if active else "") + " ORDER BY code,name,id LIMIT 50")]

    def list_crime_heads(self, active_only: bool = True) -> list[dict[str, Any]]:
        active = self._active_only(active_only)
        return [dict(row) for row in self._connection.execute("SELECT * FROM crime_heads" + (" WHERE active=1" if active else "") + " ORDER BY name,id LIMIT 50")]

    def list_crime_subheads(self, crime_head_id: str | None = None, active_only: bool = True) -> list[dict[str, Any]]:
        active = self._active_only(active_only)
        clauses: list[str] = []
        parameters: list[Any] = []
        if crime_head_id is not None:
            clauses.append("crime_head_id=?")
            parameters.append(crime_head_id)
        if active:
            clauses.append("active=1")
        sql = "SELECT * FROM crime_subheads" + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY COALESCE(sequence,2147483647),name,id LIMIT 100"
        return [dict(row) for row in self._connection.execute(sql, parameters)]

    def list_case_statuses(self, active_only: bool = True) -> list[dict[str, Any]]:
        active = self._active_only(active_only)
        return [dict(row) for row in self._connection.execute("SELECT * FROM case_statuses" + (" WHERE active=1" if active else "") + " ORDER BY code,name,id LIMIT 50")]

    @staticmethod
    def _source_scope(source_system_ids: Sequence[str] | None, alias: str) -> tuple[str, list[Any]]:
        if source_system_ids is None:
            return "", []
        source_ids = tuple(dict.fromkeys(source_system_ids))
        if not source_ids:
            return " AND 1=0", []
        return " AND " + alias + ".source_system_id IN (" + ",".join("?" for _ in source_ids) + ")", list(source_ids)

    def find_arrest_surrender_event(self, event_id: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM arrest_surrender_events WHERE id=?", (event_id,)).fetchone()
        return dict(row) if row else None

    def list_case_arrest_surrender_events(
        self, case_id: str, source_system_ids: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        scope, parameters = self._source_scope(source_system_ids, "event_source")
        sql = (
            "SELECT event.* FROM arrest_surrender_events event JOIN source_records event_source ON event_source.id=event.source_record_id "
            "WHERE event.case_id=?" + scope + " ORDER BY event.event_at,event.event_type,event.id LIMIT 100"
        )
        return [dict(row) for row in self._connection.execute(sql, (case_id, *parameters))]

    def list_arrest_event_accused(
        self, event_id: str, source_system_ids: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        scope, parameters = self._source_scope(source_system_ids, "link_source")
        sql = (
            "SELECT link.id,link.arrest_event_id,link.person_id,link.case_person_role_id,link.sequence,link.source_record_id,link.created_at,"
            "person.display_name,role.role,role.role_sequence,role.case_id,role.source_record_id AS role_source_record_id "
            "FROM arrest_accused_links link JOIN persons person ON person.id=link.person_id "
            "JOIN case_person_roles role ON role.id=link.case_person_role_id "
            "JOIN source_records link_source ON link_source.id=link.source_record_id "
            "WHERE link.arrest_event_id=?" + scope + " ORDER BY COALESCE(link.sequence,2147483647),link.person_id,link.id LIMIT 50"
        )
        return [dict(row) for row in self._connection.execute(sql, (event_id, *parameters))]

    def find_chargesheet(self, chargesheet_id: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM chargesheets WHERE id=?", (chargesheet_id,)).fetchone()
        return dict(row) if row else None

    def list_case_chargesheets(
        self, case_id: str, source_system_ids: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        scope, parameters = self._source_scope(source_system_ids, "chargesheet_source")
        sql = (
            "SELECT chargesheet.* FROM chargesheets chargesheet JOIN source_records chargesheet_source ON chargesheet_source.id=chargesheet.source_record_id "
            "WHERE chargesheet.case_id=?" + scope + " ORDER BY chargesheet.filed_at DESC,chargesheet.report_type,chargesheet.id LIMIT 50"
        )
        return [dict(row) for row in self._connection.execute(sql, (case_id, *parameters))]

    def _catalog(self, table: str, record_id: str) -> dict[str, Any] | None:
        row = self._connection.execute(f"SELECT * FROM {table} WHERE id=?", (record_id,)).fetchone()
        return dict(row) if row else None

    def _catalog_list(self, table: str, active_only: bool, order: str, scope: tuple[str, str] | None = None, limit: int = 100) -> list[dict[str, Any]]:
        active = self._active_only(active_only); clauses=[]; params: list[Any]=[]
        if scope: clauses.append(f"{scope[0]}=?"); params.append(scope[1])
        if active: clauses.append("active=1")
        sql=f"SELECT * FROM {table}" + (" WHERE " + " AND ".join(clauses) if clauses else "") + f" ORDER BY {order} LIMIT {limit}"
        return [dict(row) for row in self._connection.execute(sql, params)]

    def find_state(self, state_id: str) -> dict[str, Any] | None: return self._catalog("states", state_id)
    def list_states(self, active_only: bool = True) -> list[dict[str, Any]]: return self._catalog_list("states", active_only, "code,id", limit=20)
    def find_district(self, district_id: str) -> dict[str, Any] | None: return self._catalog("districts", district_id)
    def list_districts(self, state_id: str | None = None, active_only: bool = True) -> list[dict[str, Any]]: return self._catalog_list("districts", active_only, "code,id", ("state_id",state_id) if state_id else None)
    def find_police_unit(self, unit_id: str) -> dict[str, Any] | None: return self._catalog("police_units", unit_id)
    def list_police_units(self, district_id: str | None = None, active_only: bool = True) -> list[dict[str, Any]]: return self._catalog_list("police_units", active_only, "code,id", ("district_id",district_id) if district_id else None)
    def find_police_employee(self, employee_id: str) -> dict[str, Any] | None: return self._catalog("police_employees", employee_id)
    def list_police_employees(self, unit_id: str | None = None, active_only: bool = True) -> list[dict[str, Any]]: return self._catalog_list("police_employees", active_only, "employee_code,id", ("unit_id",unit_id) if unit_id else None)
    def find_court(self, court_id: str) -> dict[str, Any] | None: return self._catalog("courts", court_id)
    def list_courts(self, district_id: str | None = None, active_only: bool = True) -> list[dict[str, Any]]: return self._catalog_list("courts", active_only, "code,id", ("district_id",district_id) if district_id else None)
    def list_police_ranks(self, active_only: bool = True) -> list[dict[str, Any]]: return self._catalog_list("police_ranks", active_only, "code,id", limit=20)
    def list_police_designations(self, active_only: bool = True) -> list[dict[str, Any]]: return self._catalog_list("police_designations", active_only, "code,id", limit=20)
    def list_police_unit_types(self, active_only: bool = True) -> list[dict[str, Any]]: return self._catalog_list("police_unit_types", active_only, "code,id", limit=20)

    def find_case_organisation(self, case_id: str) -> dict[str, Any] | None:
        try:
            row = self._connection.execute("""
              SELECT c.id AS case_id,c.state_id,c.canonical_district_id,c.police_unit_id,c.registering_officer_id,c.investigating_officer_id,c.court_id,
                s.code AS state_code,s.name AS state_name,s.active AS state_active,
                d.code AS district_code,d.name AS district_name,d.active AS district_active,
                u.code AS unit_code,u.name AS unit_name,u.active AS unit_active,ut.code AS unit_type_code,ut.name AS unit_type_name,
                e.employee_code,e.display_name AS officer_name,e.active AS officer_active,r.code AS rank_code,r.name AS rank_name,
                pd.code AS designation_code,pd.name AS designation_name,co.code AS court_code,co.name AS court_name,co.active AS court_active,
                io.employee_code AS investigating_employee_code,io.display_name AS investigating_officer_name,io.active AS investigating_officer_active,
                ir.code AS investigating_rank_code,ir.name AS investigating_rank_name
              FROM cases c LEFT JOIN states s ON s.id=c.state_id LEFT JOIN districts d ON d.id=c.canonical_district_id
              LEFT JOIN police_units u ON u.id=c.police_unit_id LEFT JOIN police_unit_types ut ON ut.id=u.unit_type_id
              LEFT JOIN police_employees e ON e.id=c.registering_officer_id LEFT JOIN police_ranks r ON r.id=e.rank_id
              LEFT JOIN police_designations pd ON pd.id=e.designation_id LEFT JOIN courts co ON co.id=c.court_id
              LEFT JOIN police_employees io ON io.id=c.investigating_officer_id LEFT JOIN police_ranks ir ON ir.id=io.rank_id
              WHERE c.id=?""", (case_id,)).fetchone()
        except Exception:
            row = self._connection.execute("""
              SELECT c.id AS case_id,c.state_id,c.canonical_district_id,c.police_unit_id,c.registering_officer_id,c.court_id,
                s.code AS state_code,s.name AS state_name,s.active AS state_active,
                d.code AS district_code,d.name AS district_name,d.active AS district_active,
                u.code AS unit_code,u.name AS unit_name,u.active AS unit_active,ut.code AS unit_type_code,ut.name AS unit_type_name,
                e.employee_code,e.display_name AS officer_name,e.active AS officer_active,r.code AS rank_code,r.name AS rank_name,
                pd.code AS designation_code,pd.name AS designation_name,co.code AS court_code,co.name AS court_name,co.active AS court_active
              FROM cases c LEFT JOIN states s ON s.id=c.state_id LEFT JOIN districts d ON d.id=c.canonical_district_id
              LEFT JOIN police_units u ON u.id=c.police_unit_id LEFT JOIN police_unit_types ut ON ut.id=u.unit_type_id
              LEFT JOIN police_employees e ON e.id=c.registering_officer_id LEFT JOIN police_ranks r ON r.id=e.rank_id
              LEFT JOIN police_designations pd ON pd.id=e.designation_id LEFT JOIN courts co ON co.id=c.court_id WHERE c.id=?""", (case_id,)).fetchone()
        return dict(row) if row else None

    def find_source_passport_record(self, source_record_id: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT sr.*,ss.name AS source_name,ss.description AS limitations "
            "FROM source_records sr JOIN source_systems ss ON ss.id=sr.source_system_id WHERE sr.id=?",
            (source_record_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_source_transformations(self, source_record_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute(
            "SELECT operation,source_field,target_field,rule_version,occurred_at,outcome "
            "FROM transformation_events WHERE source_record_id=? ORDER BY occurred_at,id",
            (source_record_id,),
        )]

    def find_case_dna_case(self, case_id: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
        return dict(row) if row else None

    def list_case_dna_edges(self, case_id: str, request: CaseDnaRequest) -> list[dict[str, Any]]:
        source_placeholders = ",".join("?" for _ in request.source_system_ids)
        sql = (
            "SELECT e.* FROM entity_edges e JOIN source_records sr ON sr.id=e.source_record_id "
            "WHERE e.source_type='CASE' AND e.source_id=? "
            "AND e.relationship_type IN ('RECORDED_DEVICE','SHARED_IMEI','RECORDED_PHONE','RECORDED_VEHICLE') "
            "AND sr.source_system_id IN (" + source_placeholders + ") ORDER BY e.id"
        )
        return [dict(row) for row in self._connection.execute(sql, (case_id, *request.source_system_ids))]

    def list_modus_operandi_features(self) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            "SELECT case_id, value, source_record_id FROM case_dna_features "
            "WHERE feature_type='MODUS_OPERANDI' ORDER BY case_id, value"
        )
        return [
            {"case_id": row["case_id"], "value": row["value"], "source_record_id": row["source_record_id"]}
            for row in rows
        ]

    def find_evidence_graph_case(self, request: EvidenceGraphRequest) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM cases WHERE id=?", (request.case_id,)).fetchone()
        return dict(row) if row else None

    def list_evidence_graph_edges(self, request: EvidenceGraphRequest) -> list[dict[str, Any]]:
        source_placeholders = ",".join("?" for _ in request.source_system_ids)
        relationship_placeholders = ",".join("?" for _ in request.relationship_types)
        sql = (
            "SELECT e.* FROM entity_edges e JOIN source_records sr ON sr.id=e.source_record_id "
            "WHERE e.source_type='CASE' AND e.source_id=? "
            "AND sr.source_system_id IN (" + source_placeholders + ") "
            "AND e.relationship_type IN (" + relationship_placeholders + ") ORDER BY e.id LIMIT ?"
        )
        parameters = (request.case_id, *request.source_system_ids, *request.relationship_types, request.edge_limit)
        return [dict(row) for row in self._connection.execute(sql, parameters)]

    def list_assurance_trust_issues(self, case_id: str | None = None) -> list[dict[str, Any]]:
        if case_id is None:
            rows = self._connection.execute("SELECT id,case_id,issue_type,severity,description,source_record_ids_json,status FROM trust_issues ORDER BY id")
        else:
            rows = self._connection.execute("SELECT id,case_id,issue_type,severity,description,source_record_ids_json,status FROM trust_issues WHERE case_id=? ORDER BY id", (case_id,))
        return [dict(row) for row in rows]

    def list_case_materialized_trust_issues(self, case_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute("SELECT * FROM trust_issues WHERE case_id=? ORDER BY id", (case_id,))]

    def upsert_trust_issue(self, issue: Mapping[str, Any]) -> dict[str, Any]:
        existing = self._connection.execute("SELECT * FROM trust_issues WHERE id=?", (issue["id"],)).fetchone()
        status = "OPEN" if existing is None or existing["status"] == "RESOLVED" else existing["status"]
        acknowledged_at = existing["acknowledged_at"] if existing and status == "ACKNOWLEDGED" else None
        resolved_at = None if status == "OPEN" else (existing["resolved_at"] if existing else None)
        resolution_note = existing["resolution_note"] if existing and status != "OPEN" else None
        self._connection.execute(
            """INSERT INTO trust_issues (id,case_id,issue_type,severity,description,source_record_ids_json,status,rule_code,category,affected_record_type,affected_record_id,affected_field,observed_values_json,deterministic_rule_version,acknowledged_at,resolved_at,resolution_note,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET severity=excluded.severity,description=excluded.description,source_record_ids_json=excluded.source_record_ids_json,rule_code=excluded.rule_code,category=excluded.category,affected_record_type=excluded.affected_record_type,affected_record_id=excluded.affected_record_id,affected_field=excluded.affected_field,observed_values_json=excluded.observed_values_json,deterministic_rule_version=excluded.deterministic_rule_version,status=excluded.status,acknowledged_at=excluded.acknowledged_at,resolved_at=excluded.resolved_at,resolution_note=excluded.resolution_note,updated_at=excluded.updated_at""",
            (issue["id"], issue.get("case_id"), issue["rule_code"], issue["severity"], issue["description"], issue["source_record_ids_json"], status, issue["rule_code"], issue["category"], issue["affected_record_type"], issue["affected_record_id"], issue.get("affected_field"), issue["observed_values_json"], issue["deterministic_rule_version"], acknowledged_at, resolved_at, resolution_note, issue["updated_at"]),
        )
        self._connection.commit()
        return dict(self._connection.execute("SELECT * FROM trust_issues WHERE id=?", (issue["id"],)).fetchone())

    def update_trust_issue_status(self, issue_id: str, status: str, note: str | None, actor_id: str, at: str) -> dict[str, Any] | None:
        if status not in {"ACKNOWLEDGED", "RESOLVED", "OPEN"}:
            raise ValueError("Unsupported assurance status")
        row = self._connection.execute("SELECT * FROM trust_issues WHERE id=?", (issue_id,)).fetchone()
        if not row:
            return None
        self._connection.execute(
            "UPDATE trust_issues SET status=?,acknowledged_at=?,resolved_at=?,resolution_note=?,updated_at=? WHERE id=?",
            (status, at if status == "ACKNOWLEDGED" else row["acknowledged_at"], at if status == "RESOLVED" else None, (note or None) if status == "RESOLVED" else row["resolution_note"], at, issue_id),
        )
        self._connection.commit()
        return dict(self._connection.execute("SELECT * FROM trust_issues WHERE id=?", (issue_id,)).fetchone())

    def create_report_with_initial_version(self, report: Mapping[str, Any], version: Mapping[str, Any]) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT INTO reports (id,investigation_id,owner_user_id,title,status,current_version,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (report["id"], report["investigation_id"], report["owner_user_id"], report["title"], report["status"], report["current_version"], report["created_at"], report["updated_at"]),
            )
            self._connection.execute(
                "INSERT INTO report_versions VALUES (?,?,?,?,?,?,?,?,?,?)",
                (version["id"], report["id"], version["version_number"], version["status"], version["sections_json"], version["notes"], version["html"], version["created_by"], version["created_at"], version["immutable"]),
            )

    def find_report(self, report_id: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
        return dict(row) if row else None

    def _list_reports(self, column: str, user_id: str, limit: int, offset: int) -> list[dict[str, Any]]:
        safe_limit, safe_offset = max(1, min(int(limit), 50)), max(0, int(offset))
        sql = (
            "SELECT r.*,u.username AS owner_name,s.username AS reviewer_name FROM reports r "
            "JOIN users u ON u.id=r.owner_user_id LEFT JOIN users s ON s.id=r.assigned_reviewer_id "
            f"WHERE r.{column}=? ORDER BY r.updated_at DESC,r.id LIMIT ? OFFSET ?"
        )
        return [dict(row) for row in self._connection.execute(sql, (user_id, safe_limit, safe_offset))]

    def list_reports_owned_by(self, user_id: str, limit: int, offset: int) -> list[dict[str, Any]]:
        return self._list_reports("owner_user_id", user_id, limit, offset)

    def list_reports_assigned_to(self, reviewer_id: str, limit: int, offset: int) -> list[dict[str, Any]]:
        return self._list_reports("assigned_reviewer_id", reviewer_id, limit, offset)

    def find_eligible_supervisor(self, username: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT id,username,role FROM users WHERE username=? AND role='SUPERVISOR' AND active=1", (username,)).fetchone()
        return dict(row) if row else None

    def list_eligible_supervisors(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute("SELECT username,role FROM users WHERE role='SUPERVISOR' AND active=1 ORDER BY username")]

    def assign_report_reviewer(self, report_id: str, reviewer_id: str, updated_at: str) -> None:
        with self._connection:
            updated = self._connection.execute("UPDATE reports SET assigned_reviewer_id=?,updated_at=? WHERE id=?", (reviewer_id, updated_at, report_id))
            if updated.rowcount != 1:
                raise ApiError("REPORT_NOT_FOUND", "Report was not found.", 404, False)

    def find_report_version(self, report_id: str, version_number: int) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM report_versions WHERE report_id=? AND version_number=?", (report_id, version_number)).fetchone()
        return dict(row) if row else None

    def find_current_report_version(self, report_id: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT rv.* FROM reports r JOIN report_versions rv ON rv.report_id=r.id AND rv.version_number=r.current_version WHERE r.id=?", (report_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_report_versions(self, report_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute("SELECT * FROM report_versions WHERE report_id=? ORDER BY version_number DESC", (report_id,))]

    def update_report_draft(self, report_id: str, version_number: int, title: str, sections_json: str, notes: str, html: str, updated_at: str) -> None:
        with self._connection:
            updated = self._connection.execute("UPDATE report_versions SET sections_json=?,notes=?,html=? WHERE report_id=? AND version_number=? AND immutable=0", (sections_json, notes, html, report_id, version_number))
            if updated.rowcount != 1:
                raise ApiError("REPORT_IMMUTABLE", "Only an editable draft can be updated.", 409, False)
            self._connection.execute("UPDATE reports SET title=?,updated_at=? WHERE id=?", (title, updated_at, report_id))

    def submit_report_version(self, report_id: str, version_number: int, updated_at: str) -> None:
        with self._connection:
            submitted = self._connection.execute("UPDATE report_versions SET status='IN_REVIEW',immutable=1 WHERE report_id=? AND version_number=? AND immutable=0", (report_id, version_number))
            if submitted.rowcount != 1:
                raise ApiError("REPORT_IMMUTABLE", "Only an editable draft can be submitted.", 409, False)
            updated = self._connection.execute("UPDATE reports SET status='IN_REVIEW',updated_at=? WHERE id=? AND current_version=?", (updated_at, report_id, version_number))
            if updated.rowcount != 1:
                raise ApiError("INVALID_REPORT_TRANSITION", "Report version is no longer current.", 409, False)

    def create_next_report_draft(self, report_id: str, previous_version: int, version: Mapping[str, Any], updated_at: str) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT INTO report_versions VALUES (?,?,?,?,?,?,?,?,?,?)",
                (version["id"], report_id, version["version_number"], "DRAFT", version["sections_json"], version["notes"], version["html"], version["created_by"], version["created_at"], 0),
            )
            updated = self._connection.execute("UPDATE reports SET current_version=?,status='DRAFT',updated_at=? WHERE id=? AND current_version=? AND status='CHANGES_REQUESTED'", (version["version_number"], updated_at, report_id, previous_version))
            if updated.rowcount != 1:
                raise ApiError("INVALID_REPORT_TRANSITION", "A new draft cannot be created from the current report state.", 409, False)

    def create_report_review_decision(self, report_id: str, version_number: int, review: Mapping[str, Any], updated_at: str) -> None:
        with self._connection:
            version = self._connection.execute("SELECT id FROM report_versions WHERE report_id=? AND version_number=?", (report_id, version_number)).fetchone()
            if not version:
                raise ApiError("VERSION_NOT_FOUND", "Report version was not found.", 404, False)
            self._connection.execute("INSERT INTO report_reviews VALUES (?,?,?,?,?,?)", (review["id"], version["id"], review["reviewer_user_id"], review["decision"], review["note"], review["created_at"]))
            updated = self._connection.execute("UPDATE reports SET status=?,updated_at=? WHERE id=? AND current_version=? AND status='IN_REVIEW'", (review["decision"], updated_at, report_id, version_number))
            if updated.rowcount != 1:
                raise ApiError("INVALID_REPORT_TRANSITION", "The reviewed version is no longer in review.", 409, False)

    def list_report_review_history(self, report_id: str) -> list[dict[str, Any]]:
        sql = (
            "SELECT rr.decision,rr.note,rr.created_at,u.username,rv.version_number FROM report_reviews rr "
            "JOIN users u ON u.id=rr.reviewer_user_id JOIN report_versions rv ON rv.id=rr.report_version_id "
            "WHERE rv.report_id=? ORDER BY rr.created_at,rr.id"
        )
        return [dict(row) for row in self._connection.execute(sql, (report_id,))]

    def append_audit_event(self, event: AuditEventInput) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT INTO audit_events VALUES (?,?,?,?,?,?,?)",
                (event.id, event.user_id, event.event_type, event.outcome, event.request_id, event.safe_metadata_json, event.occurred_at),
            )

    def list_audit_events(self, filters: AuditEventFilter) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if filters.actor_user_id:
            clauses.append("user_id=?")
            parameters.append(filters.actor_user_id)
        if filters.actor_role:
            clauses.append("user_id IN (SELECT id FROM users WHERE role=?)")
            parameters.append(filters.actor_role)
        for value, column in ((filters.event_type, "event_type"), (filters.outcome, "outcome"), (filters.request_id, "request_id")):
            if value:
                clauses.append(f"{column}=?")
                parameters.append(value)
        for value, operator in ((filters.start, ">="), (filters.end, "<=")):
            if value:
                clauses.append(f"occurred_at {operator} ?")
                parameters.append(value)
        for value in (filters.investigation_id, filters.report_id):
            if value:
                clauses.append("safe_metadata_json LIKE ?")
                parameters.append("%" + value + "%")
        sql = "SELECT id,user_id,event_type,outcome,request_id,safe_metadata_json,occurred_at FROM audit_events"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY occurred_at DESC,id DESC LIMIT ? OFFSET ?"
        parameters.extend((filters.limit, filters.offset))
        return [dict(row) for row in self._connection.execute(sql, parameters)]

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
            "case_person_roles",
            "legal_acts", "legal_sections", "case_legal_sections", "case_categories", "gravity_offences",
            "crime_heads", "crime_subheads", "case_statuses",
            "arrest_surrender_events", "arrest_accused_links", "chargesheets",
            "states", "districts", "police_unit_types", "police_units", "police_ranks", "police_designations", "police_employees", "courts",
            "aliases", "organisations", "phones", "devices", "vehicles", "locations", "documents",
            "evidence_records", "evidence_exhibits", "forensic_events", "public_context", "entity_edges", "case_dna_features",
            "trust_issues", "import_jobs", "import_failures",
            "case_person_statements", "evidence_custody_events",
            "users", "sessions", "investigations", "investigation_messages", "audit_events",
        }
        if table not in allowed:
            raise ValueError("Unknown canonical table")
        return int(self._connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    def get_dashboard_stats(self, district: str | None = None, station: str | None = None) -> dict:
        """Return aggregate FIR stats for the dashboard."""
        con = self._connection
        try:
            total = int(con.execute("SELECT COUNT(*) FROM cases").fetchone()[0])
        except Exception:
            total = 0
        try:
            # Pending = unresolved cases
            pending = int(con.execute(
                "SELECT COUNT(*) FROM cases c LEFT JOIN case_statuses cs ON c.canonical_status_id=cs.id "
                "WHERE cs.name IS NULL OR cs.name NOT IN ('Resolved','Charge-Sheeted','Closed','Convicted')"
            ).fetchone()[0])
        except Exception:
            pending = 0
        try:
            resolved = int(con.execute(
                "SELECT COUNT(*) FROM cases c LEFT JOIN case_statuses cs ON c.canonical_status_id=cs.id "
                "WHERE cs.name IN ('Resolved','Charge-Sheeted','Closed','Convicted')"
            ).fetchone()[0])
        except Exception:
            resolved = total - pending if total else 0
        try:
            # Priority = cases with gravity HIGH or CRITICAL
            priority = int(con.execute(
                "SELECT COUNT(*) FROM cases c LEFT JOIN gravity_offences g ON c.gravity_offence_id=g.id "
                "WHERE g.severity IN ('HIGH','CRITICAL') OR c.gravity_offence_id IS NULL"
            ).fetchone()[0])
            priority = min(priority, max(1, total // 10))  # cap at 10% for display
        except Exception:
            priority = 0
        try:
            recent_rows = con.execute(
                "SELECT c.id, c.crime_number, c.fir_number, c.offence_head, c.offence_type, "
                "       pu.name as unit_name, cs.name as status_name "
                "FROM cases c "
                "LEFT JOIN police_units pu ON c.police_unit_id=pu.id "
                "LEFT JOIN case_statuses cs ON c.canonical_status_id=cs.id "
                "ORDER BY c.rowid DESC LIMIT 8"
            ).fetchall()
            recent_cases = [
                {
                    "id": r[0], "crime_number": r[1] or r[2],
                    "offence_type": r[3] or r[4] or "Unknown",
                    "unit_name": r[5] or "—",
                    "status": r[6] or "Pending",
                }
                for r in recent_rows
            ]
        except Exception:
            recent_cases = []
        try:
            offence_rows = con.execute(
                "SELECT offence_head, COUNT(*) as cnt FROM cases WHERE offence_head IS NOT NULL "
                "GROUP BY offence_head ORDER BY cnt DESC LIMIT 6"
            ).fetchall()
            by_offence = [{"offence": r[0], "count": r[1]} for r in offence_rows]
        except Exception:
            by_offence = []
        return {
            "total_firs": total,
            "pending": pending,
            "resolved": resolved,
            "priority": priority,
            "recent_cases": recent_cases,
            "by_offence": by_offence,
        }

    def close(self) -> None:
        self._connection.close()

