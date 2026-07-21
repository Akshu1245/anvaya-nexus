from flask import Blueprint, current_app, g

from backend.anvaya.config import ai_assist_enabled, voice_enabled
from backend.anvaya.schemas.common import SuccessEnvelope
from backend.anvaya.schemas.health import HealthData

health_blueprint = Blueprint("health", __name__, url_prefix="/api")


@health_blueprint.get("/health")
def health():
    repository = current_app.extensions["repository"]
    data = HealthData(
        status="ok",
        service="anvaya-api",
        environment=current_app.config["ENV_NAME"],
        database=repository.health_check(),
        public_demo_enabled=bool(current_app.config.get("PUBLIC_DEMO_MODE")),
        ai_assist_enabled=ai_assist_enabled(current_app.config),
        voice_enabled=voice_enabled(current_app.config),
    )
    envelope = SuccessEnvelope[HealthData](
        request_id=g.request_id,
        data=data,
        warnings=[],
    )
    return envelope.model_dump(mode="json"), 200
