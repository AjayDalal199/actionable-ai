import inspect
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from app import crud
from app.api.deps import get_current_workspace
from app.core.config import settings
from app.models import UserCreate
from app.services.workspaces import create_and_attach_workspace
from tests.utils.utils import random_email, random_lower_string


def test_current_workspace_does_not_take_a_client_id() -> None:
    assert "workspace_id" not in inspect.signature(get_current_workspace).parameters


def test_current_workspace_from_session_user(db: Session) -> None:
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    workspace = get_current_workspace(session=db, current_user=user)
    assert workspace.id == user.workspace_id


def test_current_workspace_for_attached_user(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    attached = create_and_attach_workspace(session=db, user=user, name="Acme")
    workspace = get_current_workspace(session=db, current_user=user)
    assert workspace.id == attached.id


def test_current_workspace_forbidden_without_membership(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    with pytest.raises(HTTPException) as exc_info:
        get_current_workspace(session=db, current_user=user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "User is not a member of a workspace"


def test_current_workspace_not_found_if_row_missing() -> None:
    session = MagicMock()
    session.get.return_value = None
    user = MagicMock()
    user.workspace_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        get_current_workspace(session=session, current_user=user)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Workspace not found"
    session.get.assert_called_once()
