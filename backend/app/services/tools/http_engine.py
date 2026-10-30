"""Call one registered HTTP tool.

The orchestrator calls this after any human-in-the-loop check. There is no
HTTP route: a public execute endpoint would skip that check. JS tools have
no URL and are not called here. Registration still does not call the URL.

The bearer is whatever the caller supplies. This module does not mint a
token and does not invent permissions. Internal chat passes the dashboard
member's token. The host end-user JWT arrives with Phase 6.
"""

import ipaddress
import json
import logging
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlsplit

import httpx

from app.models import HttpMethod, ToolKind, ToolRegistry

logger = logging.getLogger(__name__)

# Connect 5s, everything else 10s. A retry is a second attempt, not a loop.
TOOL_HTTP_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

# Same three hosts registration allows over plain HTTP for integrator testing.
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_RFC1918 = (
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
)
# AWS IPv6 instance metadata. The IPv4 metadata addresses 169.254.169.254
# and 169.254.170.2 are inside the link-local range checked below.
_AWS_IPV6_METADATA = ipaddress.IPv6Address("fd00:ec2::254")
_METADATA_HOSTS = frozenset(
    {
        "metadata.google.internal",
        "metadata.goog",
    }
)
_RETRY_STATUSES = frozenset({502, 503})
_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_HEX_DIGITS = frozenset("0123456789abcdef")

_DENIED_MESSAGE = "Refused to call a private, link-local, or metadata address."
_SCHEME_MESSAGE = (
    "Refused to call a non-HTTPS URL. "
    "HTTP is allowed only for localhost, 127.0.0.1, and ::1."
)
_JS_MESSAGE = "JS tools are not called by the API request engine."
_HTTP_FIELDS = "HTTP tools require an HTTP method and URL."
_ARGUMENTS = "Tool arguments must be an object."
_JSON_ARGUMENTS = "Tool arguments must be JSON values."
_BEARER = "Bearer token must be a single header value."
_TIMEOUT_MESSAGE = "The client API timed out."
_UNREACHABLE_MESSAGE = "The client API could not be reached."


@dataclass(frozen=True, kw_only=True)
class HttpToolResult:
    """Outcome of one HTTP tool call.

    ``ok`` is true only when the client API returned a 2xx status. A refusal
    or any other status sets ``ok`` false and puts a model-readable
    explanation in ``error``.
    """

    ok: bool
    status_code: int | None = None
    body: object = None
    error: str | None = None


class _Call:
    def __init__(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, str] | None,
        json_body: dict[str, Any] | None,
    ) -> None:
        self.method = method
        self.url = url
        self.headers = headers
        self.params = params
        self.json_body = json_body


def execute_http_tool(
    *,
    tool: ToolRegistry,
    arguments: Mapping[str, Any],
    bearer: str | None = None,
    client: httpx.Client | None = None,
) -> HttpToolResult:
    """Call ``tool`` once, or twice when the first response is 502 or 503.

    ``bearer`` is the raw token, not an ``Authorization`` header. When it is
    omitted, no ``Authorization`` header is sent. ``client`` overrides the
    default client; each attempt still uses :data:`TOOL_HTTP_TIMEOUT` and
    does not follow redirects.
    """
    prepared = _prepare(tool, arguments, bearer)
    if isinstance(prepared, HttpToolResult):
        _log_failure(tool.name, prepared)
        return prepared
    if client is None:
        with httpx.Client(
            timeout=TOOL_HTTP_TIMEOUT,
            follow_redirects=False,
        ) as owned:
            result = _exchange(owned, prepared)
    else:
        result = _exchange(client, prepared)
    if not result.ok:
        _log_failure(tool.name, result)
    return result


def _prepare(
    tool: ToolRegistry,
    arguments: Mapping[str, Any],
    bearer: str | None,
) -> _Call | HttpToolResult:
    if tool.kind == ToolKind.JS:
        return _failure(_JS_MESSAGE)
    if tool.kind != ToolKind.HTTP:
        return _failure("Unsupported tool kind.")
    method = tool.http_method
    stored_url = tool.url
    if method is None or not stored_url:
        return _failure(_HTTP_FIELDS)
    # Rows loaded through the string column come back as plain strings.
    try:
        method = HttpMethod(method)
    except ValueError:
        return _failure(_HTTP_FIELDS)
    provided = _argument_map(arguments)
    if isinstance(provided, HttpToolResult):
        return provided
    filled = _fill_url(stored_url, provided)
    if isinstance(filled, HttpToolResult):
        return filled
    url, remaining = filled
    denial = _denial_reason(url)
    if denial is not None:
        return _failure(denial)
    headers = _authorization(bearer)
    if isinstance(headers, HttpToolResult):
        return headers
    if method == HttpMethod.GET:
        params = _query_params(remaining)
        if isinstance(params, HttpToolResult):
            return params
        return _Call(method.value, url, headers, params, None)
    body = _json_body(remaining)
    if isinstance(body, HttpToolResult):
        return body
    return _Call(method.value, url, headers, None, body)


def _exchange(client: httpx.Client, call: _Call) -> HttpToolResult:
    first = _attempt(client, call)
    if isinstance(first, HttpToolResult):
        return first
    if first.status_code not in _RETRY_STATUSES:
        return _from_response(first)
    first.close()
    second = _attempt(client, call)
    if isinstance(second, HttpToolResult):
        return second
    return _from_response(second)


def _attempt(client: httpx.Client, call: _Call) -> httpx.Response | HttpToolResult:
    try:
        return client.request(
            call.method,
            call.url,
            headers=call.headers,
            params=call.params,
            json=call.json_body,
            timeout=TOOL_HTTP_TIMEOUT,
            follow_redirects=False,
        )
    except httpx.TimeoutException:
        return _failure(_TIMEOUT_MESSAGE)
    except httpx.RequestError:
        return _failure(_UNREACHABLE_MESSAGE)
    except TypeError, ValueError:
        return _failure(_JSON_ARGUMENTS)


