"""Safe, offline Catalyst error categories.

These types deliberately carry no HTTP response body, endpoint, header, or
credential material.  A future transport may map its failures into these
categories before they reach the repository boundary.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.anvaya.api.errors import ApiError


@dataclass(frozen=True)
class CatalystClientFailure(Exception):
    category: str
    retryable: bool = False
    safe_reason: str = "Catalyst operation failed."

    def __str__(self) -> str:  # Never surface transport detail through repr/str.
        return self.safe_reason


_ERRORS: dict[str, tuple[str, str, int, bool]] = {
    "not_configured": ("CATALYST_NOT_CONFIGURED", "Catalyst is not configured.", 503, False),
    "unavailable": ("CATALYST_UNAVAILABLE", "Catalyst is currently unavailable.", 503, True),
    "authentication": ("CATALYST_AUTHORIZATION_FAILED", "Catalyst authorization failed.", 503, False),
    "unsupported_query": ("CATALYST_QUERY_UNSUPPORTED", "This Catalyst query is not supported.", 501, False),
    "invalid_parameters": ("CATALYST_INVALID_PARAMETERS", "Catalyst query parameters are invalid.", 400, False),
    "not_found": ("CATALYST_ROW_NOT_FOUND", "Catalyst record was not found.", 404, False),
    "conflict": ("CATALYST_CONFLICT", "Catalyst record conflicts with existing data.", 409, False),
    "rate_limited": ("CATALYST_RATE_LIMITED", "Catalyst rate limit was reached.", 429, True),
    "timeout": ("CATALYST_TIMEOUT", "Catalyst did not respond in time.", 503, True),
    "malformed_response": ("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True),
    "not_verified": ("CATALYST_CAPABILITY_UNVERIFIED", "Catalyst capability has not been verified.", 503, False),
    "not_implemented": ("CATALYST_NOT_IMPLEMENTED", "Catalyst integration is not implemented in this milestone.", 503, False),
}


def translate_catalyst_failure(error: CatalystClientFailure) -> ApiError:
    """Convert a categorised transport failure into the normal safe envelope."""
    code, message, status, retryable = _ERRORS.get(
        error.category,
        ("CATALYST_UNAVAILABLE", "Catalyst is currently unavailable.", 503, bool(error.retryable)),
    )
    return ApiError(code, message, status, retryable or error.retryable)
