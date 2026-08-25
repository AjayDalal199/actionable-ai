import pytest
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, Workspace, WorkspaceRole
from app.services.workspaces import (
    CannotDeleteLastAdminError,
    CannotModifyLastAdminError,
    MemberNotFoundError,
    UserAlreadyCreatedWorkspaceError,
    UserAlreadyMemberError,
    WorkspaceNotAdminError,
    assert_can_delete_user,
    create_and_attach_workspace,
    get_membership,
    invite_member,
    list_members,
    name_for_new_workspace,
    rename_workspace,
    update_member,
)
from tests.utils.utils import random_email, random_lower_string
from tests.utils.workspace import add_membership


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
    membership = get_membership(session=db, user_id=user.id, workspace_id=workspace.id)
    assert membership is not None
    assert membership.role == WorkspaceRole.ADMIN
    stored = db.get(User, user.id)
    assert stored is not None
    assert stored.workspace_id == workspace.id


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
    with pytest.raises(UserAlreadyCreatedWorkspaceError):
        create_and_attach_workspace(session=db, user=user, name="Other")


def test_first_superuser_has_workspace(db: Session) -> None:
    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    assert user.workspace_id is not None
    membership = get_membership(
        session=db, user_id=user.id, workspace_id=user.workspace_id
    )
    assert membership is not None
    assert membership.role == WorkspaceRole.ADMIN
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
    add_membership(db, editor, workspace.id, WorkspaceRole.EDITOR)

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


def test_invite_member_creates_user(db: Session) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=admin, name="Acme")
    invited_email = random_email()
    member, membership, created = invite_member(
        session=db,
        admin=admin,
        workspace=workspace,
        email=invited_email,
        role=WorkspaceRole.EDITOR,
        full_name="Sam",
    )
    assert created is True
    assert member.email == invited_email
    assert member.workspace_id == workspace.id
    assert membership.role == WorkspaceRole.EDITOR
    assert member.full_name == "Sam"
    assert member.is_superuser is False


def test_invite_member_attaches_existing_user(db: Session) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=admin, name="Acme")
    existing = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    member, membership, created = invite_member(
        session=db,
        admin=admin,
        workspace=workspace,
        email=existing.email,
        role=WorkspaceRole.VIEWER,
    )
    assert created is False
    assert member.id == existing.id
    assert member.workspace_id == workspace.id
    assert membership.role == WorkspaceRole.VIEWER


def test_invite_member_does_not_overwrite_existing_full_name(db: Session) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=admin, name="Acme")
    existing = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=random_email(),
            password=random_lower_string(),
            full_name="Original Name",
        ),
    )
    member, _membership, created = invite_member(
        session=db,
        admin=admin,
        workspace=workspace,
        email=existing.email,
        role=WorkspaceRole.VIEWER,
        full_name="Renamed By Admin",
    )
    assert created is False
    assert member.full_name == "Original Name"


def test_invite_member_reactivates_deactivated_membership(db: Session) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=admin, name="Acme")
    editor = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    add_membership(db, editor, workspace.id, WorkspaceRole.EDITOR)
    update_member(
        session=db,
        admin=admin,
        workspace=workspace,
        user_id=editor.id,
        is_active=False,
    )
    member, membership, created = invite_member(
        session=db,
        admin=admin,
        workspace=workspace,
        email=editor.email,
        role=WorkspaceRole.VIEWER,
    )
    assert created is False
    assert membership.is_active is True
    assert membership.role == WorkspaceRole.VIEWER
    assert member.workspace_id == workspace.id


def test_invite_member_rejects_existing_member(db: Session) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=admin, name="Acme")
    with pytest.raises(UserAlreadyMemberError):
        invite_member(
            session=db,
            admin=admin,
            workspace=workspace,
            email=admin.email,
            role=WorkspaceRole.EDITOR,
        )


