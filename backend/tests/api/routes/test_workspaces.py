import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import InvitationStatus, UserCreate, WorkspaceRole
from app.services.workspaces import get_membership
from app.utils import generate_workspace_invite_token
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string
from tests.utils.workspace import (
    accept_invite,
    auth_headers_for_new_user,
    auth_headers_for_role,
    create_workspace,
)


def test_create_workspace(client: TestClient, db: Session) -> None:
    headers, email = auth_headers_for_new_user(client, db)
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
    membership = get_membership(
        session=db, user_id=user.id, workspace_id=uuid.UUID(content["id"])
    )
    assert membership is not None
    assert membership.role == WorkspaceRole.ADMIN
    assert membership.invitation_status == InvitationStatus.ACCEPTED


def test_create_workspace_strips_name(client: TestClient, db: Session) -> None:
    headers, _email = auth_headers_for_new_user(client, db)
    r = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=headers,
        json={"name": "  Acme Corp  "},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Acme Corp"


def test_create_workspace_blank_name_is_422(client: TestClient, db: Session) -> None:
    headers, _email = auth_headers_for_new_user(client, db)
    r = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=headers,
        json={"name": "   "},
    )
    assert r.status_code == 422


def test_create_workspace_conflict_if_already_created(
    client: TestClient, db: Session
) -> None:
    headers, _email = auth_headers_for_new_user(client, db)
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
    assert second.json()["detail"] == "User has already created a workspace"


def test_read_workspace_me_forbidden_without_membership(
    client: TestClient, db: Session
) -> None:
    headers, _email = auth_headers_for_new_user(client, db)
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


def test_rename_workspace_as_admin(client: TestClient, db: Session) -> None:
    headers, _email, workspace_id = create_workspace(client, db)
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
    headers, _email, _workspace_id = create_workspace(client, db)
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=headers,
        json={"name": "  New Name  "},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"


def test_rename_workspace_blank_name_is_422(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=headers,
        json={"name": "   "},
    )
    assert r.status_code == 422


def test_rename_workspace_forbidden_for_editor(client: TestClient, db: Session) -> None:
    _admin_headers, _email, workspace_id = create_workspace(client, db)
    editor_headers, _editor_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.EDITOR
    )
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=editor_headers,
        json={"name": "Nope"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Only workspace admins can perform this action"

    me = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=editor_headers)
    assert me.json()["name"] == "Acme"


def test_rename_workspace_forbidden_for_viewer(client: TestClient, db: Session) -> None:
    _admin_headers, _email, workspace_id = create_workspace(client, db)
    viewer_headers, _viewer_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.VIEWER
    )
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=viewer_headers,
        json={"name": "Nope"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Only workspace admins can perform this action"


def test_rename_workspace_forbidden_without_membership(
    client: TestClient, db: Session
) -> None:
    headers, _email = auth_headers_for_new_user(client, db)
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me",
        headers=headers,
        json={"name": "Nope"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "User is not a member of a workspace"


def test_list_workspace_members(client: TestClient, db: Session) -> None:
    admin_headers, admin_email, workspace_id = create_workspace(client, db)
    _editor_headers, editor_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.EDITOR
    )
    r = client.get(
        f"{settings.API_V1_STR}/workspaces/me/members", headers=admin_headers
    )
    assert r.status_code == 200
    content = r.json()
    assert content["count"] == 2
    emails = {member["email"] for member in content["data"]}
    assert emails == {admin_email, editor_email}
    roles = {member["email"]: member["role"] for member in content["data"]}
    assert roles[admin_email] == WorkspaceRole.ADMIN
    assert roles[editor_email] == WorkspaceRole.EDITOR
    assert "is_superuser" not in content["data"][0]


def test_list_workspace_members_as_viewer(client: TestClient, db: Session) -> None:
    _admin_headers, _email, workspace_id = create_workspace(client, db)
    viewer_headers, _viewer_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.VIEWER
    )
    r = client.get(
        f"{settings.API_V1_STR}/workspaces/me/members", headers=viewer_headers
    )
    assert r.status_code == 200
    assert r.json()["count"] == 2


