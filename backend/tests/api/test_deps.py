import inspect
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from app import crud
from app.api.deps import (
    get_current_membership,
    get_current_workspace,
    get_current_workspace_admin,
    get_current_workspace_editor,
)
from app.core.config import settings
from app.models import UserCreate, WorkspaceRole
from app.services.workspaces import create_and_attach_workspace
from tests.utils.utils import random_email, random_lower_string
from tests.utils.workspace import add_membership


def test_current_workspace_does_not_take_a_client_id() -> None:
    assert "workspace_id" not in inspect.signature(get_current_workspace).parameters


def test_current_workspace_from_session_user(db: Session) -> None:
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    membership = get_current_membership(session=db, current_user=user)
    workspace = get_current_workspace(session=db, membership=membership)
    assert workspace.id == user.workspace_id


def test_current_workspace_for_attached_user(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    attached = create_and_attach_workspace(session=db, user=user, name="Acme")
    membership = get_current_membership(session=db, current_user=user)
    workspace = get_current_workspace(session=db, membership=membership)
    assert workspace.id == attached.id


def test_current_workspace_forbidden_without_membership(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    with pytest.raises(HTTPException) as exc_info:
        get_current_membership(session=db, current_user=user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "User is not a member of a workspace"


def test_current_workspace_not_found_if_row_missing() -> None:
    session = MagicMock()
    session.get.return_value = None
    membership = MagicMock()
    membership.workspace_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        get_current_workspace(session=session, membership=membership)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Workspace not found"
    session.get.assert_called_once()


def test_workspace_admin_allows_admin(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    create_and_attach_workspace(session=db, user=user, name="Acme")
    membership = get_current_membership(session=db, current_user=user)
    assert get_current_workspace_admin(current_user=user, membership=membership) == user


def test_workspace_admin_rejects_editor(db: Session) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=admin, name="Acme")
    editor = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    membership = add_membership(db, editor, workspace.id, WorkspaceRole.EDITOR)
    with pytest.raises(HTTPException) as exc_info:
        get_current_workspace_admin(current_user=editor, membership=membership)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Only workspace admins can perform this action"


def test_workspace_editor_allows_editor_and_rejects_viewer(db: Session) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=admin, name="Acme")
    editor = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    editor_membership = add_membership(db, editor, workspace.id, WorkspaceRole.EDITOR)
    viewer = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    viewer_membership = add_membership(db, viewer, workspace.id, WorkspaceRole.VIEWER)

    assert (
        get_current_workspace_editor(current_user=editor, membership=editor_membership)
        is editor
    )
    with pytest.raises(HTTPException) as exc_info:
        get_current_workspace_editor(current_user=viewer, membership=viewer_membership)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Only workspace editors can perform this action"
