"""Logical parameter validation for offline Catalyst templates.

It deliberately does not produce an executable ZCQL string. Transport-level
parameter binding is unverified and intentionally left unimplemented.
"""
from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any, Mapping

from backend.anvaya.api.errors import ApiError
from backend.anvaya.repositories.catalyst_templates import (
    CatalystParameterDefinition, CatalystParameterKind, CatalystQueryParameters, CatalystQueryTemplate,
)
from backend.anvaya.repositories.discovery_requests import RELATIONSHIP_TYPES

_CANONICAL_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,127}$")


def _invalid() -> ApiError:
    return ApiError("CATALYST_INVALID_PARAMETERS", "Catalyst query parameters are invalid.", 400, False)


def _timestamp(value: str) -> str:
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    if "T" not in candidate:
        raise _invalid()
    try:
        datetime.fromisoformat(candidate)
    except (TypeError, ValueError) as error:
        raise _invalid() from error
    return value


def _date(value: str) -> str:
    if not isinstance(value, str):
        raise _invalid()
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise _invalid() from error
    return value


def _value(definition: CatalystParameterDefinition, value: Any) -> Any:
    if value is None:
        if definition.allow_null:
            return None
        raise _invalid()
    if definition.kind is CatalystParameterKind.CANONICAL_ID:
        if not isinstance(value, str) or not _CANONICAL_ID.fullmatch(value):
            raise _invalid()
        return value
    if definition.kind is CatalystParameterKind.STRING:
        if not isinstance(value, str) or (definition.maximum is not None and len(value) > definition.maximum):
            raise _invalid()
        return value
    if definition.kind is CatalystParameterKind.INTEGER:
        if isinstance(value, bool) or not isinstance(value, int):
            raise _invalid()
        return value
    if definition.kind is CatalystParameterKind.LIMIT:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > (definition.maximum or 50):
            raise _invalid()
        return value
    if definition.kind is CatalystParameterKind.OFFSET:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise _invalid()
        return value
    if definition.kind is CatalystParameterKind.TIMESTAMP:
        if not isinstance(value, str):
            raise _invalid()
        return _timestamp(value)
    if definition.kind is CatalystParameterKind.DATE:
        return _date(value)
    if definition.kind is CatalystParameterKind.BOOLEAN:
        if not isinstance(value, bool):
            raise _invalid()
        return value
    if definition.kind is CatalystParameterKind.STRING_LIST:
        if not isinstance(value, (list, tuple)):
            raise _invalid()
        normalized = tuple(dict.fromkeys(value))
        if not normalized or any(not isinstance(item, str) or not _CANONICAL_ID.fullmatch(item) for item in normalized):
            raise _invalid()
        return normalized
    if definition.kind is CatalystParameterKind.RELATIONSHIP_TYPE_LIST:
        if not isinstance(value, (list, tuple)):
            raise _invalid()
        normalized = tuple(dict.fromkeys(value))
        if not normalized or any(not isinstance(item, str) or item not in RELATIONSHIP_TYPES for item in normalized):
            raise _invalid()
        return normalized
    raise _invalid()


def bind_parameters(template: CatalystQueryTemplate, supplied: Mapping[str, Any]) -> CatalystQueryParameters:
    expected = {definition.name: definition for definition in template.parameters}
    if set(supplied) - set(expected):
        raise _invalid()
    values: dict[str, Any] = {}
    for name, definition in expected.items():
        if name not in supplied:
            if definition.required:
                raise _invalid()
            values[name] = None
            continue
        values[name] = _value(definition, supplied[name])
    return CatalystQueryParameters(values=values)
