from dataclasses import asdict,dataclass

PURPOSES=("Active Case Investigation","Entity Verification","Pattern Research","Supervisor Review","Procedural Review")
P0_SOURCES=("CCTNS_REPLICA","FORENSICS_REPLICA","VEHICLE_REPLICA","CONTEXT_FIXTURE")
ROLE_PURPOSES={
 "INVESTIGATOR":{"Active Case Investigation","Entity Verification","Pattern Research","Procedural Review"},
 "CRIME_ANALYST":{"Entity Verification","Pattern Research","Procedural Review"},
 "SUPERVISOR":{"Supervisor Review"},
}
ROLE_SOURCES={"INVESTIGATOR":set(P0_SOURCES),"CRIME_ANALYST":set(P0_SOURCES),"SUPERVISOR":set()}

@dataclass
class PolicyDecision:
 allowed:bool;denial_code:str|None;explanation:str;masking_level:str;permitted_sources:list[str];row_limit:int;metadata:dict
 def dict(self):return asdict(self)

def evaluate(user,purpose,sources,operation,max_rows=25,record_station=None,record_district=None):
    try:role=user["role"]
    except (TypeError,KeyError,IndexError):role=None
    if role not in ROLE_PURPOSES:return PolicyDecision(False,"INVALID_ROLE_CONTEXT","Role context is missing or invalid.","NONE",[],0,{"operation":operation})
    if purpose not in PURPOSES:return PolicyDecision(False,"INVALID_PURPOSE","Purpose is not approved.","NONE",[],0,{"role":role,"operation":operation})
    if purpose not in ROLE_PURPOSES[role]:return PolicyDecision(False,"PURPOSE_DENIED","Purpose is incompatible with this role.","NONE",[],0,{"role":role,"purpose":purpose,"operation":operation})
    if role=="SUPERVISOR" and operation!="REVIEW":return PolicyDecision(False,"OPERATION_DENIED","Supervisor Review does not grant investigation search powers.","NONE",[],0,{"role":role,"operation":operation})
    permitted=ROLE_SOURCES[role];requested=list(dict.fromkeys(sources or ()))
    invalid=[s for s in requested if s not in permitted]
    if invalid:return PolicyDecision(False,"SOURCE_DENIED","One or more sources are unavailable or not permitted.","NONE",sorted(permitted),0,{"role":role,"denied_sources":invalid})
    masking="NONE"
    if role=="CRIME_ANALYST":masking="ANALYST"
    elif role=="SUPERVISOR":masking="REVIEW"
    elif record_district and record_district!=user["assigned_district"]:masking="EXTERNAL"
    elif record_station and record_station!=user["assigned_station"]:masking="DISTRICT"
    returned_sources=sorted(permitted) if operation in {"SOURCE_LIST","SOURCE_CONTROL"} else requested
    return PolicyDecision(True,None,"Allowed by prototype policy.",masking,returned_sources,min(max_rows,25),{"role":role,"purpose":purpose,"operation":operation})
