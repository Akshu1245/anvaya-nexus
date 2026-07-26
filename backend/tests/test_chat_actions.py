"""Chat action router and conversation / cluster endpoints."""
from backend.anvaya.services.chat_actions import resolve_chat_action
from backend.anvaya.services.conversation_pdf import conversation_pdf
from backend.anvaya.services.generator import generate
from backend.anvaya.services.network_clusters import candidate_network_clusters


def _login(client):
    return client.post("/api/auth/login", json={
        "username": "investigator.demo",
        "password": client.application.config["DEMO_PASSWORD"],
    })


def _investigation(client):
    _login(client)
    response = client.post("/api/investigations", json={
        "title": "Chat action test",
        "purpose": "Active Case Investigation",
        "selected_sources": ["CCTNS_REPLICA"],
    })
    return response.get_json()["data"]


def test_chat_actions_resolve_complete_details_and_pdf_phrases():
    assert resolve_chat_action("complete details for SYN-CASE-0001")["action"] == "OPEN_CASE_360"
    assert resolve_chat_action("send me PDF", {"active_case_id": "SYN-CASE-0002"})["action"] == "DOWNLOAD_PDF"
    assert resolve_chat_action("पीडीएफ भेजो", {"case_id": "SYN-CASE-0003"})["action"] == "DOWNLOAD_PDF"
    assert resolve_chat_action("ಪೂರ್ಣ ವಿವರ", {"active_case_id": "SYN-CASE-0001"})["action"] == "OPEN_CASE_360"
    assert resolve_chat_action("export this chat")["action"] == "CONVERSATION_PDF"
    assert resolve_chat_action("show network clusters for SYN-CASE-0001")["action"] == "NETWORK_CLUSTERS"
    assert resolve_chat_action("send me PDF")["action"] == "NEED_CASE_FOR_PDF"


def test_chat_action_api_and_conversation_pdf(client, app):
    generate(app.extensions["repository"], app.config, "test")
    investigation = _investigation(client)
    action = client.post(
        f"/api/investigations/{investigation['id']}/chat/action",
        json={"query": "complete details SYN-CASE-0001", "context": {}},
    )
    assert action.status_code == 200
    assert action.get_json()["data"]["action"] == "OPEN_CASE_360"
    pdf = client.post(
        f"/api/investigations/{investigation['id']}/conversation.pdf",
        json={"turns": [{"role": "user", "text": "hello", "kind": "text", "created_at": "2026-01-01T00:00:00Z"}]},
    )
    assert pdf.status_code == 200
    assert pdf.headers["Content-Type"].startswith("application/pdf")
    assert pdf.data[:4] == b"%PDF"


def test_network_clusters_endpoint(client, app):
    generate(app.extensions["repository"], app.config, "test")
    investigation = _investigation(client)
    response = client.get(f"/api/investigations/{investigation['id']}/cases/SYN-CASE-0001/network-clusters")
    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["seed_case_id"] == "SYN-CASE-0001"
    assert "clusters" in payload
    assert "not a social graph" in " ".join(payload["methodology"]["limitations"]).lower() or "stored" in payload["methodology"]["method"].lower()


def test_conversation_pdf_renderer_contains_watermark():
    blob = conversation_pdf(
        [{"role": "assistant", "text": "Synthetic reply", "kind": "text", "created_at": "2026-01-01T00:00:00Z"}],
        "Demo investigation",
        "SYN-INV-1",
    )
    assert blob.startswith(b"%PDF")
    assert len(blob) > 200


def test_conversation_pdf_uses_summary_when_text_missing():
    blob = conversation_pdf(
        [{"role": "assistant", "summary": "Summary-only turn", "kind": "text", "created_at": "2026-01-01T00:00:00Z"}],
        "Demo investigation",
        "SYN-INV-1",
    )
    assert blob.startswith(b"%PDF")
    assert len(blob) > 200
    text_preferred = conversation_pdf(
        [{"role": "assistant", "text": "Full text body", "summary": "Should not replace text", "kind": "text"}],
        "Demo investigation",
        "SYN-INV-1",
    )
    assert text_preferred.startswith(b"%PDF") and len(text_preferred) > 200


def test_candidate_clusters_service_uses_related_facts(app):
    repo = app.extensions["repository"]
    generate(repo, app.config, "test")
    user = repo.find_active_user_by_username("investigator.demo")
    result = candidate_network_clusters(repo, user, "Active Case Investigation", "SYN-CASE-0001", ["CCTNS_REPLICA"])
    assert result["seed_case_id"] == "SYN-CASE-0001"
    assert isinstance(result["clusters"], list)
