from __future__ import annotations

import html
import json
import uuid
from datetime import datetime, timezone

from backend.anvaya.api.errors import ApiError


PRIMARY_SECTIONS = (
    "Cover", "Investigation Summary", "Purpose and Scope", "Selected Sources", "FIR Search Criteria",
    "Retrieved FIR Cases", "FIR Header and Incident Summary", "People and Roles", "Acts and Sections",
    "Classification", "FIR Organisation and Court", "Arrest and Surrender Timeline",
    "Chargesheet and Final Report", "Evidence", "Timeline", "Related Cases and Matching Reasons",
    "FIR Relationship Graph", "FIR Record Assurance", "Sources and Provenance", "Source Limitations",
    "Jurisdiction and Masking Notes", "Audit Reference", "Reviewer Notes", "Disclaimer",
)
LEGACY_SECTIONS = ("Search Criteria", "Retrieved Cases", "Candidate Relationships", "Case DNA Comparisons", "Evidence Graph Summary", "Record Assurance Findings", "Hypothesis Challenge", "Action Impact Preview", "VERIFY Findings", "Provenance", "Data Quality", "Provenance Appendix")
SECTIONS = PRIMARY_SECTIONS + LEGACY_SECTIONS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _report(repo, report_id):
    report = repo.find_report(report_id)
    if not report:
        raise ApiError("REPORT_NOT_FOUND", "Report was not found.", 404)
    return report


def render(repo, report, sections, notes, user):
    investigation = repo.find_investigation(report["investigation_id"])
    if not investigation:
        raise ApiError("INVESTIGATION_NOT_FOUND", "Investigation was not found.", 404)
    selected_source_ids = json.loads(investigation["selected_sources_json"])
    sources = [source for source in repo.list_source_systems() if source["id"] in selected_source_ids]
    safe_notes = html.escape(notes)
    blocks = []
    for name in sections:
        if name == "Cover":
            body = f"<p>Report ID: {report['id']} · Status: {report['status']} · Generated: {_now()}</p><p>Author role: {html.escape(user['role'])}</p>"
        elif name == "Investigation Summary":
            body = f"<p>{html.escape(investigation['title'])} · {html.escape(investigation['purpose'])}</p>"
        elif name == "Selected Sources":
            body = "<ul>" + "".join(f"<li><code>{html.escape(source['id'])}</code> · {html.escape(source['name'])}: {source['status']}</li>" for source in sources) + "</ul>"
        elif name in {"FIR Relationship Graph", "Related Cases and Matching Reasons"}:
            body = "<p>Structured factual relationship summary only. A relationship does not imply guilt, identity, risk, or recommendation.</p>"
        elif name == "FIR Record Assurance":
            body = "<p>Deterministic Record Assurance findings use the current rule version and never alter FIR records automatically.</p>"
        elif name in {"Sources and Provenance", "Source Limitations"}:
            references = ", ".join(f"<code>{html.escape(source['id'])}</code>" for source in sources) or "No selected source reference"
            body = f"<p>Authorised synthetic source references: {references}. Stale or unavailable sources remain explicit limitations.</p>"
        elif name == "Reviewer Notes":
            body = f"<p class='note'>{safe_notes}</p>"
        elif name == "Disclaimer":
            body = "<p>SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE. Candidate-support only; no identity, guilt, risk, or operational conclusion.</p>"
        elif name == "Jurisdiction and Masking Notes":
            body = "<p>Current policy and masking are re-evaluated before generation. Source limitations and unavailable data remain visible.</p>"
        else:
            body = "<p>Source-backed section available through the authorised investigation record. No invented narrative is generated.</p>"
        blocks.append(f"<section><h2>{html.escape(name)}</h2>{body}</section>")
    toc = "<nav class='toc'><strong>Contents</strong><ol>" + "".join(f"<li>{html.escape(name)}</li>" for name in sections) + "</ol></nav>"
    return "<!doctype html><html><head><meta charset='utf-8'><title>ANVAYA report</title><style>body{font-family:system-ui;margin:2rem;color:#111;background:#fff;line-height:1.45}header{border-bottom:2px solid #111;padding-bottom:1rem}section{break-inside:avoid;border-bottom:1px solid #ddd;padding:1rem 0}.note{white-space:pre-wrap}.toc{background:#f8fafc;padding:1rem}@media print{body{margin:1.5cm;background:#fff;color:#000}section{page-break-inside:avoid}.toc{background:#fff}button,nav[aria-label='application']{display:none}}</style></head><body><header><strong>ANVAYA · SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE</strong><p><strong>Human review required.</strong> This report is decision support and must be reviewed by an authorised person.</p><h1>" + html.escape(report["title"]) + "</h1></header>" + toc + "".join(blocks) + "</body></html>"


