from datetime import datetime, timedelta, timezone

from backend.anvaya.services.source_registry import freshness_state, list_sources


def test_source_registry_has_four_p0_and_two_unavailable_p1(app):
    sources=list_sources(app.extensions["repository"]); assert len(sources)==6
    assert len([s for s in sources if s["priority"]=="P0"])==4
    p1=[s for s in sources if s["priority"]=="P1"]
    assert {s["id"] for s in p1}=={"COURT_REPLICA","PROSECUTION_REPLICA"}
    assert all(s["status"]=="Unavailable" for s in p1)


def test_fresh_stale_unavailable_calculation():
    now=datetime(2026,7,11,tzinfo=timezone.utc)
    assert freshness_state((now-timedelta(hours=1)).isoformat(),2,True,now)=="Fresh"
    assert freshness_state((now-timedelta(hours=3)).isoformat(),2,True,now)=="Stale"
    assert freshness_state(None,2,False,now)=="Unavailable"


def test_source_registry_api(client):
    response=client.get("/api/sources"); assert response.status_code==200
    assert response.json["request_id"]
    assert {s["status"] for s in response.json["data"]}>={"Fresh","Unavailable"}


def test_ground_truth_is_not_exposed(client):
    assert client.get("/api/ground-truth").status_code==404
