import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, WorkspaceMembership, WorkspaceRole
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


def auth_headers_for_new_user(
    client: TestClient, db: Session
) -> tuple[dict[str, str], str]:
    email = random_email()
    password = random_lower_string()
    crud.create_user(session=db, user_create=UserCreate(email=email, password=password))
    return (
        user_authentication_headers(client=client, email=email, password=password),
        email,
    )


def create_workspace(
    client: TestClient, db: Session, name: str = "Acme"
) -> tuple[dict[str, str], str, str]:
    headers, email = auth_headers_for_new_user(client, db)
    r = client.post(
        f"{settings.API_V1_STR}/workspaces/",
        headers=headers,
        json={"name": name},
    )
    assert r.status_code == 200
    return headers, email, r.json()["id"]


def add_membership(
    db: Session,
    user: User,
    workspace_id: str | uuid.UUID,
    role: WorkspaceRole,
    *,
    set_current: bool = True,
) -> WorkspaceMembership:
    membership = WorkspaceMembership(
        user_id=user.id,
        workspace_id=uuid.UUID(str(workspace_id)),
        role=role,
        is_active=True,
    )
    if set_current:
        user.workspace_id = membership.workspace_id
        db.add(user)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def auth_headers_for_role(
    client: TestClient,
    db: Session,
    workspace_id: str,
    role: WorkspaceRole,
) -> tuple[dict[str, str], str]:
    email = random_email()
    password = random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )
    add_membership(db, user, workspace_id, role)
    return (
        user_authentication_headers(client=client, email=email, password=password),
        email,
    )
