from backend.anvaya.services.masking import mask_case
from backend.anvaya.services.policy import evaluate
from backend.anvaya.repositories.search_filter import CaseSearchFilter
from backend.anvaya.api.errors import ApiError


def _has_meaningful_filter(filters):
    return any(value is not None and value != "" for key, value in vars(filters).items() if key not in {"source_system_ids", "limit", "offset"})


def _case_summary(repository, row, source_system_ids):
    """Bounded display enrichment; policy and masking remain with the caller."""
    case = repository.find_case_360_case(row["id"]) or row
    classifications = repository.find_case_classifications(row["id"]) or {}
    organisation = repository.find_case_organisation(row["id"]) or {}
    people = repository.list_case_people(row["id"], source_system_ids=source_system_ids)
    legal = repository.list_case_legal_sections(row["id"], source_system_ids=source_system_ids)
    arrests = repository.list_case_arrest_surrender_events(row["id"], source_system_ids=source_system_ids)
    chargesheets = repository.list_case_chargesheets(row["id"], source_system_ids=source_system_ids)
    complainant = next((person["display_name"] for person in people if person["role"] == "COMPLAINANT"), None)
    return {
        "case_id": row["id"], "id": row["id"], "crime_number": case.get("crime_number"),
        "case_number": case.get("case_number"), "fir_number": case.get("fir_number"),
        "registered_at": case.get("registered_at"), "incident_from_at": case.get("incident_from_at") or case.get("incident_at"),
        "incident_to_at": case.get("incident_to_at"), "legacy_status": case.get("status"),
        "canonical_status": classifications.get("canonical_status"), "category": classifications.get("category"),
        "gravity": classifications.get("gravity"), "crime_major_head": classifications.get("crime_major_head"),
        "crime_minor_head": classifications.get("crime_minor_head"), "police_unit": {"id": organisation.get("police_unit_id"), "name": organisation.get("unit_name"), "code": organisation.get("unit_code")},
        "district": {"id": organisation.get("canonical_district_id"), "name": organisation.get("district_name"), "code": organisation.get("district_code")},
        "court": {"id": organisation.get("court_id"), "name": organisation.get("court_name"), "code": organisation.get("court_code")},
        "primary_complainant": complainant, "accused_count": sum(person["role"] == "ACCUSED" for person in people),
        "acts_sections": [{"act_code": item["act_code"], "section_code": item["section_code"]} for item in legal],
        "has_arrest_surrender": bool(arrests), "has_chargesheet": bool(chargesheets),
        "source_system_id": row["source_system_id"], "freshness_state": row["freshness_state"],
        "reliability_role": row["reliability_role"], "access_class": row["access_class"],
        "source_record_references": [row["source_record_id"]], "station_id": row["station_id"], "district_id": row["district_id"],
    }

def search_cases(repository,user,purpose,plan):
    f=plan.filters
    filters=CaseSearchFilter(offence=f.offence,status=f.status,date_from=f.date_from.isoformat() if f.date_from else None,date_to=f.date_to.isoformat() if f.date_to else None,case_identifier=f.case_identifier,location=f.location,phone=f.phone,imei=f.imei,vehicle_registration=f.vehicle_registration,person_name=f.person_name,person_role=f.person_role,act_id=f.act_id,act_code=f.act_code,section_id=f.section_id,section_code=f.section_code,case_category=f.case_category,gravity_offence=f.gravity_offence,crime_major_head=f.crime_major_head,crime_minor_head=f.crime_minor_head,canonical_case_status=f.canonical_case_status,arrest_event_type=f.arrest_event_type,chargesheet_report_type=f.chargesheet_report_type,has_arrest_event=f.has_arrest_event,has_chargesheet=f.has_chargesheet,state=f.state,district=f.district,police_unit=f.police_unit,registering_officer=f.registering_officer,court=f.court,crime_number=f.crime_number,case_number=f.case_number,registration_date_from=f.registration_date_from.isoformat() if f.registration_date_from else None,registration_date_to=f.registration_date_to.isoformat() if f.registration_date_to else None,source_system_ids=tuple(plan.selected_sources),limit=min(plan.result_limit,25))
    if not _has_meaningful_filter(filters):
        raise ApiError("SEARCH_FILTER_REQUIRED", "Provide at least one FIR search filter.", 400, False)
    for lower, upper in ((filters.date_from, filters.date_to), (filters.registration_date_from, filters.registration_date_to)):
        if lower and upper and lower > upper:
            raise ApiError("INVALID_DATE_RANGE", "A search date range is invalid.", 400, False)
    rows=repository.search_case_candidates(filters);results=[]
    for row in rows:
        decision=evaluate(user,purpose,plan.selected_sources,"SEARCH",plan.result_limit,row["station_id"],row["district_id"])
        record={**_case_summary(repository,row,filters.source_system_ids),"offence":row["offence"],"incident_at":row["incident_at"],"status":row["status"],"person_name":None,"phone":None,"imei":None,"vehicle_registration":None,"address":None,"sensitive_evidence_reference":None,"jurisdiction_state":"assigned_station" if row["station_id"]==user["assigned_station"] else ("assigned_district" if row["district_id"]==user["assigned_district"] else "external"),"match_reasons":[x for x in ("offence" if f.offence else None,"status" if f.status else None,"date" if f.date_from else None,"identifier" if any((f.case_identifier,f.crime_number,f.case_number)) else None,"person_role" if f.person_role else ("person" if f.person_name else None),"act" if any((f.act_id,f.act_code)) else None,"section" if any((f.section_id,f.section_code)) else None,"classification" if any((f.case_category,f.gravity_offence,f.crime_major_head,f.crime_minor_head,f.canonical_case_status)) else None,"organisation" if any((f.state,f.district,f.police_unit,f.registering_officer,f.court)) else None,"arrest_event" if any((f.arrest_event_type,f.has_arrest_event is not None)) else None,"chargesheet" if any((f.chargesheet_report_type,f.has_chargesheet is not None)) else None) if x]}
        results.append(mask_case(record,decision.masking_level))
    return results
