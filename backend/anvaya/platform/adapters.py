from __future__ import annotations

from dataclasses import dataclass

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.capabilities import Capability, CapabilityState
from backend.anvaya.services import auth as prototype_auth


class SQLiteRepositoryAdapter:
    backend_name = "sqlite"

    def __init__(self, repository):
        self.repository = repository

    def health_check(self) -> str:
        return self.repository.health_check()

    def transaction_capability(self) -> Capability:
        return Capability("persistence_transactions", CapabilityState.AVAILABLE, "SQLite local transactions are available.")

    def schema_version_capability(self) -> Capability:
        return Capability("schema_bootstrap", CapabilityState.AVAILABLE, "SQLite migrations are available locally.")

    def close(self) -> None:
        self.repository.close()


class PrototypeAuthenticationAdapter:
    backend_name = "prototype"

    def __init__(self, repository):
        self.repository = repository

    def resolve_identity(self, token, request_id=None):
        return prototype_auth.current_user(self.repository, token, request_id)

    def login_session(self, username, password, ttl_minutes, request_id):
        return prototype_auth.login(self.repository, username, password, ttl_minutes, request_id)

    def revoke_session(self, token, request_id):
        prototype_auth.revoke(self.repository, token, request_id)

    def capability(self) -> Capability:
        return Capability("authentication", CapabilityState.AVAILABLE, "Prototype server-side sessions are available.")


class LocalArtifactStorageAdapter:
    backend_name = "local"

    def __init__(self):
        self._artifacts: dict[str, str] = {}

    def store_report_html(self, artifact_id: str, html: str) -> str:
        self._artifacts[artifact_id] = html
        return artifact_id

    def retrieve_artifact(self, artifact_id: str) -> str:
        if artifact_id not in self._artifacts:
            raise ApiError("ARTIFACT_NOT_FOUND", "Artifact was not found.", 404, False)
        return self._artifacts[artifact_id]

    def delete_artifact(self, artifact_id: str) -> None:
        self._artifacts.pop(artifact_id, None)

    def capability(self) -> Capability:
        return Capability("artifact_storage", CapabilityState.AVAILABLE, "Local process artifact storage is available for compatibility only.")


class LocalSchemaBootstrapAdapter:
    backend_name = "sqlite"

    def __init__(self, repository):
        self.repository = repository

    def inspect_schema_state(self) -> dict[str, int]:
        return {"schema_version": self.repository.schema_version()}

    def bootstrap(self) -> None:
        self.repository.initialize()

    def seed_synthetic_demo_data(self) -> None:
        raise ApiError("EXPLICIT_SEED_REQUIRED", "Use the explicit local seed command.", 409, False)

    def capability(self) -> Capability:
        return Capability("schema_bootstrap", CapabilityState.AVAILABLE, "Local schema inspection and bootstrap are available.")


class _CatalystPlaceholder:
    backend_name = "catalyst"

    def _unsupported(self):
        raise ApiError("CATALYST_NOT_IMPLEMENTED", "Catalyst integration is not implemented in M7.1.", 503, False)


