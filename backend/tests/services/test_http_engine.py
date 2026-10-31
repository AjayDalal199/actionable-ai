import json
import uuid
from collections.abc import Callable

import httpx
import pytest

from app.models import HttpMethod, ToolKind, ToolRegistry
from app.services.tools.http_engine import (
    TOOL_HTTP_TIMEOUT,
    HttpToolResult,
    execute_http_tool,
)

_DENIED = "Refused to call a private, link-local, or metadata address."
_SCHEME = (
    "Refused to call a non-HTTPS URL. "
    "HTTP is allowed only for localhost, 127.0.0.1, and ::1."
)
_BEARER = "dashboard-member-token"

_DENIED_URLS = [
    "https://10.0.0.1/secret",
    "https://10.255.255.255/",
    "https://172.16.0.1/",
    "https://172.31.255.255/",
    "https://192.168.0.10/admin",
    "https://169.254.169.254/latest/meta-data/",
    "https://169.254.170.2/v2/credentials",
    "https://169.254.1.1/",
    "http://169.254.169.254/latest/meta-data/",
    "https://[fe80::1]/",
    "https://[fd00:ec2::254]/latest/meta-data/",
    "https://[::ffff:10.0.0.1]/",
    "https://[::ffff:169.254.169.254]/latest/meta-data/",
    "https://metadata.google.internal/computeMetadata/v1/",
    "https://metadata.google.internal:443/computeMetadata/v1/",
    "https://Metadata.Google.Internal./computeMetadata/v1/",
    "https://metadata.goog/computeMetadata/v1/",
    "https://0177.254.169.254/latest/meta-data/",
    "https://0xa9.0xfe.0xa9.0xfe/latest/meta-data/",
]

_LOOPBACK_URLS = [
    "http://localhost/health",
    "http://localhost:8080/health",
    "http://127.0.0.1/health",
    "http://127.0.0.1:8080/health",
    "http://[::1]/health",
    "https://localhost/health",
    "https://127.0.0.1/health",
    "https://[::1]/health",
]

_PUBLIC_URLS = [
    "https://api.example.com/v1",
    "https://8.8.8.8/",
    "https://172.15.255.255/",
    "https://172.32.0.1/",
    "https://192.167.1.1/",
    "https://11.0.0.1/",
]


def _tool(
    url: str | None,
    *,
    method: HttpMethod | None = HttpMethod.GET,
    kind: ToolKind = ToolKind.HTTP,
) -> ToolRegistry:
    return ToolRegistry(
        workspace_id=uuid.uuid4(),
        name="get_customer" if method == HttpMethod.GET else "update_customer",
        kind=kind,
        http_method=None if kind == ToolKind.JS else method,
        url=None if kind == ToolKind.JS else url,
        tool_schema={"type": "object", "properties": {"id": {"type": "string"}}},
        description="",
    )


def _run(
    url: str | None,
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    method: HttpMethod | None = HttpMethod.GET,
    arguments: dict[str, object] | None = None,
    bearer: str | None = None,
    kind: ToolKind = ToolKind.HTTP,
    follow_redirects: bool = False,
) -> tuple[HttpToolResult, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def wrapped(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    client = httpx.Client(
        transport=httpx.MockTransport(wrapped),
        follow_redirects=follow_redirects,
    )
    try:
        result = execute_http_tool(
            tool=_tool(url, method=method, kind=kind),
            arguments={} if arguments is None else arguments,
            bearer=bearer,
            client=client,
        )
    finally:
        client.close()
    return result, seen


def _ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"ok": True, "url": str(request.url)})


def _forbid(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"refused URL was called: {request.url}")


@pytest.mark.parametrize("url", _DENIED_URLS)
def test_denylist_refuses_private_link_local_and_metadata_hosts(url: str) -> None:
    result, seen = _run(url, _forbid, bearer=_BEARER)
    assert seen == []
    assert result.ok is False
    assert result.status_code is None
    assert result.error == _DENIED
    assert _BEARER not in (result.error or "")


@pytest.mark.parametrize("url", _LOOPBACK_URLS)
def test_localhost_exception_is_called(url: str) -> None:
    result, seen = _run(url, _ok, bearer=_BEARER)
    assert result.ok is True
    assert result.error is None
    assert len(seen) == 1
    assert seen[0].url.host in {"localhost", "127.0.0.1", "::1"}
    assert seen[0].headers["authorization"] == f"Bearer {_BEARER}"