def test_list_workspace_members_is_tenant_scoped(
    client: TestClient, db: Session
) -> None:
    headers_a, email_a, _workspace_a = create_workspace(client, db, name="A")
    headers_b, email_b, _workspace_b = create_workspace(client, db, name="B")

    list_a = client.get(
        f"{settings.API_V1_STR}/workspaces/me/members", headers=headers_a
    )
    list_b = client.get(
        f"{settings.API_V1_STR}/workspaces/me/members", headers=headers_b
    )
    emails_a = {member["email"] for member in list_a.json()["data"]}
    emails_b = {member["email"] for member in list_b.json()["data"]}
    assert emails_a == {email_a}
    assert emails_b == {email_b}


def test_invite_new_user_is_pending_until_accepted(
    client: TestClient, db: Session
) -> None:
    headers, _email, workspace_id = create_workspace(client, db)
    invited_email = random_email()
    with (
        patch("app.api.routes.workspaces.send_email", return_value=None),
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.EMAILS_FROM_EMAIL", "noreply@example.com"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/me/members",
            headers=headers,
            json={"email": invited_email, "role": "editor", "full_name": "Sam Editor"},
        )
    assert r.status_code == 201
    content = r.json()
    assert content["email"] == invited_email
    assert content["role"] == WorkspaceRole.EDITOR
    assert content["full_name"] == "Sam Editor"
    assert content["is_active"] is True
    assert content["invitation_status"] == InvitationStatus.PENDING

    user = crud.get_user_by_email(session=db, email=invited_email)
    assert user is not None
    assert user.workspace_id is None
    membership = get_membership(
        session=db, user_id=user.id, workspace_id=uuid.UUID(workspace_id)
    )
    assert membership is not None
    assert membership.role == WorkspaceRole.EDITOR
    assert membership.invitation_status == InvitationStatus.PENDING
    assert user.is_superuser is False
    assert user.must_set_password is True

    new_password = random_lower_string()
    accept_invite(client, invited_email, workspace_id, password=new_password)
    db.refresh(user)
    db.refresh(membership)
    assert user.workspace_id is not None
    assert str(user.workspace_id) == workspace_id
    assert membership.invitation_status == InvitationStatus.ACCEPTED
    assert user.must_set_password is False

    invited_headers = user_authentication_headers(
        client=client, email=invited_email, password=new_password
    )
    me = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=invited_headers)
    assert me.status_code == 200
    assert me.json()["id"] == workspace_id


def test_invite_sends_invite_email_when_enabled(
    client: TestClient, db: Session
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    invited_email = random_email()
    with (
        patch("app.api.routes.workspaces.send_email") as mock_send,
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.EMAILS_FROM_EMAIL", "noreply@example.com"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/me/members",
            headers=headers,
            json={"email": invited_email, "role": "viewer"},
        )
        assert r.status_code == 201
        mock_send.assert_called_once()
        assert mock_send.call_args.kwargs["email_to"] == invited_email
        assert "invited to" in mock_send.call_args.kwargs["subject"]
        assert "join-workspace?token=" in mock_send.call_args.kwargs["html_content"]


def test_invite_existing_user_sends_invite_email(
    client: TestClient, db: Session
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    existing_email = random_email()
    crud.create_user(
        session=db,
        user_create=UserCreate(email=existing_email, password=random_lower_string()),
    )
    with (
        patch("app.api.routes.workspaces.send_email") as mock_send,
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.EMAILS_FROM_EMAIL", "noreply@example.com"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/me/members",
            headers=headers,
            json={"email": existing_email, "role": "viewer"},
        )
        assert r.status_code == 201
        mock_send.assert_called_once()
        assert mock_send.call_args.kwargs["email_to"] == existing_email
        assert "invited to" in mock_send.call_args.kwargs["subject"]


def test_invite_existing_user_without_workspace(
    client: TestClient, db: Session
) -> None:
    headers, _email, workspace_id = create_workspace(client, db)
    existing_email = random_email()
    password = random_lower_string()
    crud.create_user(
        session=db, user_create=UserCreate(email=existing_email, password=password)
    )
    with patch("app.api.routes.workspaces.send_email"):
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/me/members",
            headers=headers,
            json={"email": existing_email, "role": "viewer"},
        )
    assert r.status_code == 201
    assert r.json()["role"] == WorkspaceRole.VIEWER
    assert r.json()["invitation_status"] == InvitationStatus.PENDING

    invited_headers = user_authentication_headers(
        client=client, email=existing_email, password=password
    )
    me = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=invited_headers)
    assert me.status_code == 403

    accept_invite(client, existing_email, workspace_id)
    me = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=invited_headers)
    assert me.json()["id"] == workspace_id