class CatalystRepositoryPlaceholder(_CatalystPlaceholder):
    def health_check(self): self._unsupported()
    def schema_version(self): self._unsupported()
    def seed_predefined_users(self, users): self._unsupported()
    def find_active_user_by_username(self, username): self._unsupported()
    def find_user_by_id(self, user_id): self._unsupported()
    def create_session(self, session_id, user_id, token_hash, created_at, expires_at): self._unsupported()
    def find_session_with_user(self, token_hash): self._unsupported()
    def revoke_session(self, session_id, revoked_at): self._unsupported()
    def upsert_source_systems(self, sources): self._unsupported()
    def list_source_systems(self): self._unsupported()
    def find_source_system(self, source_id): self._unsupported()
    def source_external_ids(self, source_system_id): self._unsupported()
    def create_import_job(self, job, failures): self._unsupported()
    def find_import_job(self, job_id): self._unsupported()
    def list_import_failures(self, job_id): self._unsupported()
    def commit_import_rows(self, job_id, imported_at, canonical_rows): self._unsupported()
    def create_investigation(self, investigation): self._unsupported()
    def find_investigation(self, investigation_id): self._unsupported()
    def list_investigations_for_user(self, user_id, limit=None): self._unsupported()
    def replace_investigation_sources(self, investigation_id, selected_sources_json, updated_at): self._unsupported()
    def create_investigation_message(self, message): self._unsupported()
    def find_investigation_message(self, investigation_id, message_id): self._unsupported()
    def list_investigation_messages(self, investigation_id): self._unsupported()
    def confirm_investigation_message(self, investigation_id, message_id, query_plan_json): self._unsupported()
    def search_case_candidates(self, filters): self._unsupported()
    def list_related_case_facts(self, case_id, source_system_ids, limit=25): self._unsupported()
    def list_discovery_candidates(self, request): self._unsupported()
    def list_relationship_edges(self, request): self._unsupported()
    def find_case_360_case(self, case_id): self._unsupported()
    def list_case_360_entities(self, case_id): self._unsupported()
    def list_case_360_evidence(self, case_id): self._unsupported()
    def list_case_360_forensics(self, case_id): self._unsupported()
    def list_case_360_trust_issues(self, case_id): self._unsupported()
    def find_person(self, person_id): self._unsupported()
    def list_case_person_roles(self, case_id, role=None, source_system_ids=None): self._unsupported()
    def list_case_people(self, case_id, source_system_ids=None): self._unsupported()
    def search_case_people_name(self, name, role, source_system_ids, limit): self._unsupported()
    def list_case_person_statements(self, case_id): self._unsupported()
    def list_exhibit_custody_events(self, exhibit_id): self._unsupported()
    def find_legal_act(self, act_id): self._unsupported()
    def find_legal_section(self, section_id): self._unsupported()
    def list_legal_acts(self, active_only=True): self._unsupported()
    def list_legal_sections(self, act_id=None, active_only=True): self._unsupported()
    def list_case_legal_sections(self, case_id, source_system_ids=None): self._unsupported()
    def find_case_classifications(self, case_id): self._unsupported()
    def list_case_categories(self, active_only=True): self._unsupported()
    def list_gravity_offences(self, active_only=True): self._unsupported()
    def list_crime_heads(self, active_only=True): self._unsupported()
    def list_crime_subheads(self, crime_head_id=None, active_only=True): self._unsupported()
    def list_case_statuses(self, active_only=True): self._unsupported()
    def find_arrest_surrender_event(self, event_id): self._unsupported()
    def list_case_arrest_surrender_events(self, case_id, source_system_ids=None): self._unsupported()
    def list_arrest_event_accused(self, event_id, source_system_ids=None): self._unsupported()
    def find_chargesheet(self, chargesheet_id): self._unsupported()
    def list_case_chargesheets(self, case_id, source_system_ids=None): self._unsupported()
    def find_state(self, state_id): self._unsupported()
    def list_states(self, active_only=True): self._unsupported()
    def find_district(self, district_id): self._unsupported()
    def list_districts(self, state_id=None, active_only=True): self._unsupported()
    def find_police_unit(self, unit_id): self._unsupported()
    def list_police_units(self, district_id=None, active_only=True): self._unsupported()
    def find_police_employee(self, employee_id): self._unsupported()
    def list_police_employees(self, unit_id=None, active_only=True): self._unsupported()
    def find_court(self, court_id): self._unsupported()
    def list_courts(self, district_id=None, active_only=True): self._unsupported()
    def list_police_ranks(self, active_only=True): self._unsupported()
    def list_police_designations(self, active_only=True): self._unsupported()
    def list_police_unit_types(self, active_only=True): self._unsupported()
    def find_case_organisation(self, case_id): self._unsupported()
    def find_source_passport_record(self, source_record_id): self._unsupported()
    def list_source_transformations(self, source_record_id): self._unsupported()
    def find_case_dna_case(self, case_id): self._unsupported()
    def list_case_dna_edges(self, case_id, request): self._unsupported()
    def find_evidence_graph_case(self, request): self._unsupported()
    def list_evidence_graph_edges(self, request): self._unsupported()
    def list_assurance_trust_issues(self, case_id=None): self._unsupported()
    def upsert_trust_issue(self, issue): self._unsupported()
    def list_case_materialized_trust_issues(self, case_id): self._unsupported()
    def update_trust_issue_status(self, issue_id, status, note, actor_id, at): self._unsupported()
    def create_report_with_initial_version(self, report, version): self._unsupported()
    def find_report(self, report_id): self._unsupported()
    def list_reports_owned_by(self, user_id, limit, offset): self._unsupported()
    def list_reports_assigned_to(self, reviewer_id, limit, offset): self._unsupported()
    def find_eligible_supervisor(self, username): self._unsupported()
    def list_eligible_supervisors(self): self._unsupported()
    def assign_report_reviewer(self, report_id, reviewer_id, updated_at): self._unsupported()
    def find_report_version(self, report_id, version_number): self._unsupported()
    def find_current_report_version(self, report_id): self._unsupported()
    def list_report_versions(self, report_id): self._unsupported()
    def update_report_draft(self, report_id, version_number, title, sections_json, notes, html, updated_at): self._unsupported()
    def submit_report_version(self, report_id, version_number, updated_at): self._unsupported()
    def create_next_report_draft(self, report_id, previous_version, version, updated_at): self._unsupported()
    def create_report_review_decision(self, report_id, version_number, review, updated_at): self._unsupported()
    def list_report_review_history(self, report_id): self._unsupported()
    def append_audit_event(self, event): self._unsupported()
    def list_audit_events(self, filters): self._unsupported()
    def transaction_capability(self): return Capability("persistence_transactions", CapabilityState.UNAVAILABLE, "Catalyst repository adapter is not implemented.")
    def schema_version_capability(self): return Capability("schema_bootstrap", CapabilityState.CONFIGURED, "Catalyst bootstrap is selected but not implemented.")
    def close(self): return None


class CatalystAuthenticationPlaceholder(_CatalystPlaceholder):
    def resolve_identity(self, token, request_id=None): self._unsupported()
    def login_session(self, username, password, ttl_minutes, request_id): self._unsupported()
    def revoke_session(self, token, request_id): self._unsupported()
    def capability(self): return Capability("authentication", CapabilityState.UNAVAILABLE, "Catalyst authentication adapter is not implemented.")


class CatalystArtifactStoragePlaceholder(_CatalystPlaceholder):
    def store_report_html(self, artifact_id, html): self._unsupported()
    def retrieve_artifact(self, artifact_id): self._unsupported()
    def delete_artifact(self, artifact_id): self._unsupported()
    def capability(self): return Capability("artifact_storage", CapabilityState.UNAVAILABLE, "Catalyst artifact storage adapter is not implemented.")


class CatalystSchemaBootstrapPlaceholder(_CatalystPlaceholder):
    def inspect_schema_state(self): return {"schema_state": "unavailable"}
    def bootstrap(self): self._unsupported()
    def seed_synthetic_demo_data(self): self._unsupported()
    def capability(self): return Capability("schema_bootstrap", CapabilityState.CONFIGURED, "Catalyst bootstrap requires explicit M7.2 implementation.")
