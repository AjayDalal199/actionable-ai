import pytest
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, Workspace, WorkspaceRole
from app.services.workspaces import (
    UserAlreadyInWorkspaceError,
    WorkspaceNotAdminError,
    create_and_attach_workspace,
    name_for_new_workspace,
    rename_workspace,
)
from tests.utils.utils import random_email, random_lower_string


def test_name_for_new_workspace_uses_explicit_name() -> None:
    assert (
        name_for_new_workspace(email="david@acme.com", name="Acme Corp") == "Acme Corp"
    )


def test_name_for_new_workspace_strips_explicit_name() -> None:
    assert name_for_new_workspace(email="david@acme.com", name="  Acme  ") == "Acme"


def test_name_for_new_workspace_defaults_from_email_domain() -> None:
    assert name_for_new_workspace(email="david@acme.com") == "Acme"


def test_name_for_new_workspace_falls_back_to_local_part() -> None:
    assert name_for_new_workspace(email="solo") == "solo"


def test_create_and_attach_workspace_makes_user_admin(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=user, name="Acme Corp")

    assert workspace.name == "Acme Corp"
    assert user.workspace_id == workspace.id
    assert user.role == WorkspaceRole.ADMIN
    stored = db.get(User, user.id)
    assert stored is not None
    assert stored.workspace_id == workspace.id
    assert stored.role == WorkspaceRole.ADMIN


def test_create_and_attach_workspace_is_idempotent_when_exist_ok(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    first = create_and_attach_workspace(session=db, user=user, name="Acme")
    second = create_and_attach_workspace(
        session=db, user=user, name="Other", exist_ok=True
    )

    assert first.id == second.id
    assert db.get(Workspace, first.id) is not None
    assert user.workspace_id == first.id


def test_create_and_attach_workspace_rejects_second_workspace(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    create_and_attach_workspace(session=db, user=user, name="Acme")
    with pytest.raises(UserAlreadyInWorkspaceError):
        create_and_attach_workspace(session=db, user=user, name="Other")


def test_first_superuser_has_workspace(db: Session) -> None:
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    assert user.workspace_id is not None
    assert user.role == WorkspaceRole.ADMIN
    workspace = db.get(Workspace, user.workspace_id)
    assert workspace is not None


def test_rename_workspace_as_admin(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=user, name="Acme")
    renamed = rename_workspace(
        session=db, user=user, workspace=workspace, name="Acme Corp"
    )
    assert renamed.name == "Acme Corp"
    stored = db.get(Workspace, workspace.id)
    assert stored is not None
    assert stored.name == "Acme Corp"


def test_rename_workspace_rejects_non_admin(db: Session) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=admin, name="Acme")
    editor = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    editor.workspace_id = workspace.id
    editor.role = WorkspaceRole.EDITOR
    db.add(editor)
    db.commit()
    db.refresh(editor)

    with pytest.raises(WorkspaceNotAdminError):
        rename_workspace(session=db, user=editor, workspace=workspace, name="Nope")
    stored = db.get(Workspace, workspace.id)
    assert stored is not None
    assert stored.name == "Acme"


def test_rename_workspace_rejects_admin_of_another_workspace(db: Session) -> None:
    admin_a = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    create_and_attach_workspace(session=db, user=admin_a, name="A")
    admin_b = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace_b = create_and_attach_workspace(session=db, user=admin_b, name="B")

    with pytest.raises(WorkspaceNotAdminError):
        rename_workspace(session=db, user=admin_a, workspace=workspace_b, name="Hacked")
    stored = db.get(Workspace, workspace_b.id)
    assert stored is not None
    assert stored.name == "B"
