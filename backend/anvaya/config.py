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
    SESSION_TTL_MINUTES = int(os.getenv("ANVAYA_SESSION_TTL_MINUTES", "60"))
    MAX_SEARCH_RESULTS = int(os.getenv("ANVAYA_MAX_SEARCH_RESULTS", "25"))
    SESSION_COOKIE_NAME = "anvaya_session"
    SESSION_SECRET = os.getenv("ANVAYA_SESSION_SECRET", "")
    ALLOWED_ORIGINS = os.getenv("ANVAYA_ALLOWED_ORIGINS", "http://localhost:5000,http://localhost:5173")
    TRUST_PROXY = os.getenv("ANVAYA_TRUST_PROXY", "false").lower() == "true"
    HTTPS_ENABLED = os.getenv("ANVAYA_HTTPS_ENABLED", "false").lower() == "true"
    MAX_CONTENT_LENGTH = int(os.getenv("ANVAYA_MAX_REQUEST_BYTES", "1048576"))
    MAX_UPLOAD_BYTES = int(os.getenv("ANVAYA_MAX_UPLOAD_BYTES", "524288"))
    LOGIN_RATE_LIMIT_PER_MINUTE = int(os.getenv("ANVAYA_LOGIN_RATE_LIMIT_PER_MINUTE", "10"))
    SEED_OFFICIAL_FIR_FIXTURE = os.getenv("ANVAYA_SEED_OFFICIAL_FIR_FIXTURE", "true").lower() == "true"


class DevelopmentConfig(Config):
    ENV_NAME = "development"
    DEBUG = True


class TestingConfig(Config):
    ENV_NAME = "testing"
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    SEED_OFFICIAL_FIR_FIXTURE = False


class ProductionConfig(Config):
    ENV_NAME = "production"
    HTTPS_ENABLED = os.getenv("ANVAYA_HTTPS_ENABLED", "true").lower() == "true"


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
