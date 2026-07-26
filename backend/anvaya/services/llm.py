from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from datetime import date
from typing import Any

from pydantic import ValidationError

from backend.anvaya.config import ai_assist_enabled
from backend.anvaya.schemas.query import QueryFilters, QueryPlan

ALLOWED_INTENTS = {"SEARCH", "DISCOVER", "VERIFY", "REPORT"}
ALLOWED_FILTER_KEYS = {
    "offence", "location", "date_from", "date_to", "status",
    "case_identifier", "phone", "imei", "vehicle_registration",
    "person_name", "person_role", "crime_number", "case_number",
}

DEFAULT_FREE_MODEL = "openrouter/free"
DEFAULT_FALLBACK_MODELS = (
    "openrouter/free,"
    "meta-llama/llama-3.3-70b-instruct:free,"
    "google/gemma-3-27b-it:free,"
    "qwen/qwen3-8b:free"
)


def _model_candidates(config: Mapping[str, object]) -> list[str]:
    primary = str(config.get("OPENROUTER_MODEL") or DEFAULT_FREE_MODEL).strip()
    raw = str(config.get("OPENROUTER_FALLBACK_MODELS") or DEFAULT_FALLBACK_MODELS)
    extras = [item.strip() for item in raw.split(",") if item.strip()]
    ordered: list[str] = []
    for model in [primary, *extras]:
        if model and model not in ordered:
            ordered.append(model)
    return ordered[:4]