def test_invite_conflict_if_already_member(client: TestClient, db: Session) -> None:
    headers, _email, workspace_id = create_workspace(client, db)
    _editor_headers, editor_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.EDITOR
    )
    r = client.post(
        f"{settings.API_V1_STR}/workspaces/me/members",
        headers=headers,
        json={"email": editor_email, "role": "viewer"},
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User is already a member of this workspace"


def test_invite_user_who_already_has_a_workspace(
    client: TestClient, db: Session
) -> None:
    headers_a, email_a, workspace_a = create_workspace(client, db, name="A")
    headers_b, email_b, workspace_b = create_workspace(client, db, name="B")
    with patch("app.api.routes.workspaces.send_email"):
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/me/members",
            headers=headers_a,
            json={"email": email_b, "role": "editor"},
        )
    assert r.status_code == 201
    assert r.json()["role"] == WorkspaceRole.EDITOR
    assert r.json()["invitation_status"] == InvitationStatus.PENDING

    me_b = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=headers_b)
    assert me_b.json()["id"] == workspace_b

    listed_before = client.get(f"{settings.API_V1_STR}/workspaces/", headers=headers_b)
    assert listed_before.json()["count"] == 1

    accept_invite(client, email_b, workspace_a)

    list_a = client.get(
        f"{settings.API_V1_STR}/workspaces/me/members", headers=headers_a
    )
    emails_a = {member["email"] for member in list_a.json()["data"]}
    assert emails_a == {email_a, email_b}
    member_b = next(
        member for member in list_a.json()["data"] if member["email"] == email_b
    )
    assert member_b["invitation_status"] == InvitationStatus.ACCEPTED

    listed = client.get(f"{settings.API_V1_STR}/workspaces/", headers=headers_b)
    assert listed.status_code == 200
    content = listed.json()
    assert content["count"] == 2
    assert content["can_create"] is False
    ids = {item["id"] for item in content["data"]}
    assert ids == {workspace_a, workspace_b}
    current = next(item for item in content["data"] if item["is_current"])
    assert current["id"] == workspace_b

    switched = client.put(
        f"{settings.API_V1_STR}/workspaces/current",
        headers=headers_b,
        json={"workspace_id": workspace_a},
    )
    assert switched.status_code == 200
    assert switched.json()["id"] == workspace_a
    me_switched = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=headers_b)
    assert me_switched.json()["id"] == workspace_a


def test_invite_forbidden_for_editor(client: TestClient, db: Session) -> None:
    _admin_headers, _email, workspace_id = create_workspace(client, db)
    editor_headers, _editor_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.EDITOR
    )
    r = client.post(
        f"{settings.API_V1_STR}/workspaces/me/members",
        headers=editor_headers,
        json={"email": random_email(), "role": "viewer"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Only workspace admins can perform this action"


def test_update_member_role(client: TestClient, db: Session) -> None:
    headers, _email, workspace_id = create_workspace(client, db)
    _editor_headers, editor_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.EDITOR
    )
    editor = crud.get_user_by_email(session=db, email=editor_email)
    assert editor is not None
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me/members/{editor.id}",
        headers=headers,
        json={"role": "viewer"},
    )
    assert r.status_code == 200
    assert r.json()["role"] == WorkspaceRole.VIEWER
    membership = get_membership(
        session=db, user_id=editor.id, workspace_id=uuid.UUID(workspace_id)
    )
    assert membership is not None
    assert membership.role == WorkspaceRole.VIEWER


