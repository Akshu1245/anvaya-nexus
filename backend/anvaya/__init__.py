from __future__ import annotations

from pathlib import Path

import logging

from flask import Flask, abort, jsonify, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.anvaya.api.errors import register_error_handlers
from backend.anvaya.api.health import health_blueprint
from backend.anvaya.config import Config, config_for, validate_catalyst_readonly_config, validate_production_config
from backend.anvaya.middleware.request_id import register_request_id_middleware
from backend.anvaya.repositories.sqlite import SQLiteRepository
from backend.anvaya.repositories.catalyst_gateway import CatalystReadGateway
from backend.anvaya.repositories.catalyst_readonly import CatalystReadOnlyRepository
from backend.anvaya.services.source_registry import seed_source_registry
from backend.anvaya.api.data_readiness import data_readiness_blueprint
from backend.anvaya.api.m3 import m3_blueprint
from backend.anvaya.api.voice import voice_blueprint
from backend.anvaya.services.auth import seed_users
from backend.anvaya.services.generator import generate
from backend.anvaya.platform.catalyst_appsail import configure_catalyst_appsail_runtime
from backend.anvaya.platform.factory import capability_summary, select_platform_adapters, validate_platform_config


def create_app(config_name: str | None = None, config_override: dict | None = None) -> Flask:
    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    # Vite emits hashed CSS/JavaScript into ``frontend/dist/assets``.  Flask's
    # static endpoint owns the ``/assets`` prefix, so it must point at that
    # directory rather than the distribution root; otherwise it returns the
    # API JSON 404 handler for asset requests.
    app = Flask(__name__, static_folder=str(frontend_dist / "assets"), static_url_path="/assets")

    selected: type[Config] = config_for(config_name)
    app.config.from_object(selected)
    if config_override:
        app.config.update(config_override)
    # AppSail constructs a request-scoped SDK client before fail-closed
    # validation checks that a real Catalyst client is present.
    configure_catalyst_appsail_runtime(app)
    validate_platform_config(app.config)
    validate_catalyst_readonly_config(app.config)
    if app.config["AUTH_BACKEND"] == "catalyst":
        raise ValueError("Catalyst authentication is not implemented; no prototype fallback is permitted")
    if app.config["ENV_NAME"] == "production":
        validate_production_config(app.config)
        app.config["SECRET_KEY"] = app.config["SESSION_SECRET"]
    if app.config["TRUST_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False

    @app.before_request
    def enforce_request_size() -> None:
        if (__import__("flask").request.content_length or 0) > app.config["MAX_CONTENT_LENGTH"]:
            abort(413)

    @app.after_request
    def allow_configured_frontend(response):
        origin = request.headers.get("Origin")
        allowed = {value.strip() for value in app.config["ALLOWED_ORIGINS"].split(",") if value.strip()}
        if origin in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
            response.headers.add("Vary", "Origin")
        return response

    register_request_id_middleware(app)
    register_error_handlers(app)

    if app.config["STORAGE_BACKEND"] == "catalyst":
        catalyst_client = app.config["CATALYST_DATASTORE_CLIENT"]
        repository = CatalystReadOnlyRepository(CatalystReadGateway(catalyst_client), catalyst_client)
    else:
        repository = SQLiteRepository.from_url(app.config["DATABASE_URL"])
        repository.initialize()
        seed_source_registry(repository, app.config)
        seed_users(repository, app.config["DEMO_PASSWORD"])
        # A Custom Runtime container has ephemeral local SQLite storage.  The
        # public datathon demo must therefore initialise its declared
        # synthetic fixture on first boot, otherwise a healthy deployment
        # contains no FIRs to search or inspect.  This runs only in explicit
        # public-demo mode and only when the local database is empty.
        if app.config["PUBLIC_DEMO_MODE"]:
            case_count = repository.connection.execute("SELECT COUNT(*) AS total FROM cases").fetchone()["total"]
            if case_count == 0:
                generate(repository, app.config, "test")

    app.extensions["repository"] = repository
    adapters = select_platform_adapters(app.config, repository)
    app.extensions["platform_adapters"] = adapters
    app.extensions["platform_capabilities"] = capability_summary(app.config, adapters)
    app.register_blueprint(health_blueprint)
    app.register_blueprint(data_readiness_blueprint)
    app.register_blueprint(m3_blueprint)
    app.register_blueprint(voice_blueprint)

    @app.get("/")
    @app.get("/<path:path>")
    def serve_frontend(path: str = ""):
        if path.startswith("api/"):
            abort(404)
        requested = frontend_dist / path
        if path and requested.is_file():
            return send_from_directory(frontend_dist, path)
        index = frontend_dist / "index.html"
        if index.is_file():
            return send_from_directory(frontend_dist, "index.html")
        return jsonify(
            {
                "request_id": getattr(__import__("flask").g, "request_id", "unavailable"),
                "code": "FRONTEND_NOT_BUILT",
                "message": "Frontend build is not available. Run npm run build.",
                "retryable": True,
            }
        ), 503

    return app
