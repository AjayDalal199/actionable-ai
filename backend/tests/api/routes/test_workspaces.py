import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import UserCreate, WorkspaceRole
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


def _auth_headers_for_new_user(
    client: TestClient, db: Session
) -> tuple[dict[str, str], str]:
    email = random_email()
    password = random_lower_string()
    crud.create_user(session=db, user_create=UserCreate(email=email, password=password))
    return (
        user_authentication_headers(client=client, email=email, password=password),
        email,
    )


def test_create_workspace(client: TestClient, db: Session) -> None:
    headers, email = _auth_headers_for_new_user(client, db)
    r = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=headers,
        json={"name": "Acme Corp"},
    )
    assert r.status_code == 200
    content = r.json()
    assert content["name"] == "Acme Corp"
    assert "id" in content

    me = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["id"] == content["id"]
    assert me.json()["name"] == "Acme Corp"

    db.expire_all()
    user = crud.get_user_by_email(session=db, email=email)
    assert user is not None
    assert str(user.workspace_id) == content["id"]
    assert user.role == WorkspaceRole.ADMIN


def test_create_workspace_strips_name(client: TestClient, db: Session) -> None:
    headers, _email = _auth_headers_for_new_user(client, db)
    r = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=headers,
        json={"name": "  Acme Corp  "},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Acme Corp"


def test_create_workspace_blank_name_is_422(client: TestClient, db: Session) -> None:
    headers, _email = _auth_headers_for_new_user(client, db)
    r = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=headers,
        json={"name": "   "},
    )
    assert r.status_code == 422


def test_create_workspace_conflict_if_already_member(
    client: TestClient, db: Session
) -> None:
    headers, _email = _auth_headers_for_new_user(client, db)
    first = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=headers,
        json={"name": "Acme"},
    )
    assert first.status_code == 200
    second = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=headers,
        json={"name": "Other"},
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "User already belongs to a workspace"


def test_read_workspace_me_forbidden_without_membership(
    client: TestClient, db: Session
) -> None:
    headers, _email = _auth_headers_for_new_user(client, db)
    r = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=headers)
    assert r.status_code == 403
    assert r.json()["detail"] == "User is not a member of a workspace"


def test_read_workspace_me_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/workspaces/me", headers=superuser_token_headers
    )
    assert r.status_code == 200
    assert r.json()["name"]
    assert "id" in r.json()


def _create_workspace(
    client: TestClient, db: Session
) -> tuple[dict[str, str], str, str]:
    headers, email = _auth_headers_for_new_user(client, db)
    r = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=headers,
        json={"name": "Acme"},
    )
    assert r.status_code == 200
    return headers, email, r.json()["id"]


def _auth_headers_for_role(
    client: TestClient,
    db: Session,
    workspace_id: str,
    role: WorkspaceRole,
) -> dict[str, str]:
    email = random_email()
    password = random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )
    user.workspace_id = uuid.UUID(workspace_id)
    user.role = role
    db.add(user)
    db.commit()
    return user_authentication_headers(client=client, email=email, password=password)


def test_rename_workspace_as_admin(client: TestClient, db: Session) -> None:
    headers, _email, workspace_id = _create_workspace(client, db)
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=headers,
        json={"name": "Acme Corp"},
    )
    assert r.status_code == 200
    assert r.json()["id"] == workspace_id
    assert r.json()["name"] == "Acme Corp"

    me = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=headers)
    assert me.json()["name"] == "Acme Corp"


def test_rename_workspace_strips_name(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = _create_workspace(client, db)
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=headers,
        json={"name": "  New Name  "},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"


def test_rename_workspace_blank_name_is_422(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = _create_workspace(client, db)
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=headers,
        json={"name": "   "},
    )
    assert r.status_code == 422


def test_rename_workspace_forbidden_for_editor(client: TestClient, db: Session) -> None:
    _admin_headers, _email, workspace_id = _create_workspace(client, db)
    editor_headers = _auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.EDITOR
    )
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=editor_headers,
        json={"name": "Nope"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Only workspace admins can rename the workspace"

    me = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=editor_headers)
    assert me.json()["name"] == "Acme"


def test_rename_workspace_forbidden_for_viewer(client: TestClient, db: Session) -> None:
    _admin_headers, _email, workspace_id = _create_workspace(client, db)
    viewer_headers = _auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.VIEWER
    )
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=viewer_headers,
        json={"name": "Nope"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Only workspace admins can rename the workspace"


def test_rename_workspace_forbidden_without_membership(
    client: TestClient, db: Session
) -> None:
    headers, _email = _auth_headers_for_new_user(client, db)
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=headers,
        json={"name": "Nope"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "User is not a member of a workspace"
