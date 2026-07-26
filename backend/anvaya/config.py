from __future__ import annotations

import os
from collections.abc import Mapping
from urllib.parse import urlparse


class Config:
    ENV_NAME = "production"
    TESTING = False
    DEBUG = False
    DATABASE_URL = os.getenv("ANVAYA_DATABASE_URL", "sqlite:///anvaya_local.db")
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = False
    CCTNS_FRESHNESS_HOURS = int(os.getenv("ANVAYA_FRESHNESS_CCTNS_HOURS", "720"))
    FORENSICS_FRESHNESS_HOURS = int(os.getenv("ANVAYA_FRESHNESS_FORENSICS_HOURS", "336"))
    VEHICLE_FRESHNESS_HOURS = int(os.getenv("ANVAYA_FRESHNESS_VEHICLE_HOURS", "720"))
    CONTEXT_FRESHNESS_HOURS = int(os.getenv("ANVAYA_FRESHNESS_CONTEXT_HOURS", "4320"))
    DEMO_PASSWORD = os.getenv("ANVAYA_DEMO_PASSWORD", "ANVAYA-DEMO-ONLY-2026")
    # A submission-only convenience gate.  It creates the normal short-lived
    # Investigator demo session; it never bypasses server-side policy checks.
    PUBLIC_DEMO_MODE = os.getenv("ANVAYA_PUBLIC_DEMO_MODE", "false").lower() == "true"
    SESSION_TTL_MINUTES = int(os.getenv("ANVAYA_SESSION_TTL_MINUTES", "60"))
    MAX_SEARCH_RESULTS = int(os.getenv("ANVAYA_MAX_SEARCH_RESULTS", "25"))
    SESSION_COOKIE_NAME = "anvaya_session"
    SESSION_SECRET = os.getenv("ANVAYA_SESSION_SECRET", "")
    ALLOWED_ORIGINS = os.getenv("ANVAYA_ALLOWED_ORIGINS", "http://localhost:5000,http://localhost:5173,http://localhost:8000,http://127.0.0.1:8000")
    TRUST_PROXY = os.getenv("ANVAYA_TRUST_PROXY", "false").lower() == "true"
    HTTPS_ENABLED = os.getenv("ANVAYA_HTTPS_ENABLED", "false").lower() == "true"
    MAX_CONTENT_LENGTH = int(os.getenv("ANVAYA_MAX_REQUEST_BYTES", "1048576"))
    MAX_UPLOAD_BYTES = int(os.getenv("ANVAYA_MAX_UPLOAD_BYTES", "524288"))
    LOGIN_RATE_LIMIT_PER_MINUTE = int(os.getenv("ANVAYA_LOGIN_RATE_LIMIT_PER_MINUTE", "10"))
    STORAGE_BACKEND = os.getenv("ANVAYA_STORAGE_BACKEND", "sqlite").lower()
    AUTH_BACKEND = os.getenv("ANVAYA_AUTH_BACKEND", "prototype").lower()
    ARTIFACT_STORAGE = os.getenv("ANVAYA_ARTIFACT_STORAGE", "local").lower()
    CATALYST_ENABLED = os.getenv("ANVAYA_CATALYST_ENABLED", "false").lower() == "true"
    CATALYST_PROJECT_ID = os.getenv("ANVAYA_CATALYST_PROJECT_ID", "")
    CATALYST_ENVIRONMENT = os.getenv("ANVAYA_CATALYST_ENVIRONMENT", "")
    CATALYST_API_BASE = os.getenv("ANVAYA_CATALYST_API_BASE", "")
    CATALYST_SERVICE_ACCOUNT_EMAIL = os.getenv("ANVAYA_CATALYST_SERVICE_ACCOUNT_EMAIL", "")
    CATALYST_CREDENTIALS_PATH = os.getenv("ANVAYA_CATALYST_CREDENTIALS_PATH", "")
    CATALYST_DATASTORE_ENABLED = os.getenv("ANVAYA_CATALYST_DATASTORE_ENABLED", "false").lower() == "true"
    CATALYST_AUTH_ENABLED = os.getenv("ANVAYA_CATALYST_AUTH_ENABLED", "false").lower() == "true"
    CATALYST_FILE_STORAGE_ENABLED = os.getenv("ANVAYA_CATALYST_FILE_STORAGE_ENABLED", "false").lower() == "true"
    CATALYST_RUNTIME = os.getenv("ANVAYA_CATALYST_RUNTIME", "injected").lower()
    # Injected only by a trusted bootstrap layer, AppSail request initialization,
    # or tests. No credentials are loaded from application configuration.
    CATALYST_DATASTORE_CLIENT = None
    CATALYST_SDK_INITIALIZER = None
    # Optional AI assist (Gemini / OpenRouter). Auto-enabled when key is present.
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("ANVAYA_GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))).strip()
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", os.getenv("ANVAYA_OPENROUTER_API_KEY", "")).strip()
    AI_ASSIST_ENABLED = (os.getenv("ANVAYA_AI_ASSIST_ENABLED", "true").lower() == "true") or bool(GEMINI_API_KEY) or bool(OPENROUTER_API_KEY)
    OPENROUTER_BASE = os.getenv("ANVAYA_OPENROUTER_BASE", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL = os.getenv("ANVAYA_OPENROUTER_MODEL", "google/gemini-2.5-flash" if GEMINI_API_KEY else "openrouter/free")
    OPENROUTER_FALLBACK_MODELS = os.getenv(
        "ANVAYA_OPENROUTER_FALLBACK_MODELS",
        "google/gemini-2.5-flash,meta-llama/llama-3.3-70b-instruct:free,google/gemma-3-27b-it:free",
    )
    OPENROUTER_TIMEOUT_SECONDS = int(os.getenv("ANVAYA_OPENROUTER_TIMEOUT_SECONDS", "10"))
    # Optional voice / translation (Sarvam AI). Auto-enabled when key is present.
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", os.getenv("ANVAYA_SARVAM_API_KEY", "")).strip()
    VOICE_ENABLED = (os.getenv("ANVAYA_VOICE_ENABLED", "true").lower() == "true") or bool(SARVAM_API_KEY)
    SARVAM_BASE = os.getenv("ANVAYA_SARVAM_BASE", "https://api.sarvam.ai")
    SARVAM_STT_MODEL = os.getenv("ANVAYA_SARVAM_STT_MODEL", "saaras:v3")
    SARVAM_TTS_MODEL = os.getenv("ANVAYA_SARVAM_TTS_MODEL", "bulbul:v3")
    SARVAM_TRANSLATE_MODEL = os.getenv("ANVAYA_SARVAM_TRANSLATE_MODEL", "mayura:v1")
    SARVAM_TIMEOUT_SECONDS = int(os.getenv("ANVAYA_SARVAM_TIMEOUT_SECONDS", "15"))


def ai_assist_enabled(config: Mapping[str, object]) -> bool:
    return bool(config.get("AI_ASSIST_ENABLED")) and (bool(str(config.get("GEMINI_API_KEY") or "").strip()) or bool(str(config.get("OPENROUTER_API_KEY") or "").strip()))


def voice_enabled(config: Mapping[str, object]) -> bool:
    return bool(config.get("VOICE_ENABLED")) or bool(str(config.get("SARVAM_API_KEY") or "").strip())


class DevelopmentConfig(Config):
    ENV_NAME = "development"
    DEBUG = True


class TestingConfig(Config):
    ENV_NAME = "testing"
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"


class ProductionConfig(Config):
    ENV_NAME = "production"
    HTTPS_ENABLED = os.getenv("ANVAYA_HTTPS_ENABLED", "true").lower() == "true"
    # Production never inherits the local-development demo credential.
    DEMO_PASSWORD = os.getenv("ANVAYA_DEMO_PASSWORD", "")


def validate_production_config(config: Mapping[str, object]) -> None:
    """Fail closed before a production server accepts requests."""
    secret = str(config.get("SESSION_SECRET") or "")
    if len(secret) < 32:
        raise ValueError("ANVAYA_SESSION_SECRET must be at least 32 characters in production")
    origins = str(config.get("ALLOWED_ORIGINS") or "")
    values = [value.strip() for value in origins.split(",") if value.strip()]
    if not values:
        raise ValueError("ANVAYA_ALLOWED_ORIGINS must contain at least one HTTPS origin in production")
    for value in values:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/"):
            raise ValueError("ANVAYA_ALLOWED_ORIGINS must contain comma-separated HTTPS origins")
    if int(config.get("MAX_CONTENT_LENGTH", 0)) <= 0 or int(config.get("MAX_UPLOAD_BYTES", 0)) <= 0:
        raise ValueError("Request and upload limits must be positive")
    if bool(config.get("PUBLIC_DEMO_MODE")) and len(str(config.get("DEMO_PASSWORD") or "")) < 24:
        raise ValueError("ANVAYA_DEMO_PASSWORD must be a private 24+ character value when public demo mode is enabled")


def validate_catalyst_readonly_config(config: Mapping[str, object]) -> None:
    """Validate explicit Development-only read wiring without any fallback."""
    if str(config.get("STORAGE_BACKEND") or "").lower() != "catalyst":
        return
    if not bool(config.get("CATALYST_ENABLED")) or not bool(config.get("CATALYST_DATASTORE_ENABLED")):
        raise ValueError("Catalyst storage requires ANVAYA_CATALYST_ENABLED=true and ANVAYA_CATALYST_DATASTORE_ENABLED=true")
    if str(config.get("ENV_NAME") or "").lower() == "production":
        raise ValueError("Catalyst read-only wiring is not authorized for production")
    provider_environment = str(config.get("CATALYST_ENVIRONMENT") or "").strip().lower()
    if provider_environment not in {"development", "dev", "sandbox"}:
        raise ValueError("Catalyst read-only wiring requires an explicit non-production environment")
    runtime = str(config.get("CATALYST_RUNTIME") or "").strip().lower()
    if runtime not in {"injected", "appsail"}:
        raise ValueError("Catalyst read-only wiring requires injected or appsail runtime mode")
    required = ("CATALYST_PROJECT_ID", "CATALYST_API_BASE")
    if any(not str(config.get(name) or "").strip() for name in required):
        raise ValueError("Catalyst read-only wiring requires project and API base configuration")
    client = config.get("CATALYST_DATASTORE_CLIENT")
    required_methods = ("execute_read", "health_check", "close")
    if client is None or any(not callable(getattr(client, method, None)) for method in required_methods):
        raise ValueError("Catalyst read-only wiring requires an injected datastore client")


CONFIGS: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def config_for(name: str | None = None) -> type[Config]:
    selected = (name or os.getenv("ANVAYA_ENV", "development")).lower()
    if selected not in CONFIGS:
        raise ValueError(f"Unsupported ANVAYA_ENV: {selected}")
    return CONFIGS[selected]
