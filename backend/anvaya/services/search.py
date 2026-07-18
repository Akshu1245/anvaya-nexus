from backend.anvaya.services.masking import mask_case
from backend.anvaya.services.policy import evaluate

def search_cases(repository,user,purpose,plan):
    clauses=[];params=[];f=plan.filters
    if f.offence:clauses.append("c.offence=?");params.append(f.offence)
    if f.status:clauses.append("c.status=?");params.append(f.status)
    if f.date_from:clauses.append("date(c.incident_at)>=?");params.append(f.date_from.isoformat())
    if f.date_to:clauses.append("date(c.incident_at)<=?");params.append(f.date_to.isoformat())
    if f.case_identifier:clauses.append("(c.id=? OR c.fir_number=? OR c.crime_number=?)");params.extend([f.case_identifier]*3)
    if f.location and f.location!="JAYANAGAR":clauses.append("(lower(c.station_id)=lower(?) OR lower(c.district_id)=lower(?))");params.extend([f.location,f.location])
    for value,column in ((f.imei,"d.synthetic_imei"),(f.phone,"p.synthetic_number"),(f.vehicle_registration,"v.synthetic_registration")):
        if value:
            table={"d.synthetic_imei":"devices d","p.synthetic_number":"phones p","v.synthetic_registration":"vehicles v"}[column]
            etype={"d.synthetic_imei":"DEVICE","p.synthetic_number":"PHONE","v.synthetic_registration":"VEHICLE"}[column]
            clauses.append(f"EXISTS (SELECT 1 FROM entity_edges e JOIN {table} ON e.target_id={column.split('.')[0]}.id WHERE e.source_type='CASE' AND e.source_id=c.id AND e.target_type='{etype}' AND {column}=?)");params.append(value)
    sql="SELECT c.*,sr.freshness_state FROM cases c JOIN source_records sr ON sr.id=c.source_record_id"+(" WHERE "+" AND ".join(clauses) if clauses else "")+" ORDER BY c.incident_at DESC LIMIT ?"
    params.append(min(plan.result_limit,25));rows=repository.connection.execute(sql,params).fetchall();results=[]
    for row in rows:
        decision=evaluate(user,purpose,plan.selected_sources,"SEARCH",plan.result_limit,row["station_id"],row["district_id"])
        record={"id":row["id"],"fir_number":row["fir_number"],"crime_number":row["crime_number"],"offence":row["offence"],"incident_at":row["incident_at"],"status":row["status"],"station_id":row["station_id"],"district_id":row["district_id"],"person_name":None,"phone":None,"imei":None,"vehicle_registration":None,"address":None,"sensitive_evidence_reference":None,"source_record_references":[row["source_record_id"]],"freshness_state":row["freshness_state"],"jurisdiction_state":"assigned_station" if row["station_id"]==user["assigned_station"] else ("assigned_district" if row["district_id"]==user["assigned_district"] else "external"),"match_reasons":[x for x in ("offence" if f.offence else None,"status" if f.status else None,"date" if f.date_from else None,"identifier" if any((f.case_identifier,f.phone,f.imei,f.vehicle_registration)) else None) if x]}
        results.append(mask_case(record,decision.masking_level))
    return results