def test_invite_member_can_join_another_workspace(db: Session) -> None:
    admin_a = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace_a = create_and_attach_workspace(session=db, user=admin_a, name="A")
    admin_b = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace_b = create_and_attach_workspace(session=db, user=admin_b, name="B")
    member, membership, created = invite_member(
        session=db,
        admin=admin_a,
        workspace=workspace_a,
        email=admin_b.email,
        role=WorkspaceRole.EDITOR,
    )
    assert created is False
    assert member.id == admin_b.id
    assert membership.workspace_id == workspace_a.id
    assert membership.role == WorkspaceRole.EDITOR
    assert admin_b.workspace_id == workspace_b.id
    assert (
        get_membership(session=db, user_id=admin_b.id, workspace_id=workspace_b.id)
        is not None
    )


def test_invite_member_rejects_non_admin(db: Session) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=admin, name="Acme")
    editor = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    add_membership(db, editor, workspace.id, WorkspaceRole.EDITOR)
    with pytest.raises(WorkspaceNotAdminError):
        invite_member(
            session=db,
            admin=editor,
            workspace=workspace,
            email=random_email(),
            role=WorkspaceRole.VIEWER,
        )


def test_list_members_is_workspace_scoped(db: Session) -> None:
    admin_a = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace_a = create_and_attach_workspace(session=db, user=admin_a, name="A")
    admin_b = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace_b = create_and_attach_workspace(session=db, user=admin_b, name="B")
    members_a, count_a = list_members(session=db, workspace=workspace_a)
    members_b, count_b = list_members(session=db, workspace=workspace_b)
    assert count_a == 1
    assert count_b == 1
    assert members_a[0].id == admin_a.id
    assert members_b[0].id == admin_b.id


def test_invited_user_can_still_create_own_workspace(db: Session) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=admin, name="Acme")
    invited = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    invite_member(
        session=db,
        admin=admin,
        workspace=workspace,
        email=invited.email,
        role=WorkspaceRole.EDITOR,
    )
    db.refresh(invited)
    own = create_and_attach_workspace(session=db, user=invited, name="Mine")
    assert own.id != workspace.id
    assert invited.workspace_id == own.id
    assert (
        get_membership(session=db, user_id=invited.id, workspace_id=workspace.id)
        is not None
    )
    own_membership = get_membership(session=db, user_id=invited.id, workspace_id=own.id)
    assert own_membership is not None
    assert own_membership.role == WorkspaceRole.ADMIN


def test_update_member_role_and_reject_last_admin(db: Session) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=admin, name="Acme")
    editor = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    add_membership(db, editor, workspace.id, WorkspaceRole.EDITOR)

    _member, membership = update_member(
        session=db,
        admin=admin,
        workspace=workspace,
        user_id=editor.id,
        role=WorkspaceRole.VIEWER,
    )
    assert membership.role == WorkspaceRole.VIEWER

    with pytest.raises(CannotModifyLastAdminError):
        update_member(
            session=db,
            admin=admin,
            workspace=workspace,
            user_id=admin.id,
            role=WorkspaceRole.EDITOR,
        )
    with pytest.raises(CannotModifyLastAdminError):
        update_member(
            session=db,
            admin=admin,
            workspace=workspace,
            user_id=admin.id,
            is_active=False,
        )


def test_update_member_not_found_cross_tenant(db: Session) -> None:
    admin_a = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace_a = create_and_attach_workspace(session=db, user=admin_a, name="A")
    admin_b = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    create_and_attach_workspace(session=db, user=admin_b, name="B")
    with pytest.raises(MemberNotFoundError):
        update_member(
            session=db,
            admin=admin_a,
            workspace=workspace_a,
            user_id=admin_b.id,
            role=WorkspaceRole.VIEWER,
        )


def test_assert_can_delete_user_allows_sole_admin(db: Session) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    create_and_attach_workspace(session=db, user=admin, name="Acme")
    assert_can_delete_user(session=db, user=admin)


def test_assert_can_delete_user_blocks_last_admin_with_other_members(
    db: Session,
) -> None:
    admin = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    workspace = create_and_attach_workspace(session=db, user=admin, name="Acme")
    editor = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    add_membership(db, editor, workspace.id, WorkspaceRole.EDITOR)
    with pytest.raises(CannotDeleteLastAdminError):
        assert_can_delete_user(session=db, user=admin)
