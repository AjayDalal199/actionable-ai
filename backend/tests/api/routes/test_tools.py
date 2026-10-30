import uuid

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import (
    HttpMethod,
    ToolKind,
    ToolRegistry,
    User,
    WorkspaceMembership,
    WorkspaceRole,
)
from tests.utils.workspace import (
    add_membership,
    auth_headers_for_new_user,
    auth_headers_for_role,
    create_workspace,
)

_SCHEMA = {
    "type": "object",
    "properties": {"id": {"type": "string"}},
    "required": ["id"],
}


def _register(
    client: TestClient, headers: dict[str, str], body: dict[str, object]
) -> httpx.Response:
    return client.post(
        f"{settings.API_V1_STR}/tools/register",
        headers=headers,
        json=body,
    )


def _http_body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "name": "delete_customer_account",
        "http_method": "DELETE",
        "url": "https://api.internal.corp/customers/{id}",
        "requires_hitl": False,
        "schema": _SCHEMA,
    }
    body.update(overrides)
    return body


def test_register_http_tool_returns_active_without_calling_the_url(
    client: TestClient, db: Session
) -> None:
    headers, _email, workspace_id = create_workspace(client, db, name="Acme")
    _other_headers, _other_email, other_workspace_id = create_workspace(
        client, db, name="Other"
    )
    response = _register(
        client,
        headers,
        _http_body(workspace_id=other_workspace_id, requires_hitl=True),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "active"
    tool_id = uuid.UUID(body["tool_id"])

    db.expire_all()
    tool = db.get(ToolRegistry, tool_id)
    assert tool is not None
    assert str(tool.workspace_id) == workspace_id
    assert tool.name == "delete_customer_account"
    assert tool.kind == ToolKind.HTTP
    assert tool.http_method == HttpMethod.DELETE
    assert tool.url == "https://api.internal.corp/customers/{id}"
    assert tool.tool_schema == _SCHEMA
    assert tool.requires_hitl is True
    assert tool.is_active is True

    listed = client.get(f"{settings.API_V1_STR}/tools", headers=headers)
    assert listed.status_code == 200
    assert listed.history == []
    assert listed.json()["count"] == 1
    row = listed.json()["data"][0]
    assert row["id"] == str(tool_id)
    assert row["schema"] == _SCHEMA
    assert row["requires_hitl"] is True

    detail = client.get(
        f"{settings.API_V1_STR}/tools/{tool_id}?workspace_id={other_workspace_id}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["schema"]["required"] == ["id"]
    assert detail.json()["is_active"] is True


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_write_methods_force_hitl(client: TestClient, db: Session, method: str) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    created = _register(
        client,
        headers,
        _http_body(
            name=f"write_{method.lower()}", http_method=method, requires_hitl=False
        ),
    )
    assert created.status_code == 201
    tool_id = created.json()["tool_id"]
    detail = client.get(f"{settings.API_V1_STR}/tools/{tool_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["requires_hitl"] is True

    patched = client.patch(
        f"{settings.API_V1_STR}/tools/{tool_id}",
        headers=headers,
        json={"requires_hitl": False, "description": "still a write"},
    )
    assert patched.status_code == 200
    assert patched.json()["requires_hitl"] is True
    assert patched.json()["description"] == "still a write"


def test_get_may_leave_hitl_off_and_patch_relocks_writes(
    client: TestClient, db: Session
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    created = _register(
        client,
        headers,
        _http_body(
            name="fetch_customer",
            http_method="GET",
            requires_hitl=False,
            url="https://api.internal.corp/customers/{id}",
        ),
    )
    assert created.status_code == 201
    tool_id = created.json()["tool_id"]
    assert (
        client.get(f"{settings.API_V1_STR}/tools/{tool_id}", headers=headers).json()[
            "requires_hitl"
        ]
        is False
    )

    optional = client.patch(
        f"{settings.API_V1_STR}/tools/{tool_id}",
        headers=headers,
        json={"requires_hitl": True},
    )
    assert optional.status_code == 200
    assert optional.json()["requires_hitl"] is True

    locked = client.patch(
        f"{settings.API_V1_STR}/tools/{tool_id}",
        headers=headers,
        json={"http_method": "POST", "requires_hitl": False},
    )
    assert locked.status_code == 200
    assert locked.json()["http_method"] == "POST"
    assert locked.json()["requires_hitl"] is True

    unlocked = client.patch(
        f"{settings.API_V1_STR}/tools/{tool_id}",
        headers=headers,
        json={"http_method": "GET", "requires_hitl": False},
    )
    assert unlocked.status_code == 200
    assert unlocked.json()["requires_hitl"] is False


def test_duplicate_name_returns_409(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db, name="Acme")
    other_headers, _other_email, _other_workspace = create_workspace(
        client, db, name="Other"
    )
    first = _register(client, headers, _http_body())
    duplicate = _register(client, headers, _http_body(http_method="POST"))
    elsewhere = _register(client, other_headers, _http_body())
    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "A tool with this name already exists."
    assert elsewhere.status_code == 201

    listed = client.get(f"{settings.API_V1_STR}/tools", headers=headers)
    assert listed.json()["count"] == 1
    assert listed.json()["data"][0]["http_method"] == "DELETE"


def test_viewer_cannot_register_update_or_delete(
    client: TestClient, db: Session
) -> None:
    admin_headers, _email, workspace_id = create_workspace(client, db)
    viewer_headers, _viewer = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.VIEWER
    )
    editor_headers, _editor = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.EDITOR
    )
    created = _register(
        client, editor_headers, _http_body(name="fetch_customer", http_method="GET")
    )
    assert created.status_code == 201
    tool_id = created.json()["tool_id"]

    forbidden = _register(client, viewer_headers, _http_body(name="nope"))
    assert forbidden.status_code == 403
    assert (
        forbidden.json()["detail"] == "Only workspace editors can perform this action"
    )

    listed = client.get(f"{settings.API_V1_STR}/tools", headers=viewer_headers)
    assert listed.status_code == 200
    assert listed.json()["count"] == 1
    detail = client.get(
        f"{settings.API_V1_STR}/tools/{tool_id}", headers=viewer_headers
    )
    assert detail.status_code == 200

    denied_update = client.patch(
        f"{settings.API_V1_STR}/tools/{tool_id}",
        headers=viewer_headers,
        json={"description": "nope"},
    )
    assert denied_update.status_code == 403
    denied_delete = client.delete(
        f"{settings.API_V1_STR}/tools/{tool_id}", headers=viewer_headers
    )
    assert denied_delete.status_code == 403
    assert (
        client.get(
            f"{settings.API_V1_STR}/tools/{tool_id}", headers=admin_headers
        ).json()["description"]
        == ""
    )

    removed = client.delete(
        f"{settings.API_V1_STR}/tools/{tool_id}", headers=editor_headers
    )
    assert removed.status_code == 200
    assert removed.json()["message"] == "Tool deleted successfully"
    assert (
        client.get(
            f"{settings.API_V1_STR}/tools/{tool_id}", headers=admin_headers
        ).status_code
        == 404
    )


def test_tool_is_hidden_outside_the_current_workspace(
    client: TestClient, db: Session
) -> None:
    headers_a, email_a, workspace_a = create_workspace(client, db, name="A")
    headers_b, _email_b, workspace_b = create_workspace(client, db, name="B")
    created = _register(client, headers_b, _http_body(name="refund_user"))
    assert created.status_code == 201
    tool_id = created.json()["tool_id"]

    db.expire_all()
    member = db.exec(select(User).where(User.email == email_a)).one()
    assert str(member.workspace_id) == workspace_a
    add_membership(db, member, workspace_b, WorkspaceRole.EDITOR, set_current=False)
    db.refresh(member)
    assert str(member.workspace_id) == workspace_a
    membership = db.exec(
        select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == member.id,
            WorkspaceMembership.workspace_id == uuid.UUID(workspace_b),
        )
    ).one()
    assert membership.role == WorkspaceRole.EDITOR

    listed = client.get(
        f"{settings.API_V1_STR}/tools?workspace_id={workspace_b}", headers=headers_a
    )
    assert listed.status_code == 200
    assert listed.json()["data"] == []
    assert listed.json()["count"] == 0

    hidden = client.get(f"{settings.API_V1_STR}/tools/{tool_id}", headers=headers_a)
    assert hidden.status_code == 404
    assert hidden.json()["detail"] == "Tool not found"
    missed = client.patch(
        f"{settings.API_V1_STR}/tools/{tool_id}",
        headers=headers_a,
        json={"description": "stolen"},
    )
    assert missed.status_code == 404
    denied = client.delete(f"{settings.API_V1_STR}/tools/{tool_id}", headers=headers_a)
    assert denied.status_code == 404

    owner = client.get(f"{settings.API_V1_STR}/tools/{tool_id}", headers=headers_b)
    assert owner.status_code == 200
    assert owner.json()["description"] == ""


def test_js_tool_stores_name_and_schema_only(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    created = _register(
        client,
        headers,
        {
            "name": "open_checkout",
            "kind": "js",
            "requires_hitl": True,
            "schema": {"type": "object", "properties": {"sku": {"type": "string"}}},
        },
    )
    assert created.status_code == 201
    tool_id = uuid.UUID(created.json()["tool_id"])
    db.expire_all()
    tool = db.get(ToolRegistry, tool_id)
    assert tool is not None
    assert tool.kind == ToolKind.JS
    assert tool.http_method is None
    assert tool.url is None
    assert tool.requires_hitl is True
    assert tool.tool_schema["properties"]["sku"]["type"] == "string"

    inferred = _register(
        client,
        headers,
        {"name": "close_checkout", "schema": _SCHEMA},
    )
    assert inferred.status_code == 201
    db.expire_all()
    inferred_tool = db.get(ToolRegistry, uuid.UUID(inferred.json()["tool_id"]))
    assert inferred_tool is not None
    assert inferred_tool.kind == ToolKind.JS
    assert inferred_tool.url is None
    assert inferred_tool.http_method is None

    denied = client.patch(
        f"{settings.API_V1_STR}/tools/{tool_id}",
        headers=headers,
        json={"url": "https://example.com/hook"},
    )
    assert denied.status_code == 422
    assert denied.json()["detail"] == (
        "JS tools are registered with a name and schema only."
    )

    with_url = _register(
        client,
        headers,
        {
            "name": "open_modal",
            "kind": "js",
            "url": "https://example.com",
            "schema": _SCHEMA,
        },
    )
    assert with_url.status_code == 422
    assert with_url.json()["detail"] == (
        "JS tools are registered with a name and schema only."
    )


def test_register_rejects_invalid_name_schema_and_url(
    client: TestClient, db: Session
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    cases: list[tuple[dict[str, object], str]] = [
        (_http_body(name="Cancel Subscription"), "snake_case"),
        (
            _http_body(name="lookup", schema={"type": "object"}),
            "type and properties",
        ),
        (
            _http_body(name="lookup", schema={"type": "string", "properties": {}}),
            "type and properties",
        ),
        (
            _http_body(name="lookup", url="http://example.com/customers"),
            "HTTPS",
        ),
        (
            _http_body(name="lookup", http_method="GET", url=None),
            "HTTP method and URL",
        ),
    ]
    for body, fragment in cases:
        response = _register(client, headers, body)
        assert response.status_code == 422
        assert fragment in response.json()["detail"]

    localhost = _register(
        client,
        headers,
        _http_body(
            name="local_probe",
            http_method="GET",
            url="http://127.0.0.1:9/not-listening",
            requires_hitl=False,
        ),
    )
    assert localhost.status_code == 201
    stored = client.get(
        f"{settings.API_V1_STR}/tools/{localhost.json()['tool_id']}",
        headers=headers,
    )
    assert stored.json()["url"] == "http://127.0.0.1:9/not-listening"
    assert stored.json()["requires_hitl"] is False

    listed = client.get(f"{settings.API_V1_STR}/tools", headers=headers)
    assert listed.json()["count"] == 1


def test_patch_edits_schema_url_and_description(
    client: TestClient, db: Session
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    created = _register(
        client,
        headers,
        _http_body(name="fetch_customer", http_method="GET", requires_hitl=False),
    )
    tool_id = created.json()["tool_id"]
    updated_schema = {
        "type": "object",
        "properties": {"email": {"type": "string"}},
    }
    patched = client.patch(
        f"{settings.API_V1_STR}/tools/{tool_id}",
        headers=headers,
        json={
            "schema": updated_schema,
            "url": "http://localhost:8080/customers/{id}",
            "description": "Look up a customer",
        },
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["schema"] == updated_schema
    assert body["url"] == "http://localhost:8080/customers/{id}"
    assert body["description"] == "Look up a customer"
    assert body["name"] == "fetch_customer"
    assert body["requires_hitl"] is False

    rejected = client.patch(
        f"{settings.API_V1_STR}/tools/{tool_id}",
        headers=headers,
        json={"url": "http://example.com/customers"},
    )
    assert rejected.status_code == 422
    unchanged = client.get(f"{settings.API_V1_STR}/tools/{tool_id}", headers=headers)
    assert unchanged.json()["url"] == "http://localhost:8080/customers/{id}"


def test_delete_removes_the_row(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    created = _register(client, headers, _http_body(name="remove_me"))
    tool_id = uuid.UUID(created.json()["tool_id"])
    removed = client.delete(f"{settings.API_V1_STR}/tools/{tool_id}", headers=headers)
    assert removed.status_code == 200
    db.expire_all()
    assert db.get(ToolRegistry, tool_id) is None
    assert (
        client.get(
            f"{settings.API_V1_STR}/tools/{tool_id}", headers=headers
        ).status_code
        == 404
    )


def test_register_requires_a_workspace(client: TestClient, db: Session) -> None:
    headers, _email = auth_headers_for_new_user(client, db)
    response = _register(client, headers, _http_body())
    assert response.status_code == 403
    assert response.json()["detail"] == "User is not a member of a workspace"


def test_missing_tool_is_404(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    missing = client.get(f"{settings.API_V1_STR}/tools/{uuid.uuid4()}", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Tool not found"
