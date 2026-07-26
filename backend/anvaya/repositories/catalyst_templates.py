"""Fixed, offline query definitions for a future Catalyst Data Store adapter.

The text is a design-time template only.  It has never been sent to Catalyst;
logical parameters are validated separately and final transport binding remains
an explicit M7.2B sandbox gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from backend.anvaya.api.errors import ApiError


class CatalystQueryName(str, Enum):
    ACTIVE_USER_BY_USERNAME = "active_user_by_username"
    USER_BY_USERNAME = "user_by_username"
    USER_BY_ID = "user_by_id"
    SOURCE_SYSTEM_LIST = "source_system_list"
    SOURCE_SYSTEM_BY_ID = "source_system_by_id"
    CASE_BY_ID = "case_by_id"
    SOURCE_RECORD_BY_ID = "source_record_by_id"
    SCHEMA_VERSION = "schema_version"
    INVESTIGATION_BY_ID = "investigation_by_id"
    INVESTIGATIONS_BY_OWNER = "investigations_by_owner"
    QUERY_HISTORY_BY_ID = "query_history_by_id"
    QUERY_HISTORY_BY_INVESTIGATION = "query_history_by_investigation"
    SEARCH_CASE_CANDIDATES = "search_case_candidates"
    DISCOVERY_CANDIDATES = "discovery_candidates"
    RELATIONSHIP_EDGES = "relationship_edges"
    CASE_360_ENTITIES = "case_360_entities"
    CASE_360_EVIDENCE = "case_360_evidence"
    CASE_360_FORENSICS = "case_360_forensics"
    CASE_360_TRUST_ISSUES = "case_360_trust_issues"
    SOURCE_PASSPORT_RECORD = "source_passport_record"
    SOURCE_TRANSFORMATIONS = "source_transformations"
    CASE_DNA_EDGES = "case_dna_edges"
    EVIDENCE_GRAPH_EDGES = "evidence_graph_edges"
    ASSURANCE_TRUST_ISSUES = "assurance_trust_issues"
    ASSURANCE_TRUST_ISSUES_BY_CASE = "assurance_trust_issues_by_case"
    REPORT_BY_ID = "report_by_id"
    REPORTS_BY_OWNER = "reports_by_owner"
    REPORTS_BY_REVIEWER = "reports_by_reviewer"
    ELIGIBLE_SUPERVISOR_BY_USERNAME = "eligible_supervisor_by_username"
    ELIGIBLE_SUPERVISORS = "eligible_supervisors"
    REPORT_VERSION_BY_NUMBER = "report_version_by_number"
    CURRENT_REPORT_VERSION = "current_report_version"
    REPORT_VERSIONS = "report_versions"
    REPORT_REVIEW_HISTORY = "report_review_history"


class CatalystOperationKind(str, Enum):
    READ = "read"
    WRITE = "write"


class CatalystParameterKind(str, Enum):
    CANONICAL_ID = "canonical_id"
    STRING = "string"
    INTEGER = "integer"
    LIMIT = "limit"
    OFFSET = "offset"
    TIMESTAMP = "timestamp"
    DATE = "date"
    BOOLEAN = "boolean"
    STRING_LIST = "string_list"
    RELATIONSHIP_TYPE_LIST = "relationship_type_list"


@dataclass(frozen=True)
class CatalystParameterDefinition:
    name: str
    kind: CatalystParameterKind
    required: bool = True
    allow_null: bool = False
    maximum: int | None = None


@dataclass(frozen=True)
class CatalystQueryTemplate:
    name: CatalystQueryName
    operation: CatalystOperationKind
    text: str
    parameters: tuple[CatalystParameterDefinition, ...]
    result_shape: str
    ordering: str
    max_results: int
    verification_status: str
    notes: str


@dataclass(frozen=True)
class CatalystQueryParameters:
    values: Mapping[str, Any]


@dataclass(frozen=True)
class CatalystQueryRequest:
    query: CatalystQueryTemplate
    parameters: CatalystQueryParameters


class CatalystTemplateRegistry:
    """Immutable server-owned template registry; no caller can add query text."""

    def __init__(self, templates: tuple[CatalystQueryTemplate, ...]):
        names = [template.name for template in templates]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate Catalyst query template name")
        self._templates = MappingProxyType({template.name: template for template in templates})

    def get(self, name: CatalystQueryName | str) -> CatalystQueryTemplate:
        try:
            normalized = name if isinstance(name, CatalystQueryName) else CatalystQueryName(name)
        except ValueError as error:
            raise ApiError("CATALYST_QUERY_UNSUPPORTED", "This Catalyst query is not supported.", 400, False) from error
        try:
            return self._templates[normalized]
        except KeyError as error:
            raise ApiError("CATALYST_QUERY_UNSUPPORTED", "This Catalyst query is not supported.", 400, False) from error

    @property
    def names(self) -> tuple[CatalystQueryName, ...]:
        return tuple(self._templates)


def _template(
    name: CatalystQueryName, text: str, parameters: tuple[CatalystParameterDefinition, ...], result_shape: str,
    ordering: str = "exact match", max_results: int = 1, notes: str = "Unverified offline template.",
) -> CatalystQueryTemplate:
    return CatalystQueryTemplate(
        name=name,
        operation=CatalystOperationKind.READ,
        text=text,
        parameters=parameters,
        result_shape=result_shape,
        ordering=ordering,
        max_results=max_results,
        verification_status="unverified",
        notes=notes,
    )


CANONICAL_ID = CatalystParameterDefinition("id", CatalystParameterKind.CANONICAL_ID)

DEFAULT_CATALYST_TEMPLATES = CatalystTemplateRegistry((
    _template(CatalystQueryName.ACTIVE_USER_BY_USERNAME,
              "SELECT id, username, password_hash, role, assigned_station, assigned_district, active FROM anvaya_users WHERE username = :username AND active = true LIMIT 0,1",
              (CatalystParameterDefinition("username", CatalystParameterKind.STRING, maximum=128),), "user"),
    _template(CatalystQueryName.USER_BY_USERNAME,
              "SELECT id, username, password_hash, role, assigned_station, assigned_district, active FROM anvaya_users WHERE username = :username LIMIT 0,1",
              (CatalystParameterDefinition("username", CatalystParameterKind.STRING, maximum=128),), "user"),
    _template(CatalystQueryName.USER_BY_ID,
              "SELECT id, username, password_hash, role, assigned_station, assigned_district, active FROM anvaya_users WHERE id = :id LIMIT 0,1",
              (CANONICAL_ID,), "user"),
    _template(CatalystQueryName.SOURCE_SYSTEM_LIST,
              "SELECT id, name, source_tier, access_class, reliability_role, status, last_successful_sync, freshness_threshold_hours, version, connector_type, description, priority FROM anvaya_source_systems ORDER BY priority ASC, id ASC LIMIT 0,:limit",
              (CatalystParameterDefinition("limit", CatalystParameterKind.LIMIT, maximum=50),), "source_system", "priority ASC, id ASC", 50),
    _template(CatalystQueryName.SOURCE_SYSTEM_BY_ID,
              "SELECT id, name, source_tier, access_class, reliability_role, status, last_successful_sync, freshness_threshold_hours, version, connector_type, description, priority FROM anvaya_source_systems WHERE id = :id LIMIT 0,1",
              (CANONICAL_ID,), "source_system"),
    _template(CatalystQueryName.CASE_BY_ID,
              "SELECT id, fir_number, crime_number, station_id, district_id, offence, incident_at, registered_at, status, source_record_id FROM anvaya_cases WHERE id = :id LIMIT 0,1",
              (CANONICAL_ID,), "case"),
    _template(CatalystQueryName.SOURCE_RECORD_BY_ID,
              "SELECT id, source_system_id, external_id, version, source_updated_at, imported_at, access_class, reliability_role, freshness_state, checksum, payload_json FROM anvaya_source_records WHERE id = :id LIMIT 0,1",
              (CANONICAL_ID,), "source_record"),
    _template(CatalystQueryName.SCHEMA_VERSION,
              "SELECT MAX(version) AS version FROM anvaya_schema_versions LIMIT 0,1",
              (), "schema_state"),
    _template(CatalystQueryName.INVESTIGATION_BY_ID,
              "SELECT id, user_id, title, purpose, selected_sources_json, assigned_station, assigned_district, created_at, updated_at FROM anvaya_investigations WHERE id = :id LIMIT 0,1",
              (CANONICAL_ID,), "investigation", notes="Requires canonical investigation ID index; unverified offline template."),
    _template(CatalystQueryName.INVESTIGATIONS_BY_OWNER,
              "SELECT id, user_id, title, purpose, selected_sources_json, assigned_station, assigned_district, created_at, updated_at FROM anvaya_investigations WHERE user_id = :user_id ORDER BY updated_at DESC, id ASC LIMIT 0,:limit",
              (CatalystParameterDefinition("user_id", CatalystParameterKind.CANONICAL_ID), CatalystParameterDefinition("limit", CatalystParameterKind.LIMIT, maximum=50)), "investigation", "updated_at DESC, id ASC", 50, "Requires owner/updated timestamp index; unverified offline template."),
    _template(CatalystQueryName.QUERY_HISTORY_BY_ID,
              "SELECT id, original_text, query_plan_json, confirmed, parent_message_id, execution_intent, result_count, request_id, created_at FROM anvaya_investigation_messages WHERE id = :id AND investigation_id = :investigation_id LIMIT 0,1",
              (CANONICAL_ID, CatalystParameterDefinition("investigation_id", CatalystParameterKind.CANONICAL_ID)), "query_history", notes="Requires canonical message and investigation scope indexes; unverified offline template."),
    _template(CatalystQueryName.QUERY_HISTORY_BY_INVESTIGATION,
              "SELECT id, original_text, query_plan_json, confirmed, parent_message_id, execution_intent, result_count, request_id, created_at FROM anvaya_investigation_messages WHERE investigation_id = :investigation_id ORDER BY created_at ASC, id ASC LIMIT 0,:limit",
              (CatalystParameterDefinition("investigation_id", CatalystParameterKind.CANONICAL_ID), CatalystParameterDefinition("limit", CatalystParameterKind.LIMIT, maximum=50)), "query_history", "created_at ASC, id ASC", 50, "Requires investigation/created timestamp index; unverified offline template."),
    _template(CatalystQueryName.SEARCH_CASE_CANDIDATES,
              "SELECT c.id, c.fir_number, c.crime_number, c.station_id, c.district_id, c.offence, c.incident_at, c.registered_at, c.status, c.source_record_id, sr.freshness_state, sr.source_system_id, sr.reliability_role, sr.access_class FROM anvaya_cases c JOIN anvaya_source_records sr ON sr.id = c.source_record_id WHERE (:offence IS NULL OR c.offence = :offence) AND (:status IS NULL OR c.status = :status) AND (:date_from IS NULL OR c.incident_at >= :date_from) AND (:date_to IS NULL OR c.incident_at <= :date_to) AND (:case_identifier IS NULL OR c.id = :case_identifier OR c.fir_number = :case_identifier OR c.crime_number = :case_identifier) AND (:location IS NULL OR c.station_id = :location OR c.district_id = :location) AND (:source_system_ids IS NULL OR sr.source_system_id IN :source_system_ids) AND (:phone IS NULL OR EXISTS FIXED_PHONE_MATCH) AND (:imei IS NULL OR EXISTS FIXED_IMEI_MATCH) AND (:vehicle_registration IS NULL OR EXISTS FIXED_VEHICLE_MATCH) ORDER BY c.incident_at DESC, c.id ASC LIMIT :offset,:limit",
              (
                  CatalystParameterDefinition("offence", CatalystParameterKind.STRING, required=False, allow_null=True, maximum=128),
                  CatalystParameterDefinition("status", CatalystParameterKind.STRING, required=False, allow_null=True, maximum=64),
                  CatalystParameterDefinition("date_from", CatalystParameterKind.DATE, required=False, allow_null=True),
                  CatalystParameterDefinition("date_to", CatalystParameterKind.DATE, required=False, allow_null=True),
                  CatalystParameterDefinition("case_identifier", CatalystParameterKind.STRING, required=False, allow_null=True, maximum=128),
                  CatalystParameterDefinition("location", CatalystParameterKind.STRING, required=False, allow_null=True, maximum=128),
                  CatalystParameterDefinition("phone", CatalystParameterKind.STRING, required=False, allow_null=True, maximum=128),
                  CatalystParameterDefinition("imei", CatalystParameterKind.STRING, required=False, allow_null=True, maximum=128),
                  CatalystParameterDefinition("vehicle_registration", CatalystParameterKind.STRING, required=False, allow_null=True, maximum=128),
                  CatalystParameterDefinition("source_system_ids", CatalystParameterKind.STRING_LIST, required=False, allow_null=True),
                  CatalystParameterDefinition("limit", CatalystParameterKind.LIMIT, maximum=25),
                  CatalystParameterDefinition("offset", CatalystParameterKind.OFFSET),
              ), "search_candidate", "incident_at DESC, id ASC", 25,
              "Fixed logical template only. Optional predicates, IN-list encoding, EXISTS syntax, joins, and LIMIT/OFFSET are unverified against live Catalyst."),
    _template(CatalystQueryName.DISCOVERY_CANDIDATES,
              "SELECT e.source_id AS base_case_id, e.target_type, e.relationship_type, e.source_record_id AS edge_source_record_id, link.source_id AS candidate_id, link.source_record_id AS link_source_record_id, c.id, c.fir_number, c.crime_number, c.station_id, c.district_id, c.offence, c.incident_at, c.registered_at, c.status, c.source_record_id, candidate_source.freshness_state, candidate_source.source_system_id, candidate_source.reliability_role, candidate_source.access_class FROM anvaya_entity_edges e JOIN anvaya_entity_edges link ON link.target_type = e.target_type AND link.target_id = e.target_id JOIN anvaya_cases c ON c.id = link.source_id JOIN anvaya_source_records candidate_source ON candidate_source.id = c.source_record_id WHERE e.source_type = 'CASE' AND e.source_id IN :seed_case_ids AND link.source_type = 'CASE' AND link.source_id <> e.source_id AND candidate_source.source_system_id IN :source_system_ids AND FIXED_EDGE_AND_LINK_SOURCE_SCOPE ORDER BY c.incident_at DESC, c.id ASC, e.id ASC, link.id ASC LIMIT :offset,:limit",
              (
                  CatalystParameterDefinition("seed_case_ids", CatalystParameterKind.STRING_LIST),
                  CatalystParameterDefinition("source_system_ids", CatalystParameterKind.STRING_LIST),
                  CatalystParameterDefinition("limit", CatalystParameterKind.LIMIT, maximum=25),
                  CatalystParameterDefinition("offset", CatalystParameterKind.OFFSET),
              ), "discovery_candidate", "incident_at DESC, candidate id ASC, stored edge IDs ASC", 25,
              "Fixed logical template only. Edge/link source scope, IN-list encoding, joins, and LIMIT/OFFSET are unverified against live Catalyst."),
    _template(CatalystQueryName.RELATIONSHIP_EDGES,
              "SELECT e.id, e.source_type, e.source_id, e.target_type, e.target_id, e.relationship_type, e.edge_class, e.source_record_id, sr.freshness_state, sr.reliability_role, sr.access_class, sr.source_system_id FROM anvaya_entity_edges e JOIN anvaya_source_records sr ON sr.id = e.source_record_id WHERE e.relationship_type IN :relationship_types AND sr.source_system_id IN :source_system_ids ORDER BY e.id ASC LIMIT 0,:edge_limit",
              (
                  CatalystParameterDefinition("relationship_types", CatalystParameterKind.RELATIONSHIP_TYPE_LIST),
                  CatalystParameterDefinition("source_system_ids", CatalystParameterKind.STRING_LIST),
                  CatalystParameterDefinition("edge_limit", CatalystParameterKind.LIMIT, maximum=200),
              ), "relationship_edge", "id ASC", 200,
              "Fixed logical template only. Relationship/source IN-list encoding and join behavior are unverified against live Catalyst."),
    _template(CatalystQueryName.CASE_360_ENTITIES,
              "SELECT e.id AS edge_id, e.source_id AS case_id, e.target_type, e.target_id, e.source_record_id AS edge_source_record_id, FIXED_CASE_360_ENTITY_VALUE AS value, FIXED_CASE_360_ENTITY_SOURCE AS entity_source_record_id FROM anvaya_entity_edges e WHERE e.source_type = 'CASE' AND e.source_id = :case_id AND e.target_type IN ('PERSON','PHONE','DEVICE','VEHICLE','LOCATION') ORDER BY e.id ASC LIMIT 0,200",
              (CatalystParameterDefinition("case_id", CatalystParameterKind.CANONICAL_ID),), "case_360_entity", "edge_id ASC", 200,
              "Fixed logical template only. CASE-style entity projection and joins are unverified against live Catalyst."),
    _template(CatalystQueryName.CASE_360_EVIDENCE,
              "SELECT id, case_id, evidence_type, description, status, sensitivity, source_record_id FROM anvaya_evidence_records WHERE case_id = :case_id ORDER BY id ASC LIMIT 0,200",
              (CatalystParameterDefinition("case_id", CatalystParameterKind.CANONICAL_ID),), "case_360_evidence", "id ASC", 200,
              "Fixed logical template only. Case scope and provider limits are unverified against live Catalyst."),
    _template(CatalystQueryName.CASE_360_FORENSICS,
              "SELECT id, case_id, event_type, occurred_at, result_status, source_record_id FROM anvaya_forensic_events WHERE case_id = :case_id ORDER BY id ASC LIMIT 0,200",
              (CatalystParameterDefinition("case_id", CatalystParameterKind.CANONICAL_ID),), "case_360_forensic", "id ASC", 200,
              "Fixed logical template only. Case scope and provider limits are unverified against live Catalyst."),
    _template(CatalystQueryName.CASE_360_TRUST_ISSUES,
              "SELECT id, case_id, issue_type, severity, description, source_record_ids_json, status FROM anvaya_trust_issues WHERE case_id = :case_id ORDER BY id ASC LIMIT 0,200",
              (CatalystParameterDefinition("case_id", CatalystParameterKind.CANONICAL_ID),), "case_360_trust_issue", "id ASC", 200,
              "Fixed logical template only. Case scope and provider limits are unverified against live Catalyst."),
    _template(CatalystQueryName.SOURCE_PASSPORT_RECORD,
              "SELECT sr.id, sr.source_system_id, sr.external_id, sr.version, sr.source_updated_at, sr.imported_at, sr.access_class, sr.reliability_role, sr.freshness_state, sr.checksum, sr.payload_json, ss.name AS source_name, ss.description AS limitations FROM anvaya_source_records sr JOIN anvaya_source_systems ss ON ss.id = sr.source_system_id WHERE sr.id = :id LIMIT 0,1",
              (CANONICAL_ID,), "source_passport_record", notes="Fixed logical template only. Source record/source system join and text/JSON behavior are unverified against live Catalyst."),
    _template(CatalystQueryName.SOURCE_TRANSFORMATIONS,
              "SELECT operation, source_field, target_field, rule_version, occurred_at, outcome FROM anvaya_transformation_events WHERE source_record_id = :source_record_id ORDER BY occurred_at ASC, id ASC LIMIT 0,200",
              (CatalystParameterDefinition("source_record_id", CatalystParameterKind.CANONICAL_ID),), "source_transformation", "occurred_at ASC, stored id ASC", 200,
              "Fixed logical template only. Transformation ordering and provider limits are unverified against live Catalyst."),
    _template(CatalystQueryName.CASE_DNA_EDGES,
              "SELECT e.id, e.source_type, e.source_id, e.target_type, e.target_id, e.relationship_type, e.edge_class, e.source_record_id FROM anvaya_entity_edges e JOIN anvaya_source_records sr ON sr.id = e.source_record_id WHERE e.source_type = 'CASE' AND e.source_id = :case_id AND sr.source_system_id IN :source_system_ids ORDER BY e.id ASC LIMIT 0,200",
              (CatalystParameterDefinition("case_id", CatalystParameterKind.CANONICAL_ID), CatalystParameterDefinition("source_system_ids", CatalystParameterKind.STRING_LIST)), "intelligence_edge", "id ASC", 200,
              "Fixed logical template only. Source join and IN-list behavior are unverified against live Catalyst."),
    _template(CatalystQueryName.EVIDENCE_GRAPH_EDGES,
              "SELECT e.id, e.source_type, e.source_id, e.target_type, e.target_id, e.relationship_type, e.edge_class, e.source_record_id FROM anvaya_entity_edges e JOIN anvaya_source_records sr ON sr.id = e.source_record_id WHERE e.source_type = 'CASE' AND e.source_id = :case_id AND sr.source_system_id IN :source_system_ids AND e.relationship_type IN :relationship_types ORDER BY e.id ASC LIMIT 0,:edge_limit",
              (CatalystParameterDefinition("case_id", CatalystParameterKind.CANONICAL_ID), CatalystParameterDefinition("source_system_ids", CatalystParameterKind.STRING_LIST), CatalystParameterDefinition("relationship_types", CatalystParameterKind.RELATIONSHIP_TYPE_LIST), CatalystParameterDefinition("edge_limit", CatalystParameterKind.LIMIT, maximum=20)), "intelligence_edge", "id ASC", 20,
              "Fixed logical template only. Source join, relationship IN-list behavior, and provider limits are unverified against live Catalyst."),
    _template(CatalystQueryName.ASSURANCE_TRUST_ISSUES,
              "SELECT id, case_id, issue_type, severity, description, source_record_ids_json, status FROM anvaya_trust_issues ORDER BY id ASC LIMIT 0,200",
              (), "case_360_trust_issue", "id ASC", 200,
              "Fixed logical template only. Provider ordering and limits are unverified against live Catalyst."),
    _template(CatalystQueryName.ASSURANCE_TRUST_ISSUES_BY_CASE,
              "SELECT id, case_id, issue_type, severity, description, source_record_ids_json, status FROM anvaya_trust_issues WHERE case_id = :case_id ORDER BY id ASC LIMIT 0,200",
              (CatalystParameterDefinition("case_id", CatalystParameterKind.CANONICAL_ID),), "case_360_trust_issue", "id ASC", 200,
              "Fixed logical template only. Case scope, provider ordering and limits are unverified against live Catalyst."),
    _template(CatalystQueryName.REPORT_BY_ID,
              "SELECT id, investigation_id, owner_user_id, assigned_reviewer_id, title, status, current_version, created_at, updated_at FROM anvaya_reports WHERE id = :id LIMIT 0,1",
              (CANONICAL_ID,), "report", notes="Fixed logical template only. Report schema and exact lookup are unverified against live Catalyst."),
    _template(CatalystQueryName.REPORTS_BY_OWNER,
              "SELECT r.id, r.investigation_id, r.owner_user_id, r.assigned_reviewer_id, r.title, r.status, r.current_version, r.created_at, r.updated_at, u.username AS owner_name, s.username AS reviewer_name FROM anvaya_reports r JOIN anvaya_users u ON u.id = r.owner_user_id LEFT JOIN anvaya_users s ON s.id = r.assigned_reviewer_id WHERE r.owner_user_id = :user_id ORDER BY r.updated_at DESC, r.id ASC LIMIT :offset,:limit",
              (CatalystParameterDefinition("user_id", CatalystParameterKind.CANONICAL_ID), CatalystParameterDefinition("limit", CatalystParameterKind.LIMIT, maximum=50), CatalystParameterDefinition("offset", CatalystParameterKind.OFFSET)), "report_list", "updated_at DESC, id ASC", 50,
              "Fixed logical template only. Joins and LIMIT/OFFSET are unverified against live Catalyst."),
    _template(CatalystQueryName.REPORTS_BY_REVIEWER,
              "SELECT r.id, r.investigation_id, r.owner_user_id, r.assigned_reviewer_id, r.title, r.status, r.current_version, r.created_at, r.updated_at, u.username AS owner_name, s.username AS reviewer_name FROM anvaya_reports r JOIN anvaya_users u ON u.id = r.owner_user_id LEFT JOIN anvaya_users s ON s.id = r.assigned_reviewer_id WHERE r.assigned_reviewer_id = :user_id ORDER BY r.updated_at DESC, r.id ASC LIMIT :offset,:limit",
              (CatalystParameterDefinition("user_id", CatalystParameterKind.CANONICAL_ID), CatalystParameterDefinition("limit", CatalystParameterKind.LIMIT, maximum=50), CatalystParameterDefinition("offset", CatalystParameterKind.OFFSET)), "report_list", "updated_at DESC, id ASC", 50,
              "Fixed logical template only. Joins and LIMIT/OFFSET are unverified against live Catalyst."),
    _template(CatalystQueryName.ELIGIBLE_SUPERVISOR_BY_USERNAME,
              "SELECT id, username, role FROM anvaya_users WHERE username = :username AND role = 'SUPERVISOR' AND active = true LIMIT 0,1",
              (CatalystParameterDefinition("username", CatalystParameterKind.STRING, maximum=128),), "eligible_supervisor", notes="Fixed logical template only. Active-role predicate is unverified against live Catalyst."),
    _template(CatalystQueryName.ELIGIBLE_SUPERVISORS,
              "SELECT username, role FROM anvaya_users WHERE role = 'SUPERVISOR' AND active = true ORDER BY username ASC LIMIT 0,50",
              (), "eligible_supervisor_list", "username ASC", 50,
              "Fixed logical template only. Active-role predicate and provider ordering are unverified against live Catalyst."),
    _template(CatalystQueryName.REPORT_VERSION_BY_NUMBER,
              "SELECT id, report_id, version_number, status, sections_json, notes, html, created_by, created_at, immutable FROM anvaya_report_versions WHERE report_id = :report_id AND version_number = :version_number LIMIT 0,1",
              (CatalystParameterDefinition("report_id", CatalystParameterKind.CANONICAL_ID), CatalystParameterDefinition("version_number", CatalystParameterKind.INTEGER)), "report_version", notes="Fixed logical template only. Version uniqueness is unverified against live Catalyst."),
    _template(CatalystQueryName.CURRENT_REPORT_VERSION,
              "SELECT rv.id, rv.report_id, rv.version_number, rv.status, rv.sections_json, rv.notes, rv.html, rv.created_by, rv.created_at, rv.immutable FROM anvaya_reports r JOIN anvaya_report_versions rv ON rv.report_id = r.id AND rv.version_number = r.current_version WHERE r.id = :report_id LIMIT 0,1",
              (CatalystParameterDefinition("report_id", CatalystParameterKind.CANONICAL_ID),), "report_version", notes="Fixed logical template only. Current-version join is unverified against live Catalyst."),
    _template(CatalystQueryName.REPORT_VERSIONS,
              "SELECT id, report_id, version_number, status, sections_json, notes, html, created_by, created_at, immutable FROM anvaya_report_versions WHERE report_id = :report_id ORDER BY version_number DESC LIMIT 0,50",
              (CatalystParameterDefinition("report_id", CatalystParameterKind.CANONICAL_ID),), "report_version", "version_number DESC", 50,
              "Fixed logical template only. Version ordering and provider limits are unverified against live Catalyst."),
    _template(CatalystQueryName.REPORT_REVIEW_HISTORY,
              "SELECT rr.decision, rr.note, rr.created_at, u.username, rv.version_number FROM anvaya_report_reviews rr JOIN anvaya_users u ON u.id = rr.reviewer_user_id JOIN anvaya_report_versions rv ON rv.id = rr.report_version_id WHERE rv.report_id = :report_id ORDER BY rr.created_at ASC, rr.id ASC LIMIT 0,50",
              (CatalystParameterDefinition("report_id", CatalystParameterKind.CANONICAL_ID),), "report_review", "created_at ASC, stored review id ASC", 50,
              "Fixed logical template only. Review joins and ordering are unverified against live Catalyst."),
))
