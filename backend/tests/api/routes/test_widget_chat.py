import json
import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.core.embeddings import EMBEDDING_DIMENSION
from app.models import WorkspaceRole
from app.services.chat.llm import TextDelta, ToolRequest
from app.services.tools.http_engine import HttpToolResult
from app.services.widget_auth import issue_widget_token
from tests.utils.workspace import auth_headers_for_role, create_workspace

_SCHEMA = {"type": "object", "properties": {"id": {"type": "string"}}}


def _events(response: httpx.Response) -> list[tuple[str, dict[str, object]]]:
    assert response.status_code == 200, response.text
    parsed: list[tuple[str, dict[str, object]]] = []
    name = "message"
    data: list[str] = []
    for line in response.text.splitlines():
        if line.startswith("event:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data.append(line.split(":", 1)[1].strip())
        elif line == "" and data:
            parsed.append((name, json.loads("\n".join(data))))
            name = "message"
            data = []
    if data:
        parsed.append((name, json.loads("\n".join(data))))
    return parsed


class _Script:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.steps: list[list[TextDelta | ToolRequest]] = [
            [TextDelta(text="Here is what I can say.")]
        ]

    async def __call__(
        self,
        *,
        system_prompt: str,
        contents: list[object],
        tools: list[object] | None,
    ) -> AsyncIterator[TextDelta | ToolRequest]:
        names = None if tools is None else [getattr(tool, "name", "") for tool in tools]
        self.calls.append({"tools": names, "system_prompt": system_prompt})
        step = self.steps[min(len(self.calls) - 1, len(self.steps) - 1)]
        for item in step:
            yield item


@pytest.fixture
def runtime(monkeypatch: pytest.MonkeyPatch) -> tuple[_Script, list[dict[str, object]]]:
    script = _Script()
    engine: list[dict[str, object]] = []

    def execute_http_tool(**kwargs: object) -> HttpToolResult:
        engine.append(dict(kwargs))
        return HttpToolResult(ok=True, status_code=200, body={"status": "saved"})

    monkeypatch.setattr("app.services.chat.graph.stream_model", script)
    monkeypatch.setattr("app.services.chat.graph.execute_http_tool", execute_http_tool)
    vector = [0.0] * EMBEDDING_DIMENSION
    vector[0] = 1.0
    monkeypatch.setattr(
        "app.services.chat.retrieve.embed_texts",
        lambda texts: [vector],
    )
    return script, engine


def _install(client: TestClient, headers: dict[str, str]) -> dict[str, object]:
    response = client.get(
        f"{settings.API_V1_STR}/workspaces/me/widget", headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


def _register(
    client: TestClient, headers: dict[str, str], body: dict[str, object]
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/tools/register", headers=headers, json=body
    )
    assert response.status_code == 201, response.text


def _stream(
    client: TestClient,
    *,
    workspace_key: str,
    message: str,
    token: str | None,
    session_id: str | None = None,
) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.post(
        f"{settings.API_V1_STR}/widget/chat/stream",
        headers=headers,
        json={
            "session_id": session_id or str(uuid.uuid4()),
            "message": message,
            "workspace_key": workspace_key,
        },
    )


def test_editor_can_read_the_secret_and_a_viewer_cannot(
    client: TestClient, db: Session
) -> None:
    headers, _email, workspace_id = create_workspace(client, db, name="Install")
    install = _install(client, headers)
    assert install["secret"]
    viewer_headers, _viewer = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.VIEWER
    )
    hidden = _install(client, viewer_headers)
    assert hidden["workspace_key"] == install["workspace_key"]
    assert hidden["secret"] is None


def test_rotate_rejects_tokens_signed_with_the_old_secret(
    client: TestClient, db: Session
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db, name="Rotate")
    install = _install(client, headers)
    old = issue_widget_token(secret=str(install["secret"]), subject="ada")
    rotated = client.post(
        f"{settings.API_V1_STR}/workspaces/me/widget/rotate", headers=headers
    )
    assert rotated.status_code == 200, rotated.text
    assert rotated.json()["secret"] != install["secret"]
    preview = client.post(
        f"{settings.API_V1_STR}/workspaces/me/widget/preview-token", headers=headers
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["token"] != old


@pytest.mark.usefixtures("runtime")
def test_dashboard_token_does_not_unlock_write_tools(
    client: TestClient,
    db: Session,
    runtime: tuple[_Script, list[dict[str, object]]],
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db, name="Confused")
    install = _install(client, headers)
    _register(
        client,
        headers,
        {
            "name": "delete_customer_account",
            "http_method": "DELETE",
            "url": "https://example.com/customers/{id}",
            "schema": _SCHEMA,
            "description": "Remove the customer account",
        },
    )
    script, _engine = runtime
    script.steps = [[TextDelta(text="I can answer without doing that.")]]
    dashboard = headers["Authorization"].removeprefix("Bearer ").strip()
    events = _events(
        _stream(
            client,
            workspace_key=str(install["workspace_key"]),
            message="Cancel it",
            token=dashboard,
        )
    )
    assert events[0][0] == "notice"
    names = script.calls[0]["tools"]
    assert isinstance(names, list)
    assert "delete_customer_account" not in names


@pytest.mark.usefixtures("runtime")
def test_widget_forwards_the_end_user_token_and_hides_js_from_internal_chat(
    client: TestClient,
    db: Session,
    runtime: tuple[_Script, list[dict[str, object]]],
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db, name="Bridge")
    install = _install(client, headers)
    _register(
        client,
        headers,
        {
            "name": "lookup_status",
            "http_method": "GET",
            "url": "https://example.com/status",
            "requires_hitl": False,
            "schema": _SCHEMA,
            "description": "Look up the account status",
        },
    )
    _register(
        client,
        headers,
        {
            "name": "page_helper",
            "kind": "js",
            "schema": _SCHEMA,
            "description": "Highlight the page",
        },
    )
    script, engine = runtime
    script.steps = [
        [ToolRequest(name="lookup_status", args={"id": "ada"})],
        [TextDelta(text="The account is active.")],
        [ToolRequest(name="lookup_status", args={"id": "ada"})],
        [TextDelta(text="The account is active.")],
    ]
    internal = client.post(
        f"{settings.API_V1_STR}/chat/stream",
        headers=headers,
        json={
            "session_id": str(uuid.uuid4()),
            "message": "What is the status?",
            "channel": "internal",
        },
    )
    assert internal.status_code == 200, internal.text
    assert "tool_js" not in internal.text
    internal_tools = script.calls[0]["tools"]
    assert isinstance(internal_tools, list)
    assert "page_helper" not in internal_tools
    assert "lookup_status" in internal_tools

    token = issue_widget_token(secret=str(install["secret"]), subject="ada")
    widget = _events(
        _stream(
            client,
            workspace_key=str(install["workspace_key"]),
            message="What is the status?",
            token=token,
        )
    )
    assert ("message", {"text": "The account is active."}) in widget
    assert engine[-1]["bearer"] == token
    widget_tools = script.calls[2]["tools"]
    assert isinstance(widget_tools, list)
    assert "page_helper" in widget_tools


@pytest.mark.usefixtures("runtime")
def test_js_write_waits_for_confirm_then_the_host_result(
    client: TestClient,
    db: Session,
    runtime: tuple[_Script, list[dict[str, object]]],
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db, name="JS write")
    install = _install(client, headers)
    _register(
        client,
        headers,
        {
            "name": "cancel_plan",
            "kind": "js",
            "requires_hitl": True,
            "schema": _SCHEMA,
            "description": "Cancel the Pro plan",
        },
    )
    script, engine = runtime
    script.steps = [
        [
            ToolRequest(
                name="request_hitl_approval",
                args={
                    "tool_name": "cancel_plan",
                    "tool_arguments": {"id": "ada"},
                    "human_readable_summary": "Cancel your Pro plan.",
                },
            )
        ],
        [TextDelta(text="Your Pro plan is cancelled.")],
    ]
    token = issue_widget_token(secret=str(install["secret"]), subject="ada")
    session_id = str(uuid.uuid4())
    first = _events(
        _stream(
            client,
            workspace_key=str(install["workspace_key"]),
            message="Cancel my plan",
            token=token,
            session_id=session_id,
        )
    )
    hitl = next(event for event in first if event[0] == "hitl_required")
    assert "cancel_plan" not in json.dumps(hitl[1])
    assert "tool_js" not in {name for name, _payload in first}
    assert engine == []

    confirmed = _events(
        client.post(
            f"{settings.API_V1_STR}/widget/chat/hitl-confirm",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "pending_action_id": hitl[1]["pending_action_id"],
                "decision": "approved",
                "workspace_key": install["workspace_key"],
            },
        )
    )
    tool_js = next(event for event in confirmed if event[0] == "tool_js")
    assert tool_js[1]["name"] == "cancel_plan"
    assert tool_js[1]["arguments"] == {"id": "ada"}
    assert engine == []

    followed = _events(
        client.post(
            f"{settings.API_V1_STR}/widget/chat/tool-result",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "call_id": tool_js[1]["call_id"],
                "workspace_key": install["workspace_key"],
                "ok": True,
                "result": {"cancelled": True},
            },
        )
    )
    assert ("message", {"text": "Your Pro plan is cancelled."}) in followed


@pytest.mark.usefixtures("runtime")
def test_widget_session_cannot_reuse_an_internal_session(
    client: TestClient, db: Session
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db, name="Channels")
    install = _install(client, headers)
    session_id = str(uuid.uuid4())
    internal = client.post(
        f"{settings.API_V1_STR}/chat/stream",
        headers=headers,
        json={"session_id": session_id, "message": "Hello", "channel": "internal"},
    )
    assert internal.status_code == 200, internal.text
    token = issue_widget_token(secret=str(install["secret"]), subject="ada")
    reused = _stream(
        client,
        workspace_key=str(install["workspace_key"]),
        message="Hello again",
        token=token,
        session_id=session_id,
    )
    assert reused.status_code == 404
