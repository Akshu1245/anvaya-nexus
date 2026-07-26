import json
import urllib.error
import urllib.request

from flask import Blueprint, current_app, g

from backend.anvaya.config import ai_assist_enabled, voice_enabled
from backend.anvaya.schemas.common import SuccessEnvelope
from backend.anvaya.schemas.health import HealthData

health_blueprint = Blueprint("health", __name__, url_prefix="/api")


def _check_ai_service(config) -> tuple[str, str]:
    if not ai_assist_enabled(config):
        return "disabled", "AI assist not configured"
    key = str(config.get("OPENROUTER_API_KEY") or "").strip()
    base = str(config.get("OPENROUTER_BASE") or "https://openrouter.ai/api/v1").rstrip("/")
    timeout = int(config.get("OPENROUTER_TIMEOUT_SECONDS") or 6)
    try:
        request = urllib.request.Request(
            f"{base}/models",
            headers={"Authorization": f"Bearer {key}"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=max(3, timeout // 2)) as response:
            body = json.loads(response.read().decode("utf-8"))
            if isinstance(body, dict) and body.get("data"):
                return "ok", "AI service reachable"
            return "degraded", "AI service responded but returned unexpected data"
    except urllib.error.HTTPError as error:
        return "degraded", f"AI service HTTP {error.code}"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return "unavailable", "AI service unreachable"


def _check_voice_service(config) -> tuple[str, str]:
    if not voice_enabled(config):
        return "disabled", "Voice service not configured"
    key = str(config.get("SARVAM_API_KEY") or "").strip()
    base = str(config.get("SARVAM_BASE") or "https://api.sarvam.ai").rstrip("/")
    timeout = int(config.get("SARVAM_TIMEOUT_SECONDS") or 15)
    try:
        request = urllib.request.Request(
            f"{base}/v1/models",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=max(5, timeout // 2)) as response:
            body = json.loads(response.read().decode("utf-8"))
            if isinstance(body, dict):
                return "ok", "Voice service reachable"
            return "degraded", "Voice service responded but returned unexpected data"
    except urllib.error.HTTPError as error:
        return "degraded", f"Voice service HTTP {error.code}"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return "unavailable", "Voice service unreachable"


@health_blueprint.get("/health")
def health():
    repository = current_app.extensions["repository"]
    ai_status, ai_message = _check_ai_service(current_app.config)
    voice_status, voice_message = _check_voice_service(current_app.config)
    data = HealthData(
        status="ok",
        service="anvaya-api",
        environment=current_app.config["ENV_NAME"],
        database=repository.health_check(),
        public_demo_enabled=bool(current_app.config.get("PUBLIC_DEMO_MODE")),
        ai_assist_enabled=ai_assist_enabled(current_app.config),
        voice_enabled=voice_enabled(current_app.config),
        ai_service_status=ai_status,
        ai_service_message=ai_message,
        voice_service_status=voice_status,
        voice_service_message=voice_message,
    )
    envelope = SuccessEnvelope[HealthData](
        request_id=g.request_id,
        data=data,
        warnings=[],
    )
    return envelope.model_dump(mode="json"), 200
