from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal, Mapping, Sequence

from backend.anvaya.repositories.search_filter import CaseSearchFilter
from backend.anvaya.repositories.discovery_requests import DiscoveryRequest, RelationshipPathRequest
from backend.anvaya.repositories.intelligence_requests import CaseDnaRequest, EvidenceGraphRequest
from backend.anvaya.repositories.audit_requests import AuditEventFilter, AuditEventInput


class Repository(ABC):
    """Storage boundary implemented by SQLite now and Catalyst in M7."""

    @abstractmethod
    def health_check(self) -> Literal["ok"]:
        raise NotImplementedError

    @abstractmethod
    def schema_version(self) -> int:
        """Return the applied canonical schema version without exposing storage details."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def initialize(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def table_count(self, table: str) -> int:
        raise NotImplementedError

    # Authentication/session operations are deliberately narrow.  Application
    # services receive plain records and never compose storage queries.
    @abstractmethod
    def seed_predefined_users(self, users: Sequence[Mapping[str, Any]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_active_user_by_username(self, username: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def find_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def create_session(
        self,
        session_id: str,
        user_id: str,
        token_hash: str,
        created_at: str,
        expires_at: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_session_with_user(self, token_hash: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def revoke_session(self, session_id: str, revoked_at: str) -> None:
        raise NotImplementedError

    # Source registry and Data Readiness operations.  Dynamic SQL, table names,
    # and ordering are intentionally not part of this contract.
    @abstractmethod
    def upsert_source_systems(self, sources: Sequence[Mapping[str, Any]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_source_systems(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def find_source_system(self, source_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def source_external_ids(self, source_system_id: str) -> set[str]:
        raise NotImplementedError

    @abstractmethod
    def create_import_job(
        self, job: Mapping[str, Any], failures: Sequence[Mapping[str, Any]]
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_import_job(self, job_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_import_failures(self, job_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def commit_import_rows(
        self, job_id: str, imported_at: str, canonical_rows: Sequence[Mapping[str, Any]]
    ) -> None:
        raise NotImplementedError

    # Investigation lifecycle, selected-source snapshot, and saved query
    # history. Authorization remains in the calling service/API layer.
    @abstractmethod
    def create_investigation(self, investigation: Mapping[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_investigation(self, investigation_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_investigations_for_user(self, user_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def replace_investigation_sources(
        self, investigation_id: str, selected_sources_json: str, updated_at: str
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_investigation_message(self, message: Mapping[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_investigation_message(
        self, investigation_id: str, message_id: str
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_investigation_messages(self, investigation_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def confirm_investigation_message(
        self, investigation_id: str, message_id: str, query_plan_json: str
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def search_case_candidates(self, filters: CaseSearchFilter) -> list[dict[str, Any]]:
        """Return deterministically ordered, source-backed SEARCH candidates."""
        raise NotImplementedError

    @abstractmethod
    def list_related_case_facts(
        self, case_id: str, source_system_ids: Sequence[str], limit: int = 25
    ) -> list[dict[str, Any]]:
        """Return bounded, stored factual links for one trusted base case."""
        raise NotImplementedError

    @abstractmethod
    def list_discovery_candidates(self, request: DiscoveryRequest) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_relationship_edges(self, request: RelationshipPathRequest) -> list[dict[str, Any]]:
        raise NotImplementedError

    # Case 360 and Source Passport records. These are intentionally fixed
    # views of the currently exposed sections rather than generic entity APIs.
    @abstractmethod
    def find_case_360_case(self, case_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_case_360_entities(self, case_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_case_360_evidence(self, case_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_case_360_documents(self, case_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_case_360_exhibits(self, case_id: str, include_blob: bool = False) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def find_case_exhibit(self, exhibit_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_case_360_forensics(self, case_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_case_360_trust_issues(self, case_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    # FIR people are represented once and linked to cases through a fixed role
    # allowlist.  Services retain policy and masking decisions.
    @abstractmethod
    def find_person(self, person_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_case_person_roles(
        self, case_id: str, role: str | None = None, source_system_ids: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_case_people(
        self, case_id: str, source_system_ids: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def search_case_people_name(
        self, name: str, role: str | None, source_system_ids: Sequence[str], limit: int
    ) -> list[dict[str, Any]]:
        """Return bounded case-level matches for a trusted person-role name filter."""
        raise NotImplementedError

    @abstractmethod
    def list_case_person_statements(self, case_id: str) -> list[dict[str, Any]]:
        """Return recorded synthetic complaint/witness statements for one case."""
        raise NotImplementedError

    @abstractmethod
    def list_exhibit_custody_events(self, exhibit_id: str) -> list[dict[str, Any]]:
        """Return the ordered synthetic custody chain for one exhibit."""
        raise NotImplementedError

    # FIR legal and classification reads are fixed, ordered views.  Services
    # own policy, masking and validation explanations.
    @abstractmethod
    def find_legal_act(self, act_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def find_legal_section(self, section_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_legal_acts(self, active_only: bool = True) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_legal_sections(self, act_id: str | None = None, active_only: bool = True) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_case_legal_sections(
        self, case_id: str, source_system_ids: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def find_case_classifications(self, case_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_case_categories(self, active_only: bool = True) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_gravity_offences(self, active_only: bool = True) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_crime_heads(self, active_only: bool = True) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_crime_subheads(self, crime_head_id: str | None = None, active_only: bool = True) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_case_statuses(self, active_only: bool = True) -> list[dict[str, Any]]:
        raise NotImplementedError

    # FIR arrest/surrender and final-report reads are intentionally bounded
    # storage views. Services retain policy, masking, timeline, and wording.
    @abstractmethod
    def find_arrest_surrender_event(self, event_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_case_arrest_surrender_events(
        self, case_id: str, source_system_ids: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_arrest_event_accused(
        self, event_id: str, source_system_ids: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def find_chargesheet(self, chargesheet_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_case_chargesheets(
        self, case_id: str, source_system_ids: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    # FIR operational organisation reference reads. These are fixed catalog
    # views; services retain authorization and masking decisions.
    @abstractmethod
    def find_state(self, state_id: str) -> dict[str, Any] | None: raise NotImplementedError
    @abstractmethod
    def list_states(self, active_only: bool = True) -> list[dict[str, Any]]: raise NotImplementedError
    @abstractmethod
    def find_district(self, district_id: str) -> dict[str, Any] | None: raise NotImplementedError
    @abstractmethod
    def list_districts(self, state_id: str | None = None, active_only: bool = True) -> list[dict[str, Any]]: raise NotImplementedError
    @abstractmethod
    def find_police_unit(self, unit_id: str) -> dict[str, Any] | None: raise NotImplementedError
    @abstractmethod
    def list_police_units(self, district_id: str | None = None, active_only: bool = True) -> list[dict[str, Any]]: raise NotImplementedError
    @abstractmethod
    def find_police_employee(self, employee_id: str) -> dict[str, Any] | None: raise NotImplementedError
    @abstractmethod
    def list_police_employees(self, unit_id: str | None = None, active_only: bool = True) -> list[dict[str, Any]]: raise NotImplementedError
    @abstractmethod
    def find_court(self, court_id: str) -> dict[str, Any] | None: raise NotImplementedError
    @abstractmethod
    def list_courts(self, district_id: str | None = None, active_only: bool = True) -> list[dict[str, Any]]: raise NotImplementedError
    @abstractmethod
    def list_police_ranks(self, active_only: bool = True) -> list[dict[str, Any]]: raise NotImplementedError
    @abstractmethod
    def list_police_designations(self, active_only: bool = True) -> list[dict[str, Any]]: raise NotImplementedError
    @abstractmethod
    def list_police_unit_types(self, active_only: bool = True) -> list[dict[str, Any]]: raise NotImplementedError
    @abstractmethod
    def find_case_organisation(self, case_id: str) -> dict[str, Any] | None: raise NotImplementedError

    @abstractmethod
    def find_source_passport_record(self, source_record_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_source_transformations(self, source_record_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    # M5 intelligence reads use trusted, bounded inputs. Similarity, weights,
    # policy, and graph presentation remain in services.
    @abstractmethod
    def find_case_dna_case(self, case_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_case_dna_edges(self, case_id: str, request: CaseDnaRequest) -> list[dict[str, Any]]:
        raise NotImplementedError

    def list_modus_operandi_features(self) -> list[dict[str, Any]]:
        """Return stored MODUS_OPERANDI fixture features for descriptive co-occurrence."""
        raise NotImplementedError

    @abstractmethod
    def find_evidence_graph_case(self, request: EvidenceGraphRequest) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_evidence_graph_edges(self, request: EvidenceGraphRequest) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_assurance_trust_issues(self, case_id: str | None = None) -> list[dict[str, Any]]:
        """Return the fixed seeded/imported trust issues used by Record Assurance."""
        raise NotImplementedError

    @abstractmethod
    def upsert_trust_issue(self, issue: Mapping[str, Any]) -> dict[str, Any]:
        """Materialise one deterministic assurance finding without duplicating it."""
        raise NotImplementedError

    @abstractmethod
    def list_case_materialized_trust_issues(self, case_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def update_trust_issue_status(self, issue_id: str, status: str, note: str | None, actor_id: str, at: str) -> dict[str, Any] | None:
        raise NotImplementedError

    # Report lifecycle storage. Authorization and state transition validation
    # stay in services; these methods provide fixed, atomic persistence steps.
    @abstractmethod
    def create_report_with_initial_version(self, report: Mapping[str, Any], version: Mapping[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_report(self, report_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_reports_owned_by(self, user_id: str, limit: int, offset: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_reports_assigned_to(self, reviewer_id: str, limit: int, offset: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def find_eligible_supervisor(self, username: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_eligible_supervisors(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def assign_report_reviewer(self, report_id: str, reviewer_id: str, updated_at: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_report_version(self, report_id: str, version_number: int) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def find_current_report_version(self, report_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_report_versions(self, report_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def update_report_draft(self, report_id: str, version_number: int, title: str, sections_json: str, notes: str, html: str, updated_at: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def submit_report_version(self, report_id: str, version_number: int, updated_at: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_next_report_draft(self, report_id: str, previous_version: int, version: Mapping[str, Any], updated_at: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_report_review_decision(self, report_id: str, version_number: int, review: Mapping[str, Any], updated_at: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_report_review_history(self, report_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def append_audit_event(self, event: AuditEventInput) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_audit_events(self, filters: AuditEventFilter) -> list[dict[str, Any]]:
        raise NotImplementedError
