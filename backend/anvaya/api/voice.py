from __future__ import annotations

from flask import Blueprint, current_app, g, request

from backend.anvaya.api.errors import ApiError
from backend.anvaya.api.m3 import _ok, protected
from backend.anvaya.services.audit import audit
from backend.anvaya.services.voice import AUDIO_CONTENT_TYPES, speak_text, transcribe_audio, translate_text

voice_blueprint = Blueprint("voice", __name__, url_prefix="/api/voice")


@voice_blueprint.post("/transcribe")
@protected
def voice_transcribe():
    repo = current_app.extensions["repository"]
    if request.content_length and request.content_length > current_app.config["MAX_UPLOAD_BYTES"]:
        raise ApiError("AUDIO_TOO_LARGE", "Audio upload exceeds the allowed size.", 413, False)
    audio = request.get_data()
    content_type = (request.content_type or "").split(";")[0].strip().lower()
    if content_type not in AUDIO_CONTENT_TYPES:
        raise ApiError("AUDIO_TYPE_UNSUPPORTED", "Unsupported audio content type.", 415, False)
    language = str(request.args.get("language_code") or request.headers.get("X-Anvaya-Language") or "unknown")
    mode = str(request.args.get("mode") or "codemix")
    result = transcribe_audio(current_app.config, audio, content_type, language_code=language, mode=mode)
    audit(repo, "VOICE_STT", "SUCCESS", g.user["id"], g.request_id, {"language": result.get("language"), "text_length": len(result["text"])})
    return _ok(result)


@voice_blueprint.post("/speak")
@protected
def voice_speak():
    repo = current_app.extensions["repository"]
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text") or "")
    target = str(payload.get("target_language_code") or "en-IN")
    result = speak_text(current_app.config, text, target)
    audit(repo, "VOICE_TTS", "SUCCESS", g.user["id"], g.request_id, {"target_language_code": target, "text_length": len(text)})
    return _ok(result)


@voice_blueprint.post("/translate")
@protected
def voice_translate():
    repo = current_app.extensions["repository"]
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text") or "")
    source = str(payload.get("source_language_code") or "auto")
    target = str(payload.get("target_language_code") or "en-IN")
    result = translate_text(current_app.config, text, source, target)
    audit(repo, "TRANSLATE", "SUCCESS", g.user["id"], g.request_id, {"source_language_code": source, "target_language_code": target})
    return _ok(result)
