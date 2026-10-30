"""Check tool names, schemas, URLs, and the HITL lock. Does not open a connection."""

import re
from typing import Any
from urllib.parse import urlsplit

from app.models import HttpMethod
from app.services.tools.errors import InvalidToolError

_NAME_RE = re.compile(r"^[a-z0-9_]+$")
_NAME_MAX = 128
_URL_MAX = 2048
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_WRITE_METHODS = frozenset({HttpMethod.POST, HttpMethod.PUT, HttpMethod.DELETE})

_URL_MESSAGE = "URL must use HTTPS. HTTP is allowed only for localhost."
_SCHEMA_MESSAGE = "Schema must be a JSON object with type and properties."


def validate_name(name: object) -> str:
    if (
        not isinstance(name, str)
        or len(name) > _NAME_MAX
        or _NAME_RE.fullmatch(name) is None
    ):
        raise InvalidToolError("Tool name must be snake_case matching ^[a-z0-9_]+$.")
    return name


def validate_schema(schema: object) -> dict[str, Any]:
    if (
        not isinstance(schema, dict)
        or schema.get("type") != "object"
        or not isinstance(schema.get("properties"), dict)
    ):
        raise InvalidToolError(_SCHEMA_MESSAGE)
    return schema


def validate_url(url: object) -> str:
    if not isinstance(url, str):
        raise InvalidToolError(_URL_MESSAGE)
    cleaned = url.strip()
    if (
        not cleaned
        or len(cleaned) > _URL_MAX
        or any(char.isspace() for char in cleaned)
    ):
        raise InvalidToolError(_URL_MESSAGE)
    parsed = urlsplit(cleaned)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme == "https" and host:
        return cleaned
    if parsed.scheme == "http" and host in _LOOPBACK_HOSTS:
        return cleaned
    raise InvalidToolError(_URL_MESSAGE)


def requires_hitl_for(method: HttpMethod | None, requested: bool) -> bool:
    if method in _WRITE_METHODS:
        return True
    return requested
