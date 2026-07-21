"""Tests for LLM + voice services — all HTTP calls are mocked; real APIs are never called."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.anvaya import create_app
from backend.anvaya.services.generator import generate


PASSWORD = "ANVAYA-DEMO-ONLY-2026"


@pytest.fixture()
def ai_app():
    application = create_app("testing", {"AI_ASSIST_ENABLED": True, "OPENROUTER_API_KEY": "test-key", "OPENROUTER_MODEL": "test-model"})
    yield application
    application.extensions["repository"].close()


@pytest.fixture()
def voice_app():
    application = create_app("testing", {"VOICE_ENABLED": True, "SARVAM_API_KEY": "test-key"})
    yield application
    application.extensions["repository"].close()


def _login_and_create(client):
    client.post("/api/auth/login", json={"username": "investigator.demo", "password": PASSWORD})
    inv = client.post("/api/investigations", json={"title": "AI test", "purpose": "Active Case Investigation", "selected_sources": ["CCTNS_REPLICA"]})
    return inv.json["data"]["id"]


# ── Config / flags ─────────────────────────────────────────────────────────────

def test_flags_off_by_default(client):
    data = client.get("/api/health").json["data"]
    assert data["ai_assist_enabled"] is False
    assert data["voice_enabled"] is False


def test_ai_flag_requires_both_flag_and_key():
    app_no_key = create_app("testing", {"AI_ASSIST_ENABLED": True, "OPENROUTER_API_KEY": ""})
    with app_no_key.test_client() as c:
        assert c.get("/api/health").json["data"]["ai_assist_enabled"] is False
    app_no_key.extensions["repository"].close()


def test_voice_flag_requires_both_flag_and_key():
    app_no_key = create_app("testing", {"VOICE_ENABLED": True, "SARVAM_API_KEY": ""})
    with app_no_key.test_client() as c:
        assert c.get("/api/health").json["data"]["voice_enabled"] is False
    app_no_key.extensions["repository"].close()


def test_flags_on_when_key_and_flag_set(ai_app, voice_app):
    with ai_app.test_client() as c:
        assert c.get("/api/health").json["data"]["ai_assist_enabled"] is True
    with voice_app.test_client() as c:
        assert c.get("/api/health").json["data"]["voice_enabled"] is True


# ── LLM interpret fallback ─────────────────────────────────────────────────────

def test_malicious_query_still_blocked_with_ai_enabled(ai_app):
    with ai_app.test_client() as c:
        generate(ai_app.extensions["repository"], ai_app.config, "test")
        c.post("/api/auth/login", json={"username": "investigator.demo", "password": PASSWORD})
        iid = c.post("/api/investigations", json={"title": "t", "purpose": "Active Case Investigation", "selected_sources": ["CCTNS_REPLICA"]}).json["data"]["id"]
        resp = c.post(f"/api/investigations/{iid}/query/preview", json={"query": "SELECT * FROM cases"})
        assert resp.status_code == 400
        assert resp.json["code"] == "UNSAFE_QUERY"


def test_preview_falls_back_to_deterministic_when_llm_returns_none(ai_app):
    with patch("backend.anvaya.api.m3.llm_interpret", return_value=None):
        with ai_app.test_client() as c:
            generate(ai_app.extensions["repository"], ai_app.config, "test")
            iid = _login_and_create(c)
            resp = c.post(f"/api/investigations/{iid}/query/preview", json={"query": "Find chain snatching"})
            assert resp.status_code == 200
            assert resp.json["data"]["interpretation_engine"] == "deterministic"


def test_preview_uses_ai_engine_label_when_llm_succeeds(ai_app):
    from backend.anvaya.schemas.query import QueryFilters, QueryPlan
    fake_plan = QueryPlan(intent="SEARCH", filters=QueryFilters(offence="CHAIN_SNATCHING"), selected_sources=["CCTNS_REPLICA"], result_limit=25, confidence=0.9, uncertain_fields=[], protected_tokens=[], requires_confirmation=False)
    with patch("backend.anvaya.api.m3.llm_interpret", return_value=fake_plan):
        with ai_app.test_client() as c:
            generate(ai_app.extensions["repository"], ai_app.config, "test")
            iid = _login_and_create(c)
            resp = c.post(f"/api/investigations/{iid}/query/preview", json={"query": "Find chain snatching"})
            assert resp.status_code == 200
            assert resp.json["data"]["interpretation_engine"] == "ai_assisted"


def test_llm_plan_with_extra_fields_is_stripped(ai_app):
    from backend.anvaya.services.llm import _build_plan_from_payload
    payload = {"intent": "SEARCH", "filters": {"offence": "CHAIN_SNATCHING", "raw_sql": "DROP TABLE cases"}, "confidence": 0.8, "uncertain_fields": []}
    plan = _build_plan_from_payload(payload, ["CCTNS_REPLICA"])
    assert plan is not None
    assert not hasattr(plan.filters, "raw_sql")
    assert plan.filters.offence == "CHAIN_SNATCHING"


# ── LLM answer ─────────────────────────────────────────────────────────────────

def test_answer_endpoint_returns_templated_when_ai_disabled(client, app):
    generate(app.extensions["repository"], app.config, "test")
    iid = _login_and_create(client)
    plan = {"intent": "SEARCH", "filters": {"offence": "CHAIN_SNATCHING"}, "selected_sources": ["CCTNS_REPLICA"], "result_limit": 5, "confidence": 1.0, "uncertain_fields": [], "protected_tokens": [], "requires_confirmation": False}
    resp = client.post(f"/api/investigations/{iid}/answer", json={"plan": plan, "question": "Find chain snatching"})
    assert resp.status_code == 200
    data = resp.json["data"]
    assert "engine" in data and "grounded" in data and data["grounded"] is True


def test_llm_answer_strips_uncited_ids(ai_app):
    from backend.anvaya.schemas.query import QueryFilters, QueryPlan
    from backend.anvaya.services.llm import llm_answer
    plan = QueryPlan(intent="SEARCH", filters=QueryFilters(), selected_sources=["CCTNS_REPLICA"], result_limit=5, confidence=1.0, uncertain_fields=[], protected_tokens=[], requires_confirmation=False)
    records = [{"case_id": "CASE-1", "source_record_references": ["SRC-REAL-1"]}]
    fake_response = json.dumps({"answer": "Found chain snatching cases.", "cited_source_ids": ["SRC-REAL-1", "SRC-INVENTED-99"]})
    def mock_complete(_cfg, _msgs, **_kw):
        return fake_response
    with patch("backend.anvaya.services.llm._chat_completion", side_effect=mock_complete):
        result = llm_answer("question", records, plan, {"AI_ASSIST_ENABLED": True, "OPENROUTER_API_KEY": "k", "OPENROUTER_BASE": "http://x", "OPENROUTER_MODEL": "m", "OPENROUTER_TIMEOUT_SECONDS": 5})
    assert result is not None
    assert "SRC-INVENTED-99" not in result["cited_source_ids"]
    assert "SRC-REAL-1" in result["cited_source_ids"]
    assert result["engine"] == "ai_assisted"


def test_llm_answer_returns_none_on_network_failure(ai_app):
    from backend.anvaya.schemas.query import QueryFilters, QueryPlan
    from backend.anvaya.services.llm import llm_answer
    plan = QueryPlan(intent="SEARCH", filters=QueryFilters(), selected_sources=["CCTNS_REPLICA"], result_limit=5, confidence=1.0, uncertain_fields=[], protected_tokens=[], requires_confirmation=False)
    with patch("backend.anvaya.services.llm._chat_completion", return_value=None):
        result = llm_answer("q", [], plan, {"AI_ASSIST_ENABLED": True, "OPENROUTER_API_KEY": "k", "OPENROUTER_BASE": "http://x", "OPENROUTER_MODEL": "m", "OPENROUTER_TIMEOUT_SECONDS": 5})
    assert result is None


# ── Voice service ─────────────────────────────────────────────────────────────

def test_voice_transcribe_disabled_when_flag_off(client, app):
    client.post("/api/auth/login", json={"username": "investigator.demo", "password": PASSWORD})
    resp = client.post("/api/voice/transcribe", data=b"fake-audio", content_type="audio/webm")
    assert resp.status_code == 404
    assert resp.json["code"] == "VOICE_DISABLED"


def test_voice_transcribe_rejects_non_audio_content_type(voice_app):
    with voice_app.test_client() as c:
        c.post("/api/auth/login", json={"username": "investigator.demo", "password": PASSWORD})
        resp = c.post("/api/voice/transcribe", data=b"data", content_type="text/plain")
        assert resp.status_code in (400, 415)


def test_voice_transcribe_enforces_max_upload_bytes(voice_app):
    with voice_app.test_client() as c:
        c.post("/api/auth/login", json={"username": "investigator.demo", "password": PASSWORD})
        huge = b"a" * (voice_app.config["MAX_UPLOAD_BYTES"] + 1)
        resp = c.post("/api/voice/transcribe", data=huge, content_type="audio/webm")
        assert resp.status_code == 413


def test_voice_transcribe_maps_sarvam_403_to_disabled(voice_app):
    import urllib.error
    with voice_app.test_client() as c:
        c.post("/api/auth/login", json={"username": "investigator.demo", "password": PASSWORD})
        with patch("backend.anvaya.services.voice._sarvam_request", side_effect=lambda *a, **kw: (_ for _ in ()).throw(Exception("VOICE_DISABLED"))):
            with patch("backend.anvaya.api.voice.transcribe_audio") as mock_stt:
                from backend.anvaya.api.errors import ApiError
                mock_stt.side_effect = ApiError("VOICE_DISABLED", "Voice provider rejected the request.", 404, False)
                resp = c.post("/api/voice/transcribe", data=b"audio", content_type="audio/webm")
                assert resp.status_code == 404


def test_voice_speak_disabled_when_flag_off(client):
    client.post("/api/auth/login", json={"username": "investigator.demo", "password": PASSWORD})
    resp = client.post("/api/voice/speak", json={"text": "test", "target_language_code": "en-IN"})
    assert resp.status_code == 404


def test_voice_translate_disabled_when_flag_off(client):
    client.post("/api/auth/login", json={"username": "investigator.demo", "password": PASSWORD})
    resp = client.post("/api/voice/translate", json={"text": "test", "source_language_code": "kn-IN", "target_language_code": "en-IN"})
    assert resp.status_code == 404


def test_voice_transcribe_returns_text_on_success(voice_app):
    with voice_app.test_client() as c:
        c.post("/api/auth/login", json={"username": "investigator.demo", "password": PASSWORD})
        with patch("backend.anvaya.api.voice.transcribe_audio", return_value={"text": "ಸರಗಳ್ಳತನ", "language": "kn-IN"}):
            resp = c.post("/api/voice/transcribe", data=b"audio", content_type="audio/webm")
            assert resp.status_code == 200
            assert resp.json["data"]["text"] == "ಸರಗಳ್ಳತನ"
