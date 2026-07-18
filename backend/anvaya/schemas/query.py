from datetime import date
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field

class QueryFilters(BaseModel):
    model_config=ConfigDict(extra="forbid")
    offence:str|None=None;location:str|None=None;date_from:date|None=None;date_to:date|None=None
    status:str|None=None;case_identifier:str|None=None;phone:str|None=None;imei:str|None=None;vehicle_registration:str|None=None

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
