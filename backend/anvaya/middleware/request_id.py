from __future__ import annotations

import re
import uuid

from flask import Flask, g, request

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def register_request_id_middleware(app: Flask) -> None:
    @app.before_request
    def assign_request_id() -> None:
        supplied = request.headers.get("X-Request-ID", "")
        g.request_id = supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else str(uuid.uuid4())

    @app.after_request
    def expose_request_id(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", "unavailable")
        return response