def _sections(payload):
    values = payload.get("sections", PRIMARY_SECTIONS)
    if not isinstance(values, list):
        raise ApiError("REPORT_SECTIONS_INVALID", "Report sections must be a list.", 400)
    selected = list(dict.fromkeys(value for value in values if value in SECTIONS))
    if not selected:
        raise ApiError("REPORT_SECTIONS_REQUIRED", "Select at least one report section.", 400)
    return selected


def _plain_text(value, field, maximum):
    text = str(value or "").strip()
    if not text or len(text) > maximum or "<" in text or ">" in text:
        raise ApiError("REPORT_INPUT_INVALID", f"{field} is invalid.", 400)
    return text


def create(repo, user, payload):
    investigation_id = payload.get("investigation_id")
    investigation = repo.find_investigation(investigation_id) if investigation_id else None
    if not investigation or investigation.get("user_id") != user["id"]:
        user_invs = repo.list_investigations_for_user(user["id"])
        if user_invs:
            investigation = user_invs[0]
            investigation_id = investigation["id"]
        else:
            investigation_id = "INV-" + uuid.uuid4().hex[:8].upper()
            now_ts = _now()
            investigation = {
                "id": investigation_id,
                "user_id": user["id"],
                "title": "General Case Investigation",
                "purpose": "Active Crime Investigation & Dossier Generation",
                "selected_sources_json": json.dumps(["CCTNS_REPLICA"]),
                "assigned_station": user.get("assigned_station", "Bengaluru Central"),
                "status": "ACTIVE",
                "created_at": now_ts,
                "updated_at": now_ts,
            }
            repo.create_investigation(investigation)

    report_id = "SYN-RPT-" + uuid.uuid4().hex[:12].upper()
    now = _now()
    sections = _sections(payload)
    notes = str(payload.get("notes", ""))
    if len(notes) > 2000 or "<" in notes or ">" in notes: raise ApiError("REPORT_INPUT_INVALID", "Notes are invalid.", 400)
    report = {"id": report_id, "investigation_id": investigation_id, "owner_user_id": user["id"], "title": _plain_text(payload.get("title", "ANVAYA report"), "Report title", 160), "status": "DRAFT", "current_version": 1, "created_at": now, "updated_at": now}
    document = render(repo, report, sections, notes, user)
    version_id = report_id + "-V1"
    version = {"id": version_id, "version_number": 1, "status": "DRAFT", "sections_json": json.dumps(sections), "notes": notes, "html": document, "created_by": user["id"], "created_at": now, "immutable": 0}
    repo.create_report_with_initial_version(report, version)
    return {"report_id": report_id, "version_id": version_id, "html": document, "status": "DRAFT"}


def submit(repo, user, report_id):
    report = _report(repo, report_id)
    if report["owner_user_id"] != user["id"]:
        raise ApiError("REPORT_DENIED", "Report access is denied.", 403)
    if report["status"] != "DRAFT":
        raise ApiError("INVALID_REPORT_TRANSITION", "This report cannot be submitted from its current status.", 409)
    repo.submit_report_version(report_id, report["current_version"], _now())
    return {"report_id": report_id, "status": "IN_REVIEW"}


