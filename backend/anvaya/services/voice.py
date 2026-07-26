from __future__ import annotations

import base64
import json
import uuid
import urllib.error
import urllib.request
from collections.abc import Mapping

from backend.anvaya.api.errors import ApiError
from backend.anvaya.config import voice_enabled

AUDIO_CONTENT_TYPES = {
    "audio/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/mp4",
    "audio/aac",
}


def _sarvam_request(config: Mapping[str, object], path: str, *, method: str = "POST", data: bytes | None = None, headers: dict[str, str] | None = None) -> dict:
    if not voice_enabled(config):
        raise ApiError("VOICE_DISABLED", "Voice services are not enabled for this deployment.", 404, False)
    key = str(config.get("SARVAM_API_KEY") or "").strip()
    base = str(config.get("SARVAM_BASE") or "https://api.sarvam.ai").rstrip("/")
    timeout = int(config.get("SARVAM_TIMEOUT_SECONDS") or 15)
    request_headers = {"api-subscription-key": key, **(headers or {})}
    request = urllib.request.Request(f"{base}{path}", data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 403:
            raise ApiError("VOICE_DISABLED", "Voice provider rejected the request.", 404, False) from error
        raise ApiError("VOICE_PROVIDER_ERROR", "Voice provider request failed.", 502, True) from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ApiError("VOICE_PROVIDER_ERROR", "Voice provider request failed.", 502, True) from error


def _multipart_audio(audio: bytes, content_type: str, fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = f"----anvaya-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        chunks.append(f"{value}\r\n".encode())
    filename = "audio.webm" if "webm" in content_type else "audio.wav"
    chunks.append(f"--{boundary}\r\n".encode())
    chunks.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    chunks.append(f"Content-Type: {content_type}\r\n\r\n".encode())
    chunks.append(audio)
    chunks.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(chunks), boundary


def transcribe_audio(config: Mapping[str, object], audio: bytes, content_type: str, *, language_code: str = "unknown", mode: str = "codemix") -> dict:
    if not audio:
        raise ApiError("AUDIO_REQUIRED", "Audio payload is required.", 400, False)
    if content_type not in AUDIO_CONTENT_TYPES:
        raise ApiError("AUDIO_TYPE_UNSUPPORTED", "Unsupported audio content type.", 415, False)
    model = str(config.get("SARVAM_STT_MODEL") or "saaras:v3")
    body, boundary = _multipart_audio(audio, content_type, {"model": model, "mode": mode})
    payload = _sarvam_request(
        config,
        "/speech-to-text",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    text = payload.get("transcript") or payload.get("text") or payload.get("output") or ""
    if not isinstance(text, str) or not text.strip():
        raise ApiError("TRANSCRIPTION_EMPTY", "No speech was detected in the audio.", 422, False)
    return {"text": text.strip(), "language": payload.get("language_code") or language_code}


def speak_text(config: Mapping[str, object], text: str, target_language_code: str) -> dict:
    if not text.strip():
        raise ApiError("TEXT_REQUIRED", "Text is required for speech synthesis.", 400, False)
    model = str(config.get("SARVAM_TTS_MODEL") or "bulbul:v3")
    payload = _sarvam_request(
        config,
        "/text-to-speech",
        data=json.dumps({
            "text": text[:2500],
            "target_language_code": target_language_code,
            "model": model,
            "speaker": "shubh",
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    audio_b64 = payload.get("audios")
    if isinstance(audio_b64, list) and audio_b64:
        audio_b64 = audio_b64[0]
    if not isinstance(audio_b64, str) or not audio_b64:
        raise ApiError("TTS_EMPTY", "Speech synthesis returned no audio.", 422, False)
    return {"audio_base64": audio_b64, "content_type": "audio/wav", "target_language_code": target_language_code}


def translate_text(config: Mapping[str, object], text: str, source_language_code: str, target_language_code: str) -> dict:
    if not text.strip():
        raise ApiError("TEXT_REQUIRED", "Text is required for translation.", 400, False)
    model = str(config.get("SARVAM_TRANSLATE_MODEL") or "mayura:v1")
    payload = _sarvam_request(
        config,
        "/translate",
        data=json.dumps({
            "input": text[:5000],
            "source_language_code": source_language_code,
            "target_language_code": target_language_code,
            "model": model,
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    translated = payload.get("translated_text") or payload.get("output") or payload.get("translation")
    if not isinstance(translated, str) or not translated.strip():
        raise ApiError("TRANSLATION_EMPTY", "Translation returned no text.", 422, False)
    return {
        "text": translated.strip(),
        "source_language_code": source_language_code,
        "target_language_code": target_language_code,
    }
