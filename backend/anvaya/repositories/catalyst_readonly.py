"""Offline-only, fake-client-backed read slice for future Catalyst storage.

This is intentionally not selected by the application factory.  It does not
contain a transport, credentials, SDK import, SQLite fallback, or write path.
"""
from __future__ import annotations

from abc import update_abstractmethods
from typing import Any

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.capabilities import Capability, CapabilityState
from backend.anvaya.platform.catalyst_client import CatalystDataStoreClient
from backend.anvaya.platform.catalyst_errors import CatalystClientFailure, translate_catalyst_failure
from backend.anvaya.repositories.base import Repository
from backend.anvaya.repositories.catalyst_gateway import CatalystReadGateway
from backend.anvaya.repositories.catalyst_templates import CatalystQueryName
from backend.anvaya.repositories.search_filter import CaseSearchFilter
from backend.anvaya.repositories.discovery_requests import DiscoveryRequest, RELATIONSHIP_TYPES, RelationshipPathRequest
from backend.anvaya.repositories.intelligence_requests import CaseDnaRequest, EvidenceGraphRequest


class CatalystReadOnlyRepository(Repository):
    """A deliberately narrow read-only contract proven only with a fake client."""

    backend_name = "catalyst-readonly-offline"

    def __init__(self, gateway: CatalystReadGateway, client: CatalystDataStoreClient):
        self._gateway = gateway
        self._client = client

    def _unsupported(self, _operation: str) -> None:
        raise ApiError("CATALYST_NOT_IMPLEMENTED", "Catalyst integration is not implemented in this milestone.", 503, False)

    @staticmethod
    def _one(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not rows:
            return None
        if len(rows) != 1:
            raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        return rows[0]

    @classmethod
    def _exact(cls, rows: list[dict[str, Any]], canonical_id: str) -> dict[str, Any] | None:
        row = cls._one(rows)
        if row is not None and row.get("id") != canonical_id:
            raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        return row

    def health_check(self) -> str:
        try:
            state = self._client.health_check()
        except CatalystClientFailure as error:
            raise translate_catalyst_failure(error) from error
        if not isinstance(state, dict) or state.get("status") != "offline_ok":
            raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        return "ok"

    def schema_version(self) -> int:
        row = self._one(self._gateway.read(CatalystQueryName.SCHEMA_VERSION, {}))
        return 0 if row is None else int(row["version"])

    def find_active_user_by_username(self, username: str) -> dict[str, Any] | None:
        row = self._one(self._gateway.read(CatalystQueryName.ACTIVE_USER_BY_USERNAME, {"username": username}))
        return row if row is None or row["active"] else None

    def find_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        return self._one(self._gateway.read(CatalystQueryName.USER_BY_ID, {"id": user_id}))

    def list_source_systems(self) -> list[dict[str, Any]]:
        rows = self._gateway.read(CatalystQueryName.SOURCE_SYSTEM_LIST, {"limit": 50})
        return sorted(rows, key=lambda row: (str(row["priority"]), str(row["id"])))

    def find_source_system(self, source_id: str) -> dict[str, Any] | None:
        return self._one(self._gateway.read(CatalystQueryName.SOURCE_SYSTEM_BY_ID, {"id": source_id}))

    def find_case_360_case(self, case_id: str) -> dict[str, Any] | None:
        return self._exact(self._gateway.read(CatalystQueryName.CASE_BY_ID, {"id": case_id}), case_id)

    @staticmethod
    def _scoped_rows(rows: list[dict[str, Any]], scope_field: str, scope_id: str, id_field: str, *, ordering: tuple[str, ...]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        for row in rows:
            if row.get(scope_field) != scope_id or row[id_field] in seen:
                raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
            seen.add(row[id_field])
        return sorted(rows, key=lambda row: tuple(str(row[field]) for field in ordering))

    def list_case_360_entities(self, case_id: str) -> list[dict[str, Any]]:
        rows = self._gateway.read(CatalystQueryName.CASE_360_ENTITIES, {"case_id": case_id})
        allowed_types = {"PERSON", "PHONE", "DEVICE", "VEHICLE", "LOCATION"}
        rows = self._scoped_rows(rows, "case_id", case_id, "edge_id", ordering=("edge_id",))
        if any(row["target_type"] not in allowed_types for row in rows):
            raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        # SQLite omits dangling entity edges whose fixed display value is NULL.
        return [{key: value for key, value in row.items() if key != "case_id"} for row in rows if row["value"] is not None]

    def list_case_360_evidence(self, case_id: str) -> list[dict[str, Any]]:
        rows = self._gateway.read(CatalystQueryName.CASE_360_EVIDENCE, {"case_id": case_id})
        return self._scoped_rows(rows, "case_id", case_id, "id", ordering=("id",))

    def list_case_360_documents(self, case_id: str) -> list[dict[str, Any]]:
        return []

    def list_case_360_exhibits(self, case_id: str, include_blob: bool = False) -> list[dict[str, Any]]:
        return []

    def find_case_exhibit(self, exhibit_id: str) -> dict[str, Any] | None:
        return None

    def list_case_person_statements(self, case_id: str) -> list[dict[str, Any]]:
        return []

    def list_exhibit_custody_events(self, exhibit_id: str) -> list[dict[str, Any]]:
        return []

    def list_case_360_forensics(self, case_id: str) -> list[dict[str, Any]]:
        rows = self._gateway.read(CatalystQueryName.CASE_360_FORENSICS, {"case_id": case_id})
        return self._scoped_rows(rows, "case_id", case_id, "id", ordering=("id",))

    def list_case_360_trust_issues(self, case_id: str) -> list[dict[str, Any]]:
        rows = self._gateway.read(CatalystQueryName.CASE_360_TRUST_ISSUES, {"case_id": case_id})
        return self._scoped_rows(rows, "case_id", case_id, "id", ordering=("id",))

    def find_case_dna_case(self, case_id: str) -> dict[str, Any] | None:
        return self.find_case_360_case(case_id)

    def find_evidence_graph_case(self, request) -> dict[str, Any] | None:
        if not isinstance(request, EvidenceGraphRequest):
            raise ApiError("CATALYST_INVALID_PARAMETERS", "Catalyst query parameters are invalid.", 400, False)
        return self.find_case_360_case(request.case_id)

    @staticmethod
    def _intelligence_edges(rows: list[dict[str, Any]], case_id: str, *, relationship_types: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
        allowed_nodes = {"PERSON", "PHONE", "DEVICE", "VEHICLE", "LOCATION"}
        seen: set[str] = set()
        for row in rows:
            if (row["id"] in seen or row["source_type"] != "CASE" or row["source_id"] != case_id
                    or row["target_type"] not in allowed_nodes or not row["target_id"] or not row["source_record_id"]
                    or (relationship_types is not None and row["relationship_type"] not in relationship_types)):
                raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
            seen.add(row["id"])
        return sorted(rows, key=lambda row: str(row["id"]))

    def list_case_dna_edges(self, case_id: str, request: CaseDnaRequest) -> list[dict[str, Any]]:
        if not isinstance(request, CaseDnaRequest) or case_id not in {request.left_case_id, request.right_case_id}:
            raise ApiError("CATALYST_INVALID_PARAMETERS", "Catalyst query parameters are invalid.", 400, False)
        rows = self._gateway.read(CatalystQueryName.CASE_DNA_EDGES, {"case_id": case_id, "source_system_ids": request.source_system_ids})
        return self._intelligence_edges(rows, case_id)

    def list_evidence_graph_edges(self, request: EvidenceGraphRequest) -> list[dict[str, Any]]:
        if not isinstance(request, EvidenceGraphRequest):
            raise ApiError("CATALYST_INVALID_PARAMETERS", "Catalyst query parameters are invalid.", 400, False)
        rows = self._gateway.read(CatalystQueryName.EVIDENCE_GRAPH_EDGES, {"case_id": request.case_id, "source_system_ids": request.source_system_ids, "relationship_types": request.relationship_types, "edge_limit": request.edge_limit})
        if len(rows) > request.edge_limit:
            raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        return self._intelligence_edges(rows, request.case_id, relationship_types=request.relationship_types)

    def list_assurance_trust_issues(self, case_id: str | None = None) -> list[dict[str, Any]]:
        if case_id is not None and (not isinstance(case_id, str) or not case_id):
            raise ApiError("CATALYST_INVALID_PARAMETERS", "Catalyst query parameters are invalid.", 400, False)
        query = CatalystQueryName.ASSURANCE_TRUST_ISSUES if case_id is None else CatalystQueryName.ASSURANCE_TRUST_ISSUES_BY_CASE
        rows = self._gateway.read(query, {} if case_id is None else {"case_id": case_id})
        seen: set[str] = set()
        for row in rows:
            if row["id"] in seen or (case_id is not None and row["case_id"] != case_id):
                raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
            seen.add(row["id"])
        return sorted(rows, key=lambda row: str(row["id"]))

    @staticmethod
    def _report_rows(rows: list[dict[str, Any]], *, scope_field: str | None = None, scope_id: str | None = None) -> list[dict[str, Any]]:
        seen: set[str] = set()
        for row in rows:
            if row["id"] in seen or (scope_field is not None and row.get(scope_field) != scope_id):
                raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
            seen.add(row["id"])
        return sorted(sorted(rows, key=lambda row: str(row["id"])), key=lambda row: str(row["updated_at"]), reverse=True)

    def find_report(self, report_id: str) -> dict[str, Any] | None:
        return self._exact(self._gateway.read(CatalystQueryName.REPORT_BY_ID, {"id": report_id}), report_id)

    def list_reports_owned_by(self, user_id: str, limit: int, offset: int) -> list[dict[str, Any]]:
        rows = self._gateway.read(CatalystQueryName.REPORTS_BY_OWNER, {"user_id": user_id, "limit": limit, "offset": offset})
        return self._report_rows(rows, scope_field="owner_user_id", scope_id=user_id)

    def list_reports_assigned_to(self, reviewer_id: str, limit: int, offset: int) -> list[dict[str, Any]]:
        rows = self._gateway.read(CatalystQueryName.REPORTS_BY_REVIEWER, {"user_id": reviewer_id, "limit": limit, "offset": offset})
        return self._report_rows(rows, scope_field="assigned_reviewer_id", scope_id=reviewer_id)

    def find_eligible_supervisor(self, username: str) -> dict[str, Any] | None:
        row = self._one(self._gateway.read(CatalystQueryName.ELIGIBLE_SUPERVISOR_BY_USERNAME, {"username": username}))
        if row is not None and (row["username"] != username or row["role"] != "SUPERVISOR"):
            raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        return row

    def list_eligible_supervisors(self) -> list[dict[str, Any]]:
        rows = self._gateway.read(CatalystQueryName.ELIGIBLE_SUPERVISORS, {})
        seen: set[str] = set()
        for row in rows:
            key = row.get("id", row["username"])
            if key in seen or row["role"] != "SUPERVISOR":
                raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
            seen.add(key)
        return sorted(rows, key=lambda row: str(row["username"]))

    @staticmethod
    def _version_rows(rows: list[dict[str, Any]], report_id: str) -> list[dict[str, Any]]:
        seen: set[int] = set()
        for row in rows:
            if row["report_id"] != report_id or row["version_number"] <= 0 or row["version_number"] in seen:
                raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
            seen.add(row["version_number"])
        return sorted(rows, key=lambda row: row["version_number"], reverse=True)

    def find_report_version(self, report_id: str, version_number: int) -> dict[str, Any] | None:
        if isinstance(version_number, bool) or not isinstance(version_number, int) or version_number <= 0:
            raise ApiError("CATALYST_INVALID_PARAMETERS", "Catalyst query parameters are invalid.", 400, False)
        row = self._one(self._gateway.read(CatalystQueryName.REPORT_VERSION_BY_NUMBER, {"report_id": report_id, "version_number": version_number}))
        if row is not None:
            self._version_rows([row], report_id)
            if row["version_number"] != version_number:
                raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        return row

    def find_current_report_version(self, report_id: str) -> dict[str, Any] | None:
        row = self._one(self._gateway.read(CatalystQueryName.CURRENT_REPORT_VERSION, {"report_id": report_id}))
        return self._version_rows([row], report_id)[0] if row is not None else None

    def list_report_versions(self, report_id: str) -> list[dict[str, Any]]:
        return self._version_rows(self._gateway.read(CatalystQueryName.REPORT_VERSIONS, {"report_id": report_id}), report_id)

    def list_report_review_history(self, report_id: str) -> list[dict[str, Any]]:
        rows = self._gateway.read(CatalystQueryName.REPORT_REVIEW_HISTORY, {"report_id": report_id})
        for row in rows:
            if row["version_number"] <= 0:
                raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        return sorted(rows, key=lambda row: (str(row["created_at"]), str(row["username"]), str(row["decision"])))

    def find_source_passport_record(self, source_record_id: str) -> dict[str, Any] | None:
        return self._exact(self._gateway.read(CatalystQueryName.SOURCE_PASSPORT_RECORD, {"id": source_record_id}), source_record_id)

    def list_source_transformations(self, source_record_id: str) -> list[dict[str, Any]]:
        rows = self._gateway.read(CatalystQueryName.SOURCE_TRANSFORMATIONS, {"source_record_id": source_record_id})
        return sorted(rows, key=lambda row: (str(row["occurred_at"]), str(row["operation"])))

    def find_investigation(self, investigation_id: str) -> dict[str, Any] | None:
        return self._one(self._gateway.read(CatalystQueryName.INVESTIGATION_BY_ID, {"id": investigation_id}))

    def list_investigations_for_user(self, user_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int)):
            raise ApiError("CATALYST_INVALID_PARAMETERS", "Catalyst query parameters are invalid.", 400, False)
        bounded_limit = 50 if limit is None else max(1, min(limit, 50))
        rows = self._gateway.read(CatalystQueryName.INVESTIGATIONS_BY_OWNER, {"user_id": user_id, "limit": bounded_limit})
        if any(row["user_id"] != user_id for row in rows):
            raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        return sorted(sorted(rows, key=lambda row: str(row["id"])), key=lambda row: str(row["updated_at"]), reverse=True)

    def find_investigation_message(self, investigation_id: str, message_id: str) -> dict[str, Any] | None:
        return self._one(self._gateway.read(CatalystQueryName.QUERY_HISTORY_BY_ID, {"id": message_id, "investigation_id": investigation_id}))

    def list_investigation_messages(self, investigation_id: str) -> list[dict[str, Any]]:
        rows = self._gateway.read(CatalystQueryName.QUERY_HISTORY_BY_INVESTIGATION, {"investigation_id": investigation_id, "limit": 50})
        return sorted(rows, key=lambda row: (str(row["created_at"]), str(row["id"])))

    def search_case_candidates(self, filters: CaseSearchFilter) -> list[dict[str, Any]]:
        if not isinstance(filters, CaseSearchFilter):
            raise ApiError("CATALYST_INVALID_PARAMETERS", "Catalyst query parameters are invalid.", 400, False)
        if sum(bool(value) for value in (filters.phone, filters.imei, filters.vehicle_registration)) > 1:
            raise ApiError("CATALYST_QUERY_UNSUPPORTED", "This Catalyst query is not supported.", 400, False)
        parameters = {
            "offence": filters.offence or None, "status": filters.status or None, "date_from": filters.date_from or None,
            "date_to": filters.date_to or None, "case_identifier": filters.case_identifier or None, "location": filters.location or None,
            "phone": filters.phone or None, "imei": filters.imei or None, "vehicle_registration": filters.vehicle_registration or None,
            "source_system_ids": filters.source_system_ids or None, "limit": filters.limit, "offset": filters.offset,
        }
        rows = self._gateway.read(CatalystQueryName.SEARCH_CASE_CANDIDATES, parameters)
        if len(rows) > filters.limit:
            raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        seen: set[str] = set()
        for row in rows:
            if row["id"] in seen or not self._matches_search_filter(row, filters):
                raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
            seen.add(row["id"])
        return sorted(sorted(rows, key=lambda row: str(row["id"])), key=lambda row: str(row["incident_at"]), reverse=True)

    @staticmethod
    def _matches_search_filter(row: dict[str, Any], filters: CaseSearchFilter) -> bool:
        if filters.case_identifier and filters.case_identifier not in {row["id"], row["fir_number"], row["crime_number"]}:
            return False
        if filters.offence and row["offence"] != filters.offence:
            return False
        if filters.status and row["status"] != filters.status:
            return False
        incident_date = str(row["incident_at"])[:10]
        if filters.date_from and incident_date < filters.date_from:
            return False
        if filters.date_to and incident_date > filters.date_to:
            return False
        if filters.location and filters.location != "JAYANAGAR" and filters.location.lower() not in {str(row["station_id"]).lower(), str(row["district_id"]).lower()}:
            return False
        return not filters.source_system_ids or row["source_system_id"] in filters.source_system_ids

    def list_discovery_candidates(self, request: DiscoveryRequest) -> list[dict[str, Any]]:
        if not isinstance(request, DiscoveryRequest):
            raise ApiError("CATALYST_INVALID_PARAMETERS", "Catalyst query parameters are invalid.", 400, False)
        rows = self._gateway.read(CatalystQueryName.DISCOVERY_CANDIDATES, {
            "seed_case_ids": request.seed_case_ids, "source_system_ids": request.source_system_ids,
            "limit": request.limit, "offset": request.offset,
        })
        if len(rows) > request.limit:
            raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        for row in rows:
            if (row["base_case_id"] not in request.seed_case_ids or row["candidate_id"] != row["id"]
                    or row["candidate_id"] == row["base_case_id"] or row["source_system_id"] not in request.source_system_ids):
                raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        return sorted(sorted(rows, key=lambda row: str(row["id"])), key=lambda row: str(row["incident_at"]), reverse=True)

    def list_relationship_edges(self, request: RelationshipPathRequest) -> list[dict[str, Any]]:
        if not isinstance(request, RelationshipPathRequest):
            raise ApiError("CATALYST_INVALID_PARAMETERS", "Catalyst query parameters are invalid.", 400, False)
        rows = self._gateway.read(CatalystQueryName.RELATIONSHIP_EDGES, {
            "relationship_types": request.relationship_types, "source_system_ids": request.source_system_ids,
            "edge_limit": request.edge_limit,
        })
        if len(rows) > request.edge_limit:
            raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        seen: set[str] = set()
        for row in rows:
            if (row["id"] in seen or row["relationship_type"] not in request.relationship_types
                    or row["source_system_id"] not in request.source_system_ids
                    or row["source_type"] not in {"CASE", "DEVICE", "PHONE", "VEHICLE"}
                    or row["target_type"] not in {"CASE", "DEVICE", "PHONE", "VEHICLE"}
                    or not row["source_id"] or not row["target_id"]):
                raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
            seen.add(row["id"])
        return sorted(rows, key=lambda row: str(row["id"]))

    def transaction_capability(self) -> Capability:
        return Capability("persistence_transactions", CapabilityState.UNAVAILABLE, "Offline read-only Catalyst adapter has no transaction support.")

    def schema_version_capability(self) -> Capability:
        return Capability("schema_bootstrap", CapabilityState.UNAVAILABLE, "Catalyst schema verification and bootstrap are unavailable.")

    def capability(self) -> Capability:
        return Capability("catalyst_readonly_contract", CapabilityState.AVAILABLE, "Offline fake-client read contract is available; live transport is unavailable.")

    def close(self) -> None:
        self._client.close()


def _unsupported_method(name: str):
    def method(self, *args, **kwargs):
        return self._unsupported(name)
    method.__name__ = name
    return method


# The base repository has many deliberately unsupported lifecycle methods.  A
# generated explicit failure implementation keeps this narrow adapter
# structurally compatible without silently returning fake data or duplicating
# dozens of identical one-line methods.
for _method_name in Repository.__abstractmethods__:
    if _method_name not in CatalystReadOnlyRepository.__dict__:
        setattr(CatalystReadOnlyRepository, _method_name, _unsupported_method(_method_name))
update_abstractmethods(CatalystReadOnlyRepository)