def update(repo, user, report_id, payload):
    report = _report(repo, report_id)
    if report["owner_user_id"] != user["id"] or report["status"] != "DRAFT":
        raise ApiError("REPORT_IMMUTABLE", "Only an owned draft can be edited.", 409)
    sections = _sections(payload)
    notes = str(payload.get("notes", ""))
    if len(notes) > 2000 or "<" in notes or ">" in notes: raise ApiError("REPORT_INPUT_INVALID", "Notes are invalid.", 400)
    document = render(repo, report, sections, notes, user)
    title = _plain_text(payload.get("title", report["title"]), "Report title", 160)
    repo.update_report_draft(report_id, report["current_version"], title, json.dumps(sections), notes, document, _now())
    return {"report_id": report_id, "status": "DRAFT", "html": document}


def new_version(repo, user, report_id):
    report = _report(repo, report_id)
    if report["owner_user_id"] != user["id"] or report["status"] != "CHANGES_REQUESTED":
        raise ApiError("VERSION_DENIED", "A new version is available only after requested changes.", 409)
    previous = repo.find_report_version(report_id, report["current_version"])
    if not previous:
        raise ApiError("VERSION_NOT_FOUND", "Report version was not found.", 404)
    version_number = report["current_version"] + 1
    version = {"id": f"{report_id}-V{version_number}", "version_number": version_number, "sections_json": previous["sections_json"], "notes": previous["notes"], "html": previous["html"], "created_by": user["id"], "created_at": _now()}
    repo.create_next_report_draft(report_id, report["current_version"], version, _now())
    return {"report_id": report_id, "version_id": version["id"], "status": "DRAFT"}


def review(repo, user, report_id, decision, note):
    report = _report(repo, report_id)
    if user["role"] != "SUPERVISOR" or report["owner_user_id"] == user["id"] or report["assigned_reviewer_id"] != user["id"] or report["status"] != "IN_REVIEW":
        raise ApiError("REVIEW_DENIED", "Review access is denied.", 403)
    if decision not in {"APPROVED", "REJECTED", "CHANGES_REQUESTED"}:
        raise ApiError("INVALID_DECISION", "Invalid review decision.", 400)
    if decision in {"REJECTED", "CHANGES_REQUESTED"} and not note.strip():
        raise ApiError("REVIEW_NOTE_REQUIRED", "A review comment is required.", 400)
    review_record = {"id": "SYN-REV-" + uuid.uuid4().hex[:12].upper(), "reviewer_user_id": user["id"], "decision": decision, "note": note, "created_at": _now()}
    repo.create_report_review_decision(report_id, report["current_version"], review_record, _now())
    return {"report_id": report_id, "status": decision}


def allowed(repo, user, report):
    return report["owner_user_id"] == user["id"] or (user["role"] == "SUPERVISOR" and report["assigned_reviewer_id"] == user["id"])


def listing(repo, user, limit=25, offset=0):
    if user["role"] == "SUPERVISOR":
        return repo.list_reports_assigned_to(user["id"], limit, offset)
    return repo.list_reports_owned_by(user["id"], limit, offset)


def assign(repo, user, report_id, reviewer):
    report = _report(repo, report_id)
    if report["owner_user_id"] != user["id"] or report["status"] not in {"DRAFT", "IN_REVIEW", "CHANGES_REQUESTED"}:
        raise ApiError("ASSIGNMENT_DENIED", "Reviewer assignment is denied.", 403)
    candidate = repo.find_eligible_supervisor(reviewer)
    if not candidate:
        raise ApiError("INVALID_REVIEWER", "Reviewer must be an eligible synthetic Supervisor.", 400)
    if candidate["id"] == user["id"]:
        raise ApiError("ASSIGNMENT_DENIED", "A report owner cannot self-assign a review.", 403)
    repo.assign_report_reviewer(report_id, candidate["id"], _now())
    return {"report_id": report_id, "reviewer": candidate["username"]}
