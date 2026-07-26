from datetime import date
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator

class QueryFilters(BaseModel):
    model_config=ConfigDict(extra="forbid")
    offence:str|None=None;location:str|None=None;date_from:date|None=None;date_to:date|None=None
    status:str|None=None;case_identifier:str|None=None;phone:str|None=None;imei:str|None=None;vehicle_registration:str|None=None
    person_name:str|None=Field(default=None,min_length=1,max_length=80)
    person_role:Literal['COMPLAINANT','VICTIM','ACCUSED','WITNESS']|None=None
    act_id:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    act_code:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    section_id:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    section_code:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    case_category:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    gravity_offence:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    crime_major_head:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    crime_minor_head:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    canonical_case_status:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    arrest_event_type:Literal['ARREST','SURRENDER']|None=None
    chargesheet_report_type:Literal['A_CHARGESHEET','B_FALSE','C_UNDETECTED']|None=None
    has_arrest_event:bool|None=None
    has_chargesheet:bool|None=None
    state:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    district:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    police_unit:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    registering_officer:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    court:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    crime_number:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    case_number:str|None=Field(default=None,min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    registration_date_from:date|None=None
    registration_date_to:date|None=None

    @field_validator('person_name')
    @classmethod
    def validate_person_name(cls,value):
        if value is not None and any(token in value for token in ('%','_')):
            raise ValueError('Person name cannot include wildcard characters')
        return value.strip() if value is not None else value

class QueryPlan(BaseModel):
    model_config=ConfigDict(extra="forbid")
    intent:Literal["SEARCH","DISCOVER","VERIFY","REPORT"]
    filters:QueryFilters=Field(default_factory=QueryFilters)
    selected_sources:list[str]=Field(min_length=1,max_length=4)
    result_limit:int=Field(default=25,ge=1,le=25)
    confidence:float=Field(ge=0,le=1)
    uncertain_fields:list[str]=Field(default_factory=list)
    protected_tokens:list[str]=Field(default_factory=list)
    requires_confirmation:bool=False
