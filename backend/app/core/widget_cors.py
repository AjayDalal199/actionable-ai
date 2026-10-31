"""Allow customer pages to call the widget API. Auth is the end-user JWT, not cookies."""

from collections.abc import MutableMapping
from typing import Any

from starlette.types import ASGIApp, Receive, Scope, Send

_ALLOW_METHODS = "GET, POST, OPTIONS"
_ALLOW_HEADERS = "Authorization, Content-Type, Accept"
_STRIP = {
    b"access-control-allow-origin",
    b"access-control-allow-credentials",
    b"access-control-allow-methods",
    b"access-control-allow-headers",
    b"access-control-expose-headers",
    b"access-control-max-age",
}


class WidgetCorsMiddleware:
    def __init__(self, app: ASGIApp, *, api_prefix: str) -> None:
        self.app = app
        self.api_prefix = api_prefix.rstrip("/")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not _is_widget_path(
            scope.get("path", ""), self.api_prefix
        ):
            await self.app(scope, receive, send)
            return
        origin = _header(scope, b"origin")
        if scope["method"] == "OPTIONS":
            await _empty(send, origin)
            return

        async def send_cors(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start" and origin:
                headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() not in _STRIP
                ]
                headers.extend(_cors_headers(origin))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_cors)


def _is_widget_path(path: str, api_prefix: str) -> bool:
    return path == "/widget.js" or path.startswith(f"{api_prefix}/widget/")


def _header(scope: Scope, name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key == name:
            return value.decode()
    return None


def _cors_headers(origin: str) -> list[tuple[bytes, bytes]]:
    encoded = origin.encode()
    return [
        (b"access-control-allow-origin", encoded),
        (b"vary", b"Origin"),
        (b"access-control-allow-methods", _ALLOW_METHODS.encode()),
        (b"access-control-allow-headers", _ALLOW_HEADERS.encode()),
        (b"access-control-max-age", b"600"),
    ]


async def _empty(send: Send, origin: str | None) -> None:
    headers = _cors_headers(origin) if origin else []
    await send(
        {
            "type": "http.response.start",
            "status": 204,
            "headers": headers,
        }
    )
    await send({"type": "http.response.body", "body": b""})
