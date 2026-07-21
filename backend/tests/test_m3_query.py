from datetime import date
import pytest
from pydantic import ValidationError
from backend.anvaya.api.errors import ApiError
from backend.anvaya.schemas.query import QueryPlan
from backend.anvaya.services.query_parser import parse_query

def test_english_kannada_and_code_mixed_parsing():
    sources=["CCTNS_REPLICA"]
    assert parse_query("Find unresolved chain snatching at SYN-STN-01",sources).filters.offence=="CHAIN_SNATCHING"
    assert parse_query("ಬಗೆಹರಿಯದ ಸರಗಳ್ಳತನ ಜಯನಗರ ತೋರಿಸಿ",sources).filters.status=="UNRESOLVED"
    golden=parse_query("Last three months alli Jayanagar hatra similar unresolved chain-snatching cases show maadi.",sources,today=date(2026,7,11))
    assert golden.intent=="SEARCH" and golden.filters.location=="JAYANAGAR" and golden.filters.date_from==date(2026,4,12)
    assert parse_query("Find similar cases",sources).intent=="SEARCH"
    assert parse_query("similar cases",sources).intent=="DISCOVER"

@pytest.mark.parametrize("token,field",[("SYN-FIR-000001","case_identifier"),("SYN-IMEI-000000000001","imei"),("SYN-PHONE-000001","phone"),("SYN-REG-000001","vehicle_registration")])
def test_protected_identifiers_preserved(token,field):
    plan=parse_query(f"Find {token}",["CCTNS_REPLICA"]);assert token in plan.protected_tokens;assert getattr(plan.filters,field)==token

def test_ambiguity_requires_confirmation():
    plan=parse_query("show maadi recent records",["CCTNS_REPLICA"]);assert plan.requires_confirmation and {"offence","location"}<=set(plan.uncertain_fields)

@pytest.mark.parametrize("query",["SELECT * FROM cases","drop table cases;","ZCQL query"])
def test_database_language_rejected(query):
    with pytest.raises(ApiError) as exc:parse_query(query,["CCTNS_REPLICA"])
    assert exc.value.code=="UNSAFE_QUERY"

def test_unknown_intent_and_field_rejected():
    base={"intent":"UNKNOWN","filters":{},"selected_sources":["CCTNS_REPLICA"],"result_limit":25,"confidence":1,"uncertain_fields":[],"protected_tokens":[],"requires_confirmation":False}
    with pytest.raises(ValidationError):QueryPlan.model_validate(base)
    base["intent"]="SEARCH";base["raw_sql"]="select 1"
    with pytest.raises(ValidationError):QueryPlan.model_validate(base)
