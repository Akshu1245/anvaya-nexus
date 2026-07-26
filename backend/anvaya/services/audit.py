from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from backend.anvaya.api.errors import ApiError
from backend.anvaya.repositories.audit_requests import AUDIT_ROLES, AuditEventFilter, AuditEventInput


_UNSAFE_METADATA_KEYS = {"password", "token", "query_text", "full_value"}


def audit(repository, event_type, outcome, user_id=None, request_id=None, metadata=None):
    safe = {key: value for key, value in (metadata or {}).items() if key not in _UNSAFE_METADATA_KEYS}
    event = AuditEventInput(
        id=f"SYN-AUD-{uuid.uuid4().hex[:16]}", event_type=event_type, outcome=outcome,
        user_id=user_id, request_id=request_id, safe_metadata_json=json.dumps(safe, sort_keys=True),
        occurred_at=datetime.now(timezone.utc).isoformat(),
    )
    repository.append_audit_event(event)


def list_events(repository, user, values):
    try:
        limit = min(max(int(values.get("limit", 25)), 1), 50)
        offset = max(int(values.get("offset", 0)), 0)
    except (TypeError, ValueError) as error:
        raise ApiError("INVALID_AUDIT_PAGINATION", "Audit pagination is invalid.", 400) from error
    start, end = values.get("start"), values.get("end")
    for value in (start, end):
        if value:
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as error:
                raise ApiError("INVALID_AUDIT_DATE", "Audit dates must be ISO timestamps.", 400) from error
    if start and end and start > end:
        raise ApiError("INVALID_AUDIT_RANGE", "Audit start must be before end.", 400)
    actor_role = values.get("actor_role")
    if actor_role and actor_role not in AUDIT_ROLES:
        raise ApiError("INVALID_AUDIT_ROLE", "Audit role is invalid.", 400)
    investigation_id, report_id = values.get("investigation"), values.get("report")
    if investigation_id and not investigation_id.startswith("SYN-INV-"):
        raise ApiError("INVALID_AUDIT_REFERENCE", "Audit reference is invalid.", 400)
    if report_id and not report_id.startswith("SYN-RPT-"):
        raise ApiError("INVALID_AUDIT_REFERENCE", "Audit reference is invalid.", 400)
    filters = AuditEventFilter(
        actor_user_id=None if user["role"] == "SUPERVISOR" else user["id"], actor_role=actor_role,
        investigation_id=investigation_id, report_id=report_id, event_type=values.get("event_type"),
        outcome=values.get("outcome"), request_id=values.get("request_id"), start=start, end=end,
        limit=limit, offset=offset,
    )
    return repository.list_audit_events(filters), limit, offset
