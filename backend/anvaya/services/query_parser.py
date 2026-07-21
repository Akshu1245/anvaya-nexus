from __future__ import annotations
import re
from datetime import date,timedelta
from backend.anvaya.api.errors import ApiError
from backend.anvaya.schemas.query import QueryFilters,QueryPlan

OFFENCES={"chain snatching":"CHAIN_SNATCHING","chain-snatching":"CHAIN_SNATCHING","ಸರ ಕಳವು":"CHAIN_SNATCHING","ಸರಗಳ್ಳತನ":"CHAIN_SNATCHING","housebreaking":"HOUSEBREAKING","ಮನೆ ಕಳ್ಳತನ":"HOUSEBREAKING","vehicle theft":"VEHICLE_THEFT"}
STATUS={"unresolved":"UNRESOLVED","ಬಗೆಹರಿಯದ":"UNRESOLVED","pending":"UNRESOLVED","resolved":"RESOLVED","ಬಗೆಹರಿದ":"RESOLVED"}
INTENTS={"verify":"VERIFY","ಪರಿಶೀಲಿಸಿ":"VERIFY","report":"REPORT","ವರದಿ":"REPORT","find":"SEARCH","show maadi":"SEARCH","show":"SEARCH","ತೋರಿಸಿ":"SEARCH","similar cases":"DISCOVER","similar":"DISCOVER","ಸಮಾನ":"DISCOVER"}
PROTECTED=re.compile(r"(?:SYN-FIR-[A-Z0-9-]+|SYN-IMEI-[0-9]+|SYN-PHONE-[0-9]+|SYN-REG-[0-9]+|\b[0-9]{10,15}\b)",re.I)
MALICIOUS=re.compile(r"\b(select|insert|update|delete|drop|alter|union|pragma|zcql)\b|--|;",re.I)

def guard_query_text(text:str)->None:
    if not text.strip():raise ApiError("QUERY_REQUIRED","Enter a query.",400,False)
    if MALICIOUS.search(text):raise ApiError("UNSAFE_QUERY","Database expressions are not allowed.",400,False)

def extract_protected_tokens(text:str)->list[str]:
    return PROTECTED.findall(text)

def apply_protected_tokens(plan:QueryPlan,protected:list[str])->QueryPlan:
    tokens=list(dict.fromkeys([*protected,*plan.protected_tokens]))
    filters=plan.filters.model_copy()
    for token in protected:
        upper=token.upper()
        if "FIR" in upper:filters.case_identifier=token
        elif "IMEI" in upper or len(re.sub(r"\D","",token))==15:filters.imei=token
        elif "PHONE" in upper or len(re.sub(r"\D","",token))==10:filters.phone=token
        elif "REG" in upper:filters.vehicle_registration=token
    return plan.model_copy(update={"filters":filters,"protected_tokens":tokens})

def parse_query(text,sources,today=None):
    guard_query_text(text)
    protected=extract_protected_tokens(text);normalized=text.lower();intent="SEARCH"
    for key,value in INTENTS.items():
        if key in normalized:intent=value;break
    offence=next((v for k,v in OFFENCES.items() if k in normalized),None);status=next((v for k,v in STATUS.items() if k in normalized),None)
    location=None
    for candidate in ("jayanagar","ಜಯನಗರ","synthetic sector","syn-stn-01","syn-dst-01"):
        if candidate in normalized:location="JAYANAGAR" if "jaya" in candidate or "ಜಯ" in candidate else candidate.upper();break
    current=today or date.today();date_from=date_to=None
    if "last three months" in normalized or "ಕಳೆದ ಮೂರು ತಿಂಗಳು" in normalized or "three months alli" in normalized:date_to=current;date_from=current-timedelta(days=90)
    filters=QueryFilters(offence=offence,location=location,date_from=date_from,date_to=date_to,status=status)
    for token in protected:
        upper=token.upper()
        if "FIR" in upper:filters.case_identifier=token
        elif "IMEI" in upper or len(re.sub(r"\D","",token))==15:filters.imei=token
        elif "PHONE" in upper or len(re.sub(r"\D","",token))==10:filters.phone=token
        elif "REG" in upper:filters.vehicle_registration=token
    uncertain=[]
    if not offence:uncertain.append("offence")
    if not location:uncertain.append("location")
    return QueryPlan(intent=intent,filters=filters,selected_sources=sources,result_limit=25,confidence=max(0.4,1-len(uncertain)*0.2),uncertain_fields=uncertain,protected_tokens=protected,requires_confirmation=bool(uncertain))