@pytest.mark.parametrize("url", _PUBLIC_URLS)
def test_public_https_targets_are_called(url: str) -> None:
    result, seen = _run(url, _ok)
    assert result.ok is True
    assert len(seen) == 1
    assert seen[0].url.scheme == "https"


@pytest.mark.parametrize(
    "url",
    ["http://api.example.com/v1", "http://8.8.8.8/health", "file:///etc/passwd"],
)
def test_non_https_is_refused_off_localhost(url: str) -> None:
    result, seen = _run(url, _forbid)
    assert seen == []
    assert result.ok is False
    assert result.error == _SCHEME


def test_bearer_is_forwarded_and_not_invented() -> None:
    result, seen = _run(
        "https://api.example.com/customers",
        _ok,
        arguments={"id": "abc", "active": True},
        bearer=f"  {_BEARER}  ",
    )
    assert result.ok is True
    assert result.status_code == 200
    assert result.error is None
    assert isinstance(result.body, dict)
    assert result.body["ok"] is True
    request = seen[0]
    assert request.headers["authorization"] == f"Bearer {_BEARER}"
    assert request.url.params["id"] == "abc"
    assert request.url.params["active"] == "true"
    assert "cookie" not in request.headers
    names = [
        name.lower() for name in request.headers if name.lower() != "authorization"
    ]
    assert "x-api-key" not in names


def test_omitted_or_blank_bearer_sets_no_authorization() -> None:
    omitted, seen = _run("https://api.example.com/customers", _ok, bearer=None)
    assert omitted.ok is True
    assert "authorization" not in seen[0].headers
    blank, blank_seen = _run("https://api.example.com/customers", _ok, bearer="  ")
    assert blank.ok is True
    assert "authorization" not in blank_seen[0].headers


def test_bearer_with_whitespace_is_refused_before_the_call() -> None:
    result, seen = _run(
        "https://api.example.com/customers",
        _forbid,
        bearer=f"{_BEARER}\r\nX-Injected: 1",
    )
    assert seen == []
    assert result.ok is False
    assert result.error == "Bearer token must be a single header value."
    assert _BEARER not in (result.error or "")


def test_non_2xx_is_a_structured_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "Customer not found"})

    result, seen = _run("https://api.example.com/customers/missing", handler)
    assert len(seen) == 1
    assert result.ok is False
    assert result.status_code == 404
    assert result.body == {"detail": "Customer not found"}
    assert result.error == "The client API returned HTTP 404."
    assert result.error is not None
    assert "success" not in result.error.lower()


@pytest.mark.parametrize("status", [502, 503])
def test_retries_a_gateway_status_once(status: int) -> None:
    payloads = [(status, {"attempt": 1}), (200, {"attempt": 2}), (500, {"attempt": 3})]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == f"Bearer {_BEARER}"
        code, body = payloads.pop(0)
        return httpx.Response(code, json=body)

    result, seen = _run(
        "https://api.example.com/customers",
        handler,
        method=HttpMethod.POST,
        arguments={"id": "abc"},
        bearer=_BEARER,
    )
    assert result.ok is True
    assert result.status_code == 200
    assert result.error is None
    assert result.body == {"attempt": 2}
    assert len(seen) == 2
    assert payloads == [(500, {"attempt": 3})]
    assert seen[0].method == "POST"
    assert json.loads(seen[0].content) == {"id": "abc"}
    assert json.loads(seen[1].content) == {"id": "abc"}


def test_second_gateway_failure_is_returned_and_not_retried_again() -> None:
    payloads = [(503, {"attempt": 1}), (503, {"attempt": 2}), (200, {"attempt": 3})]

    def handler(_request: httpx.Request) -> httpx.Response:
        code, body = payloads.pop(0)
        return httpx.Response(code, json=body)

    result, seen = _run("https://api.example.com/customers", handler)
    assert len(seen) == 2
    assert payloads == [(200, {"attempt": 3})]
    assert result.ok is False
    assert result.status_code == 503
    assert result.body == {"attempt": 2}
    assert result.error == "The client API returned HTTP 503."


@pytest.mark.parametrize("status", [500, 504, 429])
def test_other_statuses_are_not_retried(status: int) -> None:
    payloads = [(status, {"attempt": 1}), (200, {"attempt": 2})]

    def handler(_request: httpx.Request) -> httpx.Response:
        code, body = payloads.pop(0)
        return httpx.Response(code, json=body)

    result, seen = _run("https://api.example.com/customers", handler)
    assert len(seen) == 1
    assert payloads == [(200, {"attempt": 2})]
    assert result.ok is False
    assert result.status_code == status
    assert result.error == f"The client API returned HTTP {status}."


