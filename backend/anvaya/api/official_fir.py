from __future__ import annotations

from flask import Blueprint, current_app, g, request

from backend.anvaya.api.errors import ApiError
from backend.anvaya.api.m3 import _ok, protected
from backend.anvaya.services.audit import audit
from backend.anvaya.services.official_fir import (official_case_360, official_fir_counts, search_official_cases,
    identity_suggestions, investigation_brief, investigation_report_preview, record_assurance, related_cases_with_evidence,
    relationship_graph, review_identity_suggestion)

official_fir_blueprint = Blueprint("official_fir", __name__, url_prefix="/api/fir")


@official_fir_blueprint.get("/readiness")
@protected
def readiness():
    counts = official_fir_counts(current_app.extensions["repository"])
    return _ok({"schema_version": 5, "synthetic_only": True, "counts": counts,
                "ready": counts["fir_case_details"] > 0})


@official_fir_blueprint.get("/cases")
@protected
def cases_search():
    role = request.args.get("role")
    if role and role not in {"COMPLAINANT", "VICTIM", "ACCUSED"}:
        raise ApiError("INVALID_PERSON_ROLE", "Role must be COMPLAINANT, VICTIM or ACCUSED.", 400, False)
    try:
        limit = min(max(int(request.args.get("limit", 25)), 1), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError as exc:
        raise ApiError("INVALID_PAGINATION", "Limit and offset must be integers.", 400, False) from exc
    results = search_official_cases(
        current_app.extensions["repository"], crime_no=request.args.get("crime_no"),
        case_no=request.args.get("case_no"), person_name=request.args.get("person_name"), role=role,
        act=request.args.get("act"), section=request.args.get("section"), unit_id=request.args.get("unit_id"),
        court_id=request.args.get("court_id"), status=request.args.get("status"), category=request.args.get("category"),
        gravity=request.args.get("gravity"), major_head=request.args.get("major_head"),
        minor_head=request.args.get("minor_head"), q=request.args.get("q"), limit=limit, offset=offset,
    )
    audit(current_app.extensions["repository"], "OFFICIAL_FIR_SEARCH", "SUCCESS", g.user["id"], g.request_id,
          {"result_count": len(results), "synthetic_only": True})
    return _ok({"results": results, "result_count": len(results), "limit": limit, "offset": offset,
                "synthetic_only": True})


@official_fir_blueprint.get("/cases/<case_id>/360")
@protected
def case_360(case_id: str):
    result = official_case_360(current_app.extensions["repository"], case_id)
    audit(current_app.extensions["repository"], "OFFICIAL_FIR_CASE_360_OPENED", "SUCCESS", g.user["id"],
          g.request_id, {"case_id": case_id})
    return _ok(result, warnings=["Synthetic FIR fixture only. No real police or citizen data is present."])

@official_fir_blueprint.get("/cases/<case_id>/brief")
@protected
def brief(case_id: str):
    result=investigation_brief(current_app.extensions["repository"],case_id,g.user["id"])
    audit(current_app.extensions["repository"],"GROUNDED_INVESTIGATION_BRIEF","SUCCESS",g.user["id"],g.request_id,{"case_id":case_id,"synthetic_only":True})
    return _ok(result)

@official_fir_blueprint.get("/cases/<case_id>/related-cases")
@protected
def related_cases(case_id: str):
    return _ok({"results":related_cases_with_evidence(current_app.extensions["repository"],case_id),"human_review_required":True})

@official_fir_blueprint.get("/cases/<case_id>/identity-suggestions")
@protected
def identities(case_id: str):
    return _ok({"suggestions":identity_suggestions(current_app.extensions["repository"],case_id),"automatic_merge":False})

@official_fir_blueprint.post("/cases/<case_id>/identity-suggestions/review")
@protected
def review_identity(case_id: str):
    p=request.get_json(silent=True) or {}
    result=review_identity_suggestion(current_app.extensions["repository"],case_id,str(p.get("related_case_id","")),str(p.get("person_id","")),str(p.get("decision","")),g.user["id"],str(p.get("note","")))
    audit(current_app.extensions["repository"],"IDENTITY_LINK_REVIEWED","SUCCESS",g.user["id"],g.request_id,{"case_id":case_id,"decision":result["status"]})
    return _ok(result)

@official_fir_blueprint.get("/cases/<case_id>/assurance")
@protected
def assurance(case_id: str):
    return _ok({"findings":record_assurance(current_app.extensions["repository"],case_id),"non_mutating":True})

@official_fir_blueprint.get("/cases/<case_id>/graph")
@protected
def graph(case_id: str):
    return _ok(relationship_graph(current_app.extensions["repository"],case_id))

@official_fir_blueprint.get("/cases/<case_id>/report-preview")
@protected
def report_preview(case_id: str):
    result=investigation_report_preview(current_app.extensions["repository"],case_id,g.user["id"])
    audit(current_app.extensions["repository"],"FIR_SOURCE_CITED_REPORT_PREVIEW","SUCCESS",g.user["id"],g.request_id,{"case_id":case_id})
    return _ok(result)
