import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import WorkspaceRole
from tests.utils.item import create_random_item
from tests.utils.workspace import (
    accept_invite,
    auth_headers_for_new_user,
    auth_headers_for_role,
    create_workspace,
)


def test_create_item(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    data = {"title": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content


def test_create_item_forbidden_for_viewer(client: TestClient, db: Session) -> None:
    _admin_headers, _email, workspace_id = create_workspace(client, db)
    viewer_headers, _viewer_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.VIEWER
    )
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=viewer_headers,
        json={"title": "Nope", "description": "Nope"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Only workspace editors can perform this action"


def test_create_item_forbidden_without_workspace(
    client: TestClient, db: Session
) -> None:
    headers, _email = auth_headers_for_new_user(client, db)
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers,
        json={"title": "Nope", "description": "Nope"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "User is not a member of a workspace"


def test_read_item(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    created = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers,
        json={"title": "Foo", "description": "Fighters"},
    )
    item_id = created.json()["id"]
    response = client.get(
        f"{settings.API_V1_STR}/items/{item_id}",
        headers=headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == "Foo"
    assert content["id"] == item_id


def test_read_item_as_viewer(client: TestClient, db: Session) -> None:
    admin_headers, _email, workspace_id = create_workspace(client, db)
    created = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=admin_headers,
        json={"title": "Shared", "description": "Doc"},
    )
    viewer_headers, _viewer_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.VIEWER
    )
    response = client.get(
        f"{settings.API_V1_STR}/items/{created.json()['id']}",
        headers=viewer_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Shared"


def test_read_item_not_found(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_read_item_hidden_across_workspaces(client: TestClient, db: Session) -> None:
    headers_a, _email_a, _workspace_a = create_workspace(client, db, name="A")
    headers_b, _email_b, _workspace_b = create_workspace(client, db, name="B")
    created = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers_a,
        json={"title": "Secret", "description": "A only"},
    )
    response = client.get(
        f"{settings.API_V1_STR}/items/{created.json()['id']}",
        headers=headers_b,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_read_item_hidden_across_workspaces_even_if_owner_is_a_member(
    client: TestClient, db: Session
) -> None:
    headers_a, _email_a, workspace_a = create_workspace(client, db, name="A")
    headers_b, email_b, _workspace_b = create_workspace(client, db, name="B")
    created = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers_b,
        json={"title": "B secret", "description": "B only"},
    )
    item_id = created.json()["id"]
    with patch("app.api.routes.workspaces.send_email"):
        invite = client.post(
            f"{settings.API_V1_STR}/workspaces/me/members",
            headers=headers_a,
            json={"email": email_b, "role": "editor"},
        )
    assert invite.status_code == 201
    accept_invite(client, email_b, workspace_a)

    list_a = client.get(f"{settings.API_V1_STR}/items/", headers=headers_a)
    titles_a = {item["title"] for item in list_a.json()["data"]}
    assert "B secret" not in titles_a
    assert (
        client.get(
            f"{settings.API_V1_STR}/items/{item_id}", headers=headers_a
        ).status_code
        == 404
    )
    assert (
        client.put(
            f"{settings.API_V1_STR}/items/{item_id}",
            headers=headers_a,
            json={"title": "Hacked"},
        ).status_code
        == 404
    )

    switched = client.put(
        f"{settings.API_V1_STR}/workspaces/current",
        headers=headers_b,
        json={"workspace_id": workspace_a},
    )
    assert switched.status_code == 200
    list_b_in_a = client.get(f"{settings.API_V1_STR}/items/", headers=headers_b)
    titles_b_in_a = {item["title"] for item in list_b_in_a.json()["data"]}
    assert "B secret" not in titles_b_in_a
    assert (
        client.get(
            f"{settings.API_V1_STR}/items/{item_id}", headers=headers_b
        ).status_code
        == 404
    )


def test_read_item_hidden_when_created_in_another_workspace(
    client: TestClient, db: Session
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    other_headers, _other_email, other_workspace_id = create_workspace(
        client, db, name="Other"
    )
    item = create_random_item(db, uuid.UUID(other_workspace_id))
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_read_items_workspace_scoped(client: TestClient, db: Session) -> None:
    headers_a, _email_a, _workspace_a = create_workspace(client, db, name="A")
    headers_b, _email_b, _workspace_b = create_workspace(client, db, name="B")
    client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers_a,
        json={"title": "A1", "description": "A"},
    )
    client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers_b,
        json={"title": "B1", "description": "B"},
    )
    list_a = client.get(f"{settings.API_V1_STR}/items/", headers=headers_a)
    list_b = client.get(f"{settings.API_V1_STR}/items/", headers=headers_b)
    titles_a = {item["title"] for item in list_a.json()["data"]}
    titles_b = {item["title"] for item in list_b.json()["data"]}
    assert "A1" in titles_a
    assert "B1" not in titles_a
    assert "B1" in titles_b
    assert "A1" not in titles_b


def test_update_item(client: TestClient, db: Session) -> None:
    headers, _email, workspace_id = create_workspace(client, db)
    created = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers,
        json={"title": "Foo", "description": "Bar"},
    )
    editor_headers, _editor_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.EDITOR
    )
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{created.json()['id']}",
        headers=editor_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]


def test_update_item_not_found(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    response = client.put(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=headers,
        json={"title": "Updated title", "description": "Updated description"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_update_item_forbidden_for_viewer(client: TestClient, db: Session) -> None:
    admin_headers, _email, workspace_id = create_workspace(client, db)
    created = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=admin_headers,
        json={"title": "Foo", "description": "Bar"},
    )
    viewer_headers, _viewer_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.VIEWER
    )
    response = client.put(
        f"{settings.API_V1_STR}/items/{created.json()['id']}",
        headers=viewer_headers,
        json={"title": "Nope", "description": "Nope"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Only workspace editors can perform this action"


def test_delete_item(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    created = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers,
        json={"title": "Foo", "description": "Bar"},
    )
    response = client.delete(
        f"{settings.API_V1_STR}/items/{created.json()['id']}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Item deleted successfully"


def test_delete_item_not_found(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_delete_item_forbidden_for_viewer(client: TestClient, db: Session) -> None:
    admin_headers, _email, workspace_id = create_workspace(client, db)
    created = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=admin_headers,
        json={"title": "Foo", "description": "Bar"},
    )
    viewer_headers, _viewer_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.VIEWER
    )
    response = client.delete(
        f"{settings.API_V1_STR}/items/{created.json()['id']}",
        headers=viewer_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Only workspace editors can perform this action"


def test_superuser_does_not_bypass_workspace_scope(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    created = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers,
        json={"title": "Tenant secret", "description": "Not for ops admin"},
    )
    response = client.get(
        f"{settings.API_V1_STR}/items/{created.json()['id']}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"
