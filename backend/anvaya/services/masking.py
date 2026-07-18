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
    result["masking"]={"applied":bool(masked),"level":level,"fields":masked};return result
