def _partial(value):
    parts=str(value).split();return " ".join((p[:1]+"***") for p in parts) if parts else "***"
def _last(value,n=4):return "***"+str(value)[-n:]

def mask_case(record,level):
    result=dict(record);masked=[]
    if level!="NONE":
        for field in ("person_name",):
            if result.get(field):result[field]=_partial(result[field]);masked.append(field)
        for field in ("phone","imei","vehicle_registration"):
            if result.get(field):result[field]=_last(result[field],2 if level=="EXTERNAL" else 4);masked.append(field)
        if result.get("address"):result["address"]=result.get("locality") or result.get("district_id");masked.append("address")
        if result.get("sensitive_evidence_reference"):result["sensitive_evidence_reference"]={"category":result.get("evidence_type"),"status":result.get("evidence_status")};masked.append("sensitive_evidence_reference")
        if result.get("brief_facts"):result["brief_facts"]="Masked by policy.";masked.append("brief_facts")
        if result.get("body_text"):result["body_text"]="Masked by policy.";masked.append("body_text")
        if result.get("statement_body"):result["statement_body"]="Masked by policy.";masked.append("statement_body")
        if result.get("latitude") is not None or result.get("longitude") is not None:
            result["latitude"]=None;result["longitude"]=None;masked.extend(("latitude","longitude"))
        if result.get("caption"):result["caption"]="Masked by policy.";masked.append("caption")
        if result.get("content_blob") is not None:result["content_blob"]=None;result["thumbnail_masked"]=True;masked.append("content_blob")
        if level=="EXTERNAL" and result.get("sha256") and "content_blob" not in masked:
            # EXTERNAL policy withholds exhibit thumbnails even when blob is not present in the payload.
            result["thumbnail_masked"]=True;masked.append("thumbnail")
        if result.get("filename") and level=="EXTERNAL":result["filename"]="***masked***";masked.append("filename")
    result["masking"]={"applied":bool(masked),"level":level,"fields":masked};return result
