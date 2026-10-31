import asyncio
import uuid

import pytest
from sqlmodel import Session

from app.models import HttpMethod, ToolKind, ToolRegistry, Workspace
from app.services.chat.graph import execute, invoke_tool
from app.services.tools.http_engine import HttpToolResult


def _workspace(db: Session) -> Workspace:
    row = Workspace(name=f"Tools {uuid.uuid4()}")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _tool(
    db: Session,
    workspace: Workspace,
    *,
    name: str,
    kind: ToolKind,
    requires_hitl: bool,
    method: HttpMethod | None = None,
    url: str | None = None,
) -> ToolRegistry:
    row = ToolRegistry(
        workspace_id=workspace.id,
        name=name,
        kind=kind,
        http_method=method,
        url=url,
        tool_schema={"type": "object", "properties": {"id": {"type": "string"}}},
        requires_hitl=requires_hitl,
        description="Remove the customer account",
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_unapproved_write_does_not_call_the_engine(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = _workspace(db)
    tool = _tool(
        db,
        workspace,
        name="delete_customer_account",
        kind=ToolKind.HTTP,
        requires_hitl=True,
        method=HttpMethod.DELETE,
        url="https://api.internal.corp/customers/{id}",
    )
    called: list[object] = []

    def execute_http_tool(**kwargs: object) -> HttpToolResult:
        called.append(kwargs)
        return HttpToolResult(ok=True, status_code=200, body={})

    monkeypatch.setattr("app.services.chat.graph.execute_http_tool", execute_http_tool)
    result = asyncio.run(
        execute(
            {
                "session_id": str(uuid.uuid4()),
                "workspace_id": str(workspace.id),
                "user_id": str(uuid.uuid4()),
                "bearer": "raw-token",
                "approved": False,
                "visible": "",
                "iteration": 0,
                "transcript": [],
                "tool_call": {
                    "tool_id": str(tool.id),
                    "arguments": {"id": "ada"},
                    "function_name": "delete_customer_account",
                    "function_args": {"id": "ada"},
                },
            }
        )
    )
    assert called == []
    pending = result["pending"]
    assert isinstance(pending, dict)
    assert pending["summary"] == "Remove the customer account"
    assert "https://" not in pending["summary"]
    assert "API" not in pending["summary"]
    assert str(tool.id) not in pending["summary"]


def test_approved_write_calls_the_engine_with_the_raw_bearer(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = _workspace(db)
    tool = _tool(
        db,
        workspace,
        name="delete_customer_account",
        kind=ToolKind.HTTP,
        requires_hitl=True,
        method=HttpMethod.DELETE,
        url="https://api.internal.corp/customers/{id}",
    )
    called: list[dict[str, object]] = []

    def execute_http_tool(**kwargs: object) -> HttpToolResult:
        tool = kwargs["tool"]
        called.append(
            {
                "bearer": kwargs["bearer"],
                "arguments": kwargs["arguments"],
                "tool_id": getattr(tool, "id", None),
            }
        )
        return HttpToolResult(ok=True, status_code=200, body={"status": "saved"})

    monkeypatch.setattr("app.services.chat.graph.execute_http_tool", execute_http_tool)
    result = asyncio.run(
        execute(
            {
                "session_id": str(uuid.uuid4()),
                "workspace_id": str(workspace.id),
                "user_id": str(uuid.uuid4()),
                "bearer": "raw-token",
                "approved": True,
                "visible": "",
                "iteration": 0,
                "transcript": [],
                "tool_call": {
                    "tool_id": str(tool.id),
                    "arguments": {"id": "ada"},
                    "function_name": "delete_customer_account",
                    "function_args": {"id": "ada"},
                },
            }
        )
    )
    assert result["force_answer"] is True
    assert result["tool_error"] is None
    assert len(called) == 1
    assert called[0]["bearer"] == "raw-token"
    assert called[0]["arguments"] == {"id": "ada"}
    assert called[0]["tool_id"] == tool.id


def test_js_execute_does_not_call_the_engine(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = _workspace(db)
    tool = _tool(
        db, workspace, name="page_helper", kind=ToolKind.JS, requires_hitl=False
    )
    called: list[object] = []
    monkeypatch.setattr(
        "app.services.chat.graph.execute_http_tool",
        lambda **kwargs: called.append(kwargs),
    )
    result = asyncio.run(
        execute(
            {
                "workspace_id": str(workspace.id),
                "approved": True,
                "visible": "",
                "transcript": [],
                "tool_call": {
                    "tool_id": str(tool.id),
                    "arguments": {"id": "ada"},
                    "function_name": "page_helper",
                    "function_args": {"id": "ada"},
                    "kind": "js",
                    "tool_name": "page_helper",
                    "requires_hitl": False,
                },
            }
        )
    )
    assert called == []
    assert result["js_call"]["tool_name"] == "page_helper"
    assert result["pending"] is None


def test_js_tools_are_not_sent_to_the_engine(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = _workspace(db)
    tool = _tool(
        db, workspace, name="page_helper", kind=ToolKind.JS, requires_hitl=False
    )
    called: list[object] = []
    monkeypatch.setattr(
        "app.services.chat.graph.execute_http_tool",
        lambda **kwargs: called.append(kwargs),
    )
    result = invoke_tool(
        tool_id=str(tool.id),
        workspace_id=str(workspace.id),
        arguments={},
        bearer="raw-token",
        approved=True,
    )
    assert called == []
    assert isinstance(result, HttpToolResult)
    assert result.ok is False
    assert result.error == "That action is not available."