def _gemini_direct_completion(config: Mapping[str, object], messages: list[dict[str, str]], max_tokens: int) -> tuple[str | None, str | None]:
    gemini_key = str(config.get("GEMINI_API_KEY") or "").strip()
    if not gemini_key:
        return None, None
    model = str(config.get("GEMINI_MODEL") or "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
    contents = []
    system_text = ""
    for msg in messages:
        role = msg.get("role", "user")
        text = msg.get("content", "")
        if role == "system":
            system_text += text + "\n\n"
        else:
            contents.append({"role": "user" if role == "user" else "model", "parts": [{"text": text}]})
    if system_text and contents:
        contents[0]["parts"][0]["text"] = f"{system_text}Request:\n{contents[0]['parts'][0]['text']}"
    payload = json.dumps({
        "contents": contents or [{"role": "user", "parts": [{"text": system_text}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": max_tokens, "responseMimeType": "application/json"}
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=int(config.get("OPENROUTER_TIMEOUT_SECONDS") or 8)) as response:
            body = json.loads(response.read().decode("utf-8"))
            candidates = body.get("candidates", [])
            if candidates and candidates[0].get("content", {}).get("parts"):
                text = candidates[0]["content"]["parts"][0].get("text", "")
                if text and text.strip():
                    return text.strip(), f"google/{model}"
    except Exception:
        pass
    return None, None


def _chat_completion(
    config: Mapping[str, object],
    messages: list[dict[str, str]],
    max_tokens: int = 700,
) -> tuple[str | None, dict[str, Any]]:
    """Return (content, meta). meta includes model_used / fallback_reason for audit."""
    meta: dict[str, Any] = {"model_used": None, "fallback_reason": None, "attempts": 0}
    if not ai_assist_enabled(config):
        meta["fallback_reason"] = "ai_disabled"
        return None, meta

    # Try direct Google Gemini API if key is present
    gemini_text, gemini_model = _gemini_direct_completion(config, messages, max_tokens)
    if gemini_text:
        meta["model_used"] = gemini_model
        meta["attempts"] = 1
        return gemini_text, meta

    key = str(config.get("OPENROUTER_API_KEY") or "").strip()
    if not key:
        meta["fallback_reason"] = "missing_key"
        return None, meta
    base = str(config.get("OPENROUTER_BASE") or "https://openrouter.ai/api/v1").rstrip("/")
    timeout = int(config.get("OPENROUTER_TIMEOUT_SECONDS") or 6)
    candidates = _model_candidates(config)
    last_reason = "no_candidates"
    for index, model in enumerate(candidates):
        meta["attempts"] = index + 1
        body_payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        if model == "openrouter/free" and len(candidates) > 1:
            body_payload["models"] = [item for item in candidates[1:] if item != model]
        payload = json.dumps(body_payload).encode("utf-8")
        request = urllib.request.Request(
            f"{base}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://anvaya.local",
                "X-Title": "ANVAYA",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            if isinstance(content, str) and content.strip():
                meta["model_used"] = body.get("model") or model
                if index:
                    meta["fallback_reason"] = f"recovered_after_{index}_failures"
                return content, meta
            last_reason = "empty_content"
        except urllib.error.HTTPError as error:
            last_reason = f"http_{error.code}"
            if error.code == 429 and index < len(candidates) - 1:
                time.sleep(0.35)
            continue
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError):
            last_reason = "provider_error"
            continue
    meta["fallback_reason"] = last_reason
    return None, meta


def _parse_json_blob(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _coerce_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _build_plan_from_payload(payload: dict[str, Any], sources: list[str]) -> QueryPlan | None:
    intent = str(payload.get("intent") or "SEARCH").upper()
    if intent not in ALLOWED_INTENTS:
        return None
    raw_filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else {}
    filters: dict[str, Any] = {}
    for key, value in raw_filters.items():
        if key not in ALLOWED_FILTER_KEYS or value in (None, ""):
            continue
        if key in {"date_from", "date_to"}:
            parsed = _coerce_date(value)
            if parsed is not None:
                filters[key] = parsed
        else:
            filters[key] = str(value)
    uncertain = payload.get("uncertain_fields")
    if not isinstance(uncertain, list):
        uncertain = [field for field in ("offence", "location") if filters.get(field) is None]
    confidence = payload.get("confidence", 0.75)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.75
    confidence = max(0.0, min(1.0, confidence))
    try:
        return QueryPlan(
            intent=intent,  # type: ignore[arg-type]
            filters=QueryFilters(**filters),
            selected_sources=list(sources),
            result_limit=25,
            confidence=confidence,
            uncertain_fields=[str(item) for item in uncertain if str(item)],
            protected_tokens=[],
            requires_confirmation=bool(payload.get("requires_confirmation", bool(uncertain))),
        )
    except ValidationError:
        return None


def llm_interpret(text: str, sources: list[str], config: Mapping[str, object]) -> QueryPlan | None:
    system = (
        "You convert investigator questions into a strict JSON query plan for a police FIR search system. "
        "Return only JSON with keys: intent, filters, confidence, uncertain_fields. "
        "intent must be one of SEARCH, DISCOVER, VERIFY, REPORT. "
        "filters may only include: offence, location, status, date_from, date_to, case_identifier, phone, imei, vehicle_registration, person_name, person_role, crime_number, case_number. "
        "Use offence codes like CHAIN_SNATCHING, HOUSEBREAKING, VEHICLE_THEFT when obvious. "
        "Use location JAYANAGAR for Jayanagar references. "
        "Use status UNRESOLVED or RESOLVED when asked. "
        "Dates must be ISO YYYY-MM-DD. "
        "Never include SQL, database commands, or fields outside the allow-list. "
        "Support English, Kannada, Hindi, and code-mixed text."
    )
    user = json.dumps({"question": text, "selected_sources": sources})
    content, _meta = _completion_result(
        config,
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=500,
    )
    payload = _parse_json_blob(content or "")
    if not payload:
        return None
    return _build_plan_from_payload(payload, sources)


def _compact_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact = []
    for record in records[:12]:
        compact.append({
            "case_id": record.get("case_id") or record.get("id"),
            "crime_number": record.get("crime_number") or record.get("fir_number"),
            "case_number": record.get("case_number"),
            "status": (record.get("canonical_status") or {}).get("name") or record.get("status"),
            "station": (record.get("police_unit") or {}).get("name") or record.get("station_id"),
            "district": (record.get("district") or {}).get("name") or record.get("district_id"),
            "category": (record.get("category") or {}).get("name"),
            "registered_at": record.get("registered_at"),
            "source_record_ids": list(dict.fromkeys(record.get("source_record_references") or [])),
            "masking_applied": bool((record.get("masking") or {}).get("applied")),
        })
    return compact


def templated_answer(question: str, records: list[dict[str, Any]], plan: QueryPlan) -> dict[str, Any]:
    if not records:
        return {
            "answer": "I did not find any authorised FIR records for that scope in the selected sources.",
            "cited_source_ids": [],
            "engine": "deterministic",
            "grounded": True,
            "confidence": 1.0,
            "reasoning": {
                "title": "Search execution steps",
                "steps": [
                    {"step": "Query parsed", "detail": f"Intent: {plan.intent}, filters: {plan.filters.model_dump(exclude_none=True)}"},
                    {"step": "Sources queried", "detail": f"{len(plan.selected_sources)} source(s) searched"},
                    {"step": "No results found", "detail": "No matching records returned from any source"},
                ],
                "provenance": "Deterministic search — all cited records are policy-filtered synthetic data",
            },
        }
    place = plan.filters.location or "the selected scope"
    status = plan.filters.status or "any status"
    offence = plan.filters.offence or "the requested offence pattern"
    lead = records[0]
    crime = lead.get("crime_number") or lead.get("fir_number") or lead.get("case_id")
    station = (lead.get("police_unit") or {}).get("name") or lead.get("station_id") or "an unrecorded unit"
    cited = list(dict.fromkeys(source for record in records for source in (record.get("source_record_references") or [])))
    answer = (
        f"I found {len(records)} authorised FIR record{'s' if len(records) != 1 else ''} for {offence} near {place} with status {status}. "
        f"The first returned record is {crime} at {station}. "
        "These are policy-filtered synthetic records only; open a case for Case 360, provenance, and human review."
    )
    return {
        "answer": answer,
        "cited_source_ids": cited[:8],
        "engine": "deterministic",
        "grounded": True,
        "confidence": 1.0,
        "reasoning": {
            "title": "Search execution steps",
            "steps": [
                {"step": "Query parsed", "detail": f"Intent: {plan.intent}, filters: {plan.filters.model_dump(exclude_none=True)}"},
                {"step": "Sources queried", "detail": f"{len(plan.selected_sources)} source(s) searched"},
                {"step": f"Found {len(records)} record(s)", "detail": f"First: {crime} at {station}"},
                {"step": "Template applied", "detail": "Deterministic answer generated from structured fields"},
            ],
            "provenance": "Deterministic search — all cited records are policy-filtered synthetic data",
        },
    }


def _completion_result(config: Mapping[str, object], messages: list[dict[str, str]], max_tokens: int = 700) -> tuple[str | None, dict[str, Any]]:
    """Normalize _chat_completion return for callers and older test mocks."""
    raw = _chat_completion(config, messages, max_tokens=max_tokens)
    if isinstance(raw, tuple) and len(raw) == 2:
        content, meta = raw
        if not isinstance(meta, dict):
            meta = {"model_used": None, "fallback_reason": "invalid_meta"}
        return (content if isinstance(content, str) or content is None else str(content)), meta
    if raw is None:
        return None, {"model_used": None, "fallback_reason": "provider_error"}
    if isinstance(raw, str):
        return raw, {"model_used": None, "fallback_reason": None}
    return None, {"model_used": None, "fallback_reason": "provider_error"}


def llm_answer(question: str, records: list[dict[str, Any]], plan: QueryPlan, config: Mapping[str, object]) -> dict[str, Any] | None:
    if not ai_assist_enabled(config):
        return None
    allowed_ids = {source for record in records for source in (record.get("source_record_references") or [])}
    system = (
        "You answer investigator questions using only the provided FIR JSON records. "
        "Return JSON with keys answer and cited_source_ids. "
        "Never invent case IDs, people, guilt, risk, or facts not present in the records. "
        "Mention masking or limitations when records are masked. "
        "Keep the answer concise and operational, 2-4 sentences."
    )
    user = json.dumps({
        "question": question,
        "plan": plan.model_dump(mode="json"),
        "records": _compact_records(records),
    })
    content, meta = _completion_result(
        config,
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=450,
    )
    payload = _parse_json_blob(content or "")
    if not payload or not isinstance(payload.get("answer"), str):
        return None
    cited = payload.get("cited_source_ids")
    if not isinstance(cited, list):
        cited = []
    verified = [str(item) for item in cited if str(item) in allowed_ids]
    if records and not verified:
        verified = list(allowed_ids)[:3]
    confidence = 0.0
    if meta.get("fallback_reason") is None or meta.get("fallback_reason", "").startswith("recovered"):
        confidence = 0.85
    elif meta.get("fallback_reason") == "ai_disabled":
        confidence = 0.0
    else:
        confidence = 0.6
    reasoning_steps = [
        {"step": "Question interpreted", "detail": f"Intent: {plan.intent}"},
        {"step": "Records retrieved", "detail": f"{len(records)} record(s) from {len(plan.selected_sources)} source(s)"},
        {"step": "AI answer drafted", "detail": f"Model: {meta.get('model_used') or 'unknown'}"},
    ]
    if meta.get("fallback_reason"):
        reasoning_steps.append({"step": "Fallback note", "detail": f"Reason: {meta['fallback_reason']}"})
    return {
        "answer": payload["answer"].strip(),
        "cited_source_ids": verified,
        "engine": "ai_assisted",
        "grounded": True,
        "confidence": confidence,
        "reasoning": {
            "title": "AI reasoning steps",
            "steps": reasoning_steps,
            "provenance": "AI-generated answer grounded in policy-filtered synthetic records",
        },
        "model_used": meta.get("model_used"),
        "fallback_reason": meta.get("fallback_reason"),
    }
