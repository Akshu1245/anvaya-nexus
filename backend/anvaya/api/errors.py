from __future__ import annotations

from flask import Flask, g
from werkzeug.exceptions import HTTPException

from backend.anvaya.schemas.common import ErrorEnvelope


class ApiError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable


def _response(code: str, message: str, retryable: bool, status_code: int):
    body = ErrorEnvelope(
        request_id=getattr(g, "request_id", "unavailable"),
        code=code,
        message=message,
        retryable=retryable,
    )
    return body.model_dump(mode="json"), status_code


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return _response(error.code, error.message, error.retryable, error.status_code)

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        return _response(
            code=f"HTTP_{error.code}",
            message=error.description if error.code != 500 else "An unexpected error occurred.",
            retryable=bool(error.code and error.code >= 500),
            status_code=error.code or 500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unhandled API error", exc_info=error)
        return _response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
            retryable=True,
            status_code=500,
        )