def test_timeout_is_not_retried() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    result, seen = _run("https://api.example.com/customers", handler)
    assert len(seen) == 1
    assert result.ok is False
    assert result.status_code is None
    assert result.error == "The client API timed out."


def test_redirect_is_not_followed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "169.254.169.254":
            raise AssertionError("followed a redirect to metadata")
        return httpx.Response(
            302,
            headers={"location": "https://169.254.169.254/latest/meta-data/"},
        )

    result, seen = _run(
        "https://api.example.com/go",
        handler,
        follow_redirects=True,
    )
    assert len(seen) == 1
    assert seen[0].url.host == "api.example.com"
    assert result.ok is False
    assert result.status_code == 302
    assert result.error == "The client API returned HTTP 302."


def test_path_arguments_stay_on_the_registered_host() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"host": request.url.host})

    result, seen = _run(
        "https://api.example.com/customers/{id}",
        handler,
        method=HttpMethod.POST,
        arguments={"id": "a/../../169.254.169.254", "note": "hi"},
        bearer=_BEARER,
    )
    assert result.ok is True
    request = seen[0]
    assert request.url.host == "api.example.com"
    assert request.url.raw_path == b"/customers/a%2F..%2F..%2F169.254.169.254"
    assert json.loads(request.content) == {"note": "hi"}
    assert request.headers["authorization"] == f"Bearer {_BEARER}"


def test_missing_path_parameter_does_not_call() -> None:
    result, seen = _run(
        "https://api.example.com/customers/{id}",
        _forbid,
        arguments={},
    )
    assert seen == []
    assert result.ok is False
    assert result.error == "Missing value for URL parameter 'id'."


def test_tools_router_has_no_execute_endpoint() -> None:
    from app.api.routes import tools as tools_routes

    paths = [getattr(route, "path", "") for route in tools_routes.router.routes]
    assert paths
    assert all("execute" not in path for path in paths)


def test_js_tool_is_not_called() -> None:
    result, seen = _run(None, _forbid, method=None, kind=ToolKind.JS)
    assert seen == []
    assert result.ok is False
    assert result.error == "JS tools are not called by the API request engine."


def test_default_client_sets_a_timeout_and_does_not_follow_redirects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    class RecordingClient(httpx.Client):
        def __init__(self, *args: object, **kwargs: object) -> None:
            seen["init_timeout"] = kwargs.get("timeout")
            seen["init_follow_redirects"] = kwargs.get("follow_redirects")
            super().__init__(
                transport=httpx.MockTransport(_ok),
                timeout=TOOL_HTTP_TIMEOUT,
                follow_redirects=False,
            )

        def request(
            self,
            method: str,
            url: httpx.URL | str,
            **kwargs: object,
        ) -> httpx.Response:
            seen["request_timeout"] = kwargs.get("timeout")
            seen["follow_redirects"] = kwargs.get("follow_redirects")
            return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr("app.services.tools.http_engine.httpx.Client", RecordingClient)
    result = execute_http_tool(
        tool=_tool("https://api.example.com/v1"),
        arguments={},
        bearer=_BEARER,
    )
    assert result.ok is True
    assert seen["init_timeout"] == TOOL_HTTP_TIMEOUT
    assert seen["init_follow_redirects"] is False
    assert seen["request_timeout"] == TOOL_HTTP_TIMEOUT
    assert seen["follow_redirects"] is False
    assert TOOL_HTTP_TIMEOUT.connect == 5.0
    assert TOOL_HTTP_TIMEOUT.read == 10.0


def test_database_string_method_is_called() -> None:
    from sqlalchemy.orm.attributes import set_committed_value

    tool = _tool("https://api.example.com/notes", method=HttpMethod.POST)
    set_committed_value(tool, "http_method", "POST")
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"status": "saved"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        result = execute_http_tool(
            tool=tool,
            arguments={"note": "tide is high"},
            bearer=_BEARER,
            client=client,
        )
    finally:
        client.close()
    assert type(tool.http_method) is str
    assert result.ok is True
    assert result.status_code == 200
    assert len(seen) == 1
    assert seen[0].method == "POST"
    assert json.loads(seen[0].content) == {"note": "tide is high"}
    assert seen[0].headers["authorization"] == f"Bearer {_BEARER}"
