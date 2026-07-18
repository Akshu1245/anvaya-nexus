from __future__ import annotations

from pathlib import Path

import logging

from flask import Flask, abort, jsonify, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.anvaya.api.errors import register_error_handlers
from backend.anvaya.api.health import health_blueprint
from backend.anvaya.config import Config, config_for, validate_production_config
from backend.anvaya.middleware.request_id import register_request_id_middleware
from backend.anvaya.repositories.sqlite import SQLiteRepository
from backend.anvaya.services.source_registry import seed_source_registry
from backend.anvaya.api.data_readiness import data_readiness_blueprint
from backend.anvaya.api.m3 import m3_blueprint
from backend.anvaya.services.auth import seed_users
from backend.anvaya.services.official_fir import seed_official_fir_fixture
from backend.anvaya.api.official_fir import official_fir_blueprint


def create_app(config_name: str | None = None, config_override: dict | None = None) -> Flask:
    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    app = Flask(__name__, static_folder=str(frontend_dist / "assets"), static_url_path="/assets")

    selected: type[Config] = config_for(config_name)
    app.config.from_object(selected)
    if config_override:
        app.config.update(config_override)
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

    register_request_id_middleware(app)
    register_error_handlers(app)

    repository = SQLiteRepository.from_url(app.config["DATABASE_URL"])
    repository.initialize()
    seed_source_registry(repository, app.config)
    seed_users(repository, app.config["DEMO_PASSWORD"])
    if app.config["SEED_OFFICIAL_FIR_FIXTURE"]:
        seed_official_fir_fixture(repository)
    app.extensions["repository"] = repository
    app.register_blueprint(health_blueprint)
    app.register_blueprint(data_readiness_blueprint)
    app.register_blueprint(m3_blueprint)
    app.register_blueprint(official_fir_blueprint)

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
