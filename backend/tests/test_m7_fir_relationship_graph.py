"""D-8 bounded, factual FIR Relationship Graph contract."""

from backend.anvaya.repositories.audit_requests import AuditEventFilter
from backend.anvaya.services.generator import generate
from backend.anvaya.services.investigation import fir_relationship_graph, fir_relationship_path


def _graph(app, case_id="SYN-CASE-0001"):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    user = repository.find_user_by_id("SYN-USR-INV")
    return repository, user, fir_relationship_graph(repository, user, "Active Case Investigation", case_id, ("CCTNS_REPLICA",))["graph"]


def test_fir_graph_contains_factual_dataset_nodes_edges_and_safe_provenance(app):
    _, _, graph = _graph(app)
    types = {node["type"] for node in graph["nodes"]}
    assert {"CASE", "PERSON", "ACT", "SECTION", "POLICE_UNIT", "POLICE_OFFICER", "COURT", "ARREST_EVENT", "CHARGESHEET"} <= types
    relationships = {edge["relationship_type"] for edge in graph["edges"]}
    assert {
        "CASE_HAS_COMPLAINANT", "CASE_HAS_VICTIM", "CASE_HAS_ACCUSED", "CASE_INVOKES_ACT",
        "CASE_INVOKES_SECTION", "SECTION_BELONGS_TO_ACT", "CASE_REGISTERED_AT_UNIT",
        "CASE_REGISTERED_BY_OFFICER", "CASE_HEARD_AT_COURT", "CASE_HAS_ARREST_EVENT",
        "ARREST_INVOLVES_ACCUSED", "CASE_HAS_CHARGESHEET",
    } <= relationships
    assert graph["node_count"] == len(graph["nodes"]) <= 75
    assert graph["edge_count"] == len(graph["edges"]) <= 150
    assert len({(node["type"], node["id"]) for node in graph["nodes"]}) == graph["node_count"]
    assert len({edge["id"] for edge in graph["edges"]}) == graph["edge_count"]
    assert all({"source_record_id", "source_system", "freshness", "access_class", "factual_basis"} <= set(edge) for edge in graph["edges"])
    assert "guilt" in graph["disclaimer"].lower()
    assert "payload" not in str(graph).lower() and "latitude" not in str(graph).lower()


def test_fir_graph_projects_related_case_reasons_without_case_dna_score(app):
    _, _, graph = _graph(app)
    projected = [edge for edge in graph["edges"] if edge["projected"]]
    assert projected
    assert {edge["relationship_type"] for edge in projected} <= {
        "CASE_SHARES_ACCUSED_WITH_CASE", "CASE_SHARES_COMPLAINANT_WITH_CASE",
        "CASE_SHARES_VICTIM_WITH_CASE", "CASE_SHARES_ACT_SECTION_WITH_CASE",
        "CASE_SHARES_UNIT_WITH_CASE", "CASE_SHARES_COURT_WITH_CASE",
        "CASE_SHARES_OFFICER_WITH_CASE",
    }
    assert all(edge["factual_basis"] for edge in projected)
    assert "score" not in str(graph).lower() and "probability" not in str(graph).lower()


def test_fir_graph_masks_external_people_and_keeps_path_bounded(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    user = repository.find_user_by_id("SYN-USR-INV")
    external = next(
        row["id"] for row in (repository.find_case_360_case(f"SYN-CASE-{number:04d}") for number in range(1, 31))
        if row["station_id"] != user["assigned_station"]
    )
    graph = fir_relationship_graph(repository, user, "Active Case Investigation", external, ("CCTNS_REPLICA",))["graph"]
    assert any(node["type"] == "PERSON" and node["masked"] for node in graph["nodes"])
    target = next(node["id"] for node in graph["nodes"] if node["type"] == "PERSON")
    path = fir_relationship_path(repository, user, "Active Case Investigation", external, target, ("CCTNS_REPLICA",), 3)
    assert path["hop_count"] <= 3
    assert path["path_nodes"][0] == external and path["path_nodes"][-1] == target
    absent = fir_relationship_path(repository, user, "Active Case Investigation", external, "SYN-NOT-A-NODE", ("CCTNS_REPLICA",), 3)
    assert absent["path_edges"] == [] and "No factual path" in absent["warning"]


def test_fir_graph_api_audits_and_returns_the_bounded_contract(client, app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    login = client.post("/api/auth/login", json={"username": "investigator.demo", "password": client.application.config["DEMO_PASSWORD"]})
    assert login.status_code == 200
    created = client.post("/api/investigations", json={"title": "FIR graph", "purpose": "Active Case Investigation", "selected_sources": ["CCTNS_REPLICA"]}).get_json()["data"]
    response = client.get(f"/api/investigations/{created['id']}/cases/SYN-CASE-0001/graph")
    assert response.status_code == 200
    assert response.get_json()["data"]["graph"]["base_case_id"] == "SYN-CASE-0001"
    target = response.get_json()["data"]["graph"]["nodes"][1]["id"]
    path = client.get(f"/api/investigations/{created['id']}/cases/SYN-CASE-0001/graph/path?to={target}")
    assert path.status_code == 200 and path.get_json()["data"]["hop_count"] <= 3
    events = repository.list_audit_events(AuditEventFilter(actor_user_id="SYN-USR-INV", limit=25))
    assert {"FIR_GRAPH_VIEWED", "FIR_RELATIONSHIP_PATH_VIEWED"} <= {event["event_type"] for event in events}