def test_deactivate_member(client: TestClient, db: Session) -> None:
    headers, _email, workspace_id = create_workspace(client, db)
    editor_headers, editor_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.EDITOR
    )
    editor = crud.get_user_by_email(session=db, email=editor_email)
    assert editor is not None
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me/members/{editor.id}",
        headers=headers,
        json={"is_active": False},
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    me = client.get(f"{settings.API_V1_STR}/users/me", headers=editor_headers)
    assert me.status_code == 200
    assert me.json()["email"] == editor_email
    assert me.json()["workspace_id"] is None

    blocked = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=editor_headers)
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "User is not a member of a workspace"
    membership = get_membership(
        session=db, user_id=editor.id, workspace_id=uuid.UUID(workspace_id)
    )
    assert membership is not None
    assert membership.is_active is False


def test_invite_reactivates_deactivated_member(client: TestClient, db: Session) -> None:
    headers, _email, workspace_id = create_workspace(client, db)
    editor_headers, editor_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.EDITOR
    )
    editor = crud.get_user_by_email(session=db, email=editor_email)
    assert editor is not None
    deactivate = client.patch(
        f"{settings.API_V1_STR}/workspaces/me/members/{editor.id}",
        headers=headers,
        json={"is_active": False},
    )
    assert deactivate.status_code == 200
    with patch("app.api.routes.workspaces.send_email"):
        r = client.post(
            f"{settings.API_V1_STR}/workspaces/me/members",
            headers=headers,
            json={"email": editor_email, "role": "viewer"},
        )
    assert r.status_code == 201
    assert r.json()["role"] == WorkspaceRole.VIEWER
    assert r.json()["is_active"] is True
    me = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=editor_headers)
    assert me.status_code == 200
    assert me.json()["id"] == workspace_id


def test_cannot_demote_last_admin(client: TestClient, db: Session) -> None:
    headers, admin_email, _workspace_id = create_workspace(client, db)
    admin = crud.get_user_by_email(session=db, email=admin_email)
    assert admin is not None
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me/members/{admin.id}",
        headers=headers,
        json={"role": "editor"},
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "Cannot demote or deactivate the last admin"
    assert admin.workspace_id is not None
    membership = get_membership(
        session=db, user_id=admin.id, workspace_id=admin.workspace_id
    )
    assert membership is not None
    assert membership.role == WorkspaceRole.ADMIN


def test_cannot_deactivate_last_admin(client: TestClient, db: Session) -> None:
    headers, admin_email, _workspace_id = create_workspace(client, db)
    admin = crud.get_user_by_email(session=db, email=admin_email)
    assert admin is not None
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me/members/{admin.id}",
        headers=headers,
        json={"is_active": False},
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "Cannot demote or deactivate the last admin"


def test_update_member_not_found_in_other_workspace(
    client: TestClient, db: Session
) -> None:
    headers_a, _email_a, _workspace_a = create_workspace(client, db, name="A")
    _headers_b, email_b, _workspace_b = create_workspace(client, db, name="B")
    user_b = crud.get_user_by_email(session=db, email=email_b)
    assert user_b is not None
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me/members/{user_b.id}",
        headers=headers_a,
        json={"role": "viewer"},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Member not found"
    assert user_b.workspace_id is not None
    membership = get_membership(
        session=db, user_id=user_b.id, workspace_id=user_b.workspace_id
    )
    assert membership is not None
    assert membership.role == WorkspaceRole.ADMIN