def _from_response(response: httpx.Response) -> HttpToolResult:
    body = _response_body(response)
    status_code = response.status_code
    if 200 <= status_code <= 299:
        return HttpToolResult(ok=True, status_code=status_code, body=body)
    return _failure(
        f"The client API returned HTTP {status_code}.",
        status_code=status_code,
        body=body,
    )


def _response_body(response: httpx.Response) -> object:
    if not response.content:
        return None
    media_type = (
        response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    )
    if media_type.endswith("/json") or media_type.endswith("+json"):
        try:
            return response.json()
        except ValueError:
            pass
    return response.text


def _argument_map(
    arguments: Mapping[str, Any],
) -> dict[str, Any] | HttpToolResult:
    if not isinstance(arguments, Mapping):
        return _failure(_ARGUMENTS)
    try:
        provided = dict(arguments)
    except TypeError, ValueError:
        return _failure(_ARGUMENTS)
    if any(not isinstance(key, str) for key in provided):
        return _failure(_ARGUMENTS)
    return provided


def _fill_url(
    url: str, arguments: Mapping[str, Any]
) -> tuple[str, dict[str, Any]] | HttpToolResult:
    missing: list[str] = []
    invalid: list[str] = []
    used: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in arguments:
            if key not in missing:
                missing.append(key)
            return ""
        token = _scalar(arguments[key])
        if token is None or token == "":
            if key not in invalid:
                invalid.append(key)
            return ""
        used.add(key)
        return quote(token, safe="")

    filled = _PLACEHOLDER.sub(replace, url)
    if missing:
        return _failure(f"Missing value for URL parameter '{missing[0]}'.")
    if invalid:
        return _failure(
            f"URL parameter '{invalid[0]}' must be a string, number, or boolean."
        )
    remaining = {key: value for key, value in arguments.items() if key not in used}
    return filled, remaining


def _query_params(
    values: Mapping[str, Any],
) -> dict[str, str] | None | HttpToolResult:
    if not values:
        return None
    params: dict[str, str] = {}
    for key, value in values.items():
        rendered = _scalar(value)
        if rendered is None:
            return _failure(
                f"Query argument '{key}' must be a string, number, or boolean."
            )
        params[key] = rendered
    return params


def _json_body(
    values: Mapping[str, Any],
) -> dict[str, Any] | None | HttpToolResult:
    if not values:
        return None
    body = dict(values)
    try:
        json.dumps(body, allow_nan=False)
    except TypeError, ValueError:
        return _failure(_JSON_ARGUMENTS)
    return body


def _authorization(bearer: str | None) -> dict[str, str] | HttpToolResult:
    if bearer is None:
        return {}
    token = bearer.strip()
    if token == "":
        return {}
    if any(character.isspace() for character in token):
        return _failure(_BEARER)
    return {"Authorization": f"Bearer {token}"}


def _denial_reason(url: str) -> str | None:
    parts = urlsplit(url.strip())
    host = _normalize_host(parts.hostname)
    if host is None:
        return _SCHEME_MESSAGE
    # Literal addresses and metadata hostnames only. Integer-form hosts and
    # DNS names that resolve into these ranges are the V1 SSRF pass.
    if _is_blocked_host(host):
        return _DENIED_MESSAGE
    if parts.scheme == "https":
        return None
    if parts.scheme == "http" and _is_loopback_exception(host):
        return None
    return _SCHEME_MESSAGE


def _normalize_host(hostname: str | None) -> str | None:
    if not hostname:
        return None
    host = hostname.rstrip(".").lower()
    return host or None


def _is_loopback_exception(host: str) -> bool:
    if host in _LOOPBACK_HOSTS:
        return True
    ip = _parse_ip(host)
    if ip is None:
        return False
    return ip == ipaddress.ip_address("127.0.0.1") or ip == ipaddress.ip_address("::1")


def _is_blocked_host(host: str) -> bool:
    if host in _METADATA_HOSTS:
        return True
    if _is_obfuscated_ipv4(host):
        return True
    ip = _parse_ip(host)
    if ip is None:
        return False
    if isinstance(ip, ipaddress.IPv4Address):
        return bool(ip.is_link_local) or any(ip in network for network in _RFC1918)
    return bool(ip.is_link_local) or ip == _AWS_IPV6_METADATA


def _parse_ip(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        parsed = ipaddress.ip_address(host)
    except ValueError:
        return None
    if isinstance(parsed, ipaddress.IPv6Address) and parsed.ipv4_mapped is not None:
        return parsed.ipv4_mapped
    return parsed


def _is_obfuscated_ipv4(host: str) -> bool:
    """Dotted IPv4 written with leading zeros or hex, which hides metadata IPs."""
    parts = host.split(".")
    if len(parts) != 4:
        return False
    obfuscated = False
    for part in parts:
        if (
            part.startswith("0x")
            and len(part) > 2
            and all(character in _HEX_DIGITS for character in part[2:])
        ):
            obfuscated = True
            continue
        if not part.isdigit():
            return False
        if len(part) > 1 and part.startswith("0"):
            obfuscated = True
    return obfuscated


def _scalar(value: object) -> str | None:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and math.isfinite(value):
        return str(value)
    return None


def _failure(
    error: str, *, status_code: int | None = None, body: object = None
) -> HttpToolResult:
    return HttpToolResult(ok=False, status_code=status_code, body=body, error=error)


def _log_failure(name: str, result: HttpToolResult) -> None:
    logger.info("Tool %s failed: %s", name, result.error)