def test_update_member_forbidden_for_editor(client: TestClient, db: Session) -> None:
    _admin_headers, admin_email, workspace_id = create_workspace(client, db)
    editor_headers, _editor_email = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.EDITOR
    )
    admin = crud.get_user_by_email(session=db, email=admin_email)
    assert admin is not None
    r = client.patch(
        f"{settings.API_V1_STR}/workspaces/me/members/{admin.id}",
        headers=editor_headers,
        json={"role": "viewer"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Only workspace admins can perform this action"


def test_invite_invalid_role_is_422(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    r = client.post(
        f"{settings.API_V1_STR}/workspaces/me/members",
        headers=headers,
        json={"email": random_email(), "role": "owner"},
    )
    assert r.status_code == 422


def test_list_workspaces_empty_can_create(client: TestClient, db: Session) -> None:
    headers, _email = auth_headers_for_new_user(client, db)
    r = client.get(f"{settings.API_V1_STR}/workspaces/", headers=headers)
    assert r.status_code == 200
    assert r.json() == {"data": [], "count": 0, "can_create": True}


def test_list_workspaces_after_create(client: TestClient, db: Session) -> None:
    headers, _email, workspace_id = create_workspace(client, db)
    r = client.get(f"{settings.API_V1_STR}/workspaces/", headers=headers)
    assert r.status_code == 200
    content = r.json()
    assert content["count"] == 1
    assert content["can_create"] is False
    assert content["data"][0]["id"] == workspace_id
    assert content["data"][0]["is_current"] is True
    assert content["data"][0]["role"] == WorkspaceRole.ADMIN


def test_invited_user_can_create_own_workspace(client: TestClient, db: Session) -> None:
    admin_headers, _admin_email, invited_workspace_id = create_workspace(client, db)
    headers, email = auth_headers_for_new_user(client, db)
    with patch("app.api.routes.workspaces.send_email"):
        invite = client.post(
            f"{settings.API_V1_STR}/workspaces/me/members",
            headers=admin_headers,
            json={"email": email, "role": "editor"},
        )
    assert invite.status_code == 201

    listed = client.get(f"{settings.API_V1_STR}/workspaces/", headers=headers)
    assert listed.json()["can_create"] is True
    assert listed.json()["count"] == 0

    created = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=headers,
        json={"name": "Mine"},
    )
    assert created.status_code == 200
    own_id = created.json()["id"]
    assert own_id != invited_workspace_id

    me = client.get(f"{settings.API_V1_STR}/workspaces/me", headers=headers)
    assert me.json()["id"] == own_id

    listed_after = client.get(f"{settings.API_V1_STR}/workspaces/", headers=headers)
    assert listed_after.json()["count"] == 1
    assert listed_after.json()["can_create"] is False


def test_decline_invite_and_reinvite(client: TestClient, db: Session) -> None:
    headers, _email, workspace_id = create_workspace(client, db)
    existing_email = random_email()
    password = random_lower_string()
    crud.create_user(
        session=db, user_create=UserCreate(email=existing_email, password=password)
    )
    with patch("app.api.routes.workspaces.send_email"):
        invited = client.post(
            f"{settings.API_V1_STR}/workspaces/me/members",
            headers=headers,
            json={"email": existing_email, "role": "viewer"},
        )
    assert invited.status_code == 201

    invite_token = generate_workspace_invite_token(
        email=existing_email, workspace_id=uuid.UUID(workspace_id)
    )
    preview = client.get(
        f"{settings.API_V1_STR}/workspaces/invites",
        params={"token": invite_token},
    )
    assert preview.status_code == 200
    assert preview.json()["status"] == InvitationStatus.PENDING
    assert preview.json()["needs_password"] is False

    declined = client.post(
        f"{settings.API_V1_STR}/workspaces/invites/decline",
        json={"token": invite_token},
    )
    assert declined.status_code == 200
    assert declined.json()["invitation_status"] == InvitationStatus.DECLINED

    listed = client.get(f"{settings.API_V1_STR}/workspaces/me/members", headers=headers)
    member = next(
        item for item in listed.json()["data"] if item["email"] == existing_email
    )
    assert member["invitation_status"] == InvitationStatus.DECLINED

    with patch("app.api.routes.workspaces.send_email"):
        reinvite = client.post(
            f"{settings.API_V1_STR}/workspaces/me/members",
            headers=headers,
            json={"email": existing_email, "role": "editor"},
        )
    assert reinvite.status_code == 201
    assert reinvite.json()["invitation_status"] == InvitationStatus.PENDING
    assert reinvite.json()["role"] == WorkspaceRole.EDITOR


def test_select_current_workspace_rejects_non_member(
    client: TestClient, db: Session
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    _other_headers, _other_email, other_workspace_id = create_workspace(
        client, db, name="Other"
    )
    r = client.put(
        f"{settings.API_V1_STR}/workspaces/current",
        headers=headers,
        json={"workspace_id": other_workspace_id},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "User is not a member of a workspace"
