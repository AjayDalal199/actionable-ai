import secrets
import uuid

from sqlmodel import Session, col, func, select

from app import crud
from app.models import (
    InvitationStatus,
    User,
    UserCreate,
    UserPublic,
    UserUpdate,
    Workspace,
    WorkspaceInvitePreview,
    WorkspaceListItem,
    WorkspaceMemberPublic,
    WorkspaceMembership,
    WorkspaceRole,
    WorkspacesPublic,
)


class UserAlreadyCreatedWorkspaceError(Exception):
    """The user has already created their one allowed workspace."""


class WorkspaceNotAdminError(Exception):
    """The user is not an Admin of the given workspace."""


class UserAlreadyMemberError(Exception):
    """The email already belongs to this workspace."""


class MemberNotFoundError(Exception):
    """No such member in this workspace."""


class CannotModifyLastAdminError(Exception):
    """Demoting or deactivating the last active Admin would lock the workspace."""


class CannotDeleteLastAdminError(Exception):
    """Deleting the last Admin would leave other members unable to manage the workspace."""


class WorkspaceNotMemberError(Exception):
    """The user is not an active member of the given workspace."""


class InviteTokenInvalidError(Exception):
    """The invite token is missing, expired, or does not match a membership."""


class InvitePasswordRequiredError(Exception):
    """A new invited account must choose a password before accepting."""


class InviteAlreadyAcceptedError(Exception):
    """The invite was already accepted, so it cannot be declined."""


def is_joined_member(membership: WorkspaceMembership) -> bool:
    return (
        membership.is_active
        and membership.invitation_status == InvitationStatus.ACCEPTED
    )


def _joined_membership_filters() -> tuple:
    return (
        col(WorkspaceMembership.is_active).is_(True),
        WorkspaceMembership.invitation_status == InvitationStatus.ACCEPTED,
    )


def name_for_new_workspace(*, email: str, name: str | None = None) -> str:
    if name is not None:
        stripped = name.strip()
        if stripped:
            return stripped[:255]
    _, separator, domain = email.partition("@")
    if separator and domain:
        label = domain.split(".")[0].strip()
        if label:
            return label.capitalize()[:255]
    local = email.partition("@")[0].strip()
    return (local or "Workspace")[:255]


def get_membership(
    *, session: Session, user_id: uuid.UUID, workspace_id: uuid.UUID
) -> WorkspaceMembership | None:
    return session.exec(
        select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.workspace_id == workspace_id,
        )
    ).first()


def created_workspace(*, session: Session, user_id: uuid.UUID) -> Workspace | None:
    return session.exec(
        select(Workspace).where(Workspace.created_by_id == user_id)
    ).first()


def user_can_create_workspace(*, session: Session, user_id: uuid.UUID) -> bool:
    return created_workspace(session=session, user_id=user_id) is None


def to_user_public(*, session: Session, user: User) -> UserPublic:
    role = None
    if user.workspace_id is not None:
        membership = get_membership(
            session=session, user_id=user.id, workspace_id=user.workspace_id
        )
        if membership is not None and is_joined_member(membership):
            role = membership.role
    return UserPublic(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        full_name=user.full_name,
        created_at=user.created_at,
        workspace_id=user.workspace_id,
        role=role,
    )


def member_public(user: User, membership: WorkspaceMembership) -> WorkspaceMemberPublic:
    return WorkspaceMemberPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=membership.role,
        invitation_status=membership.invitation_status,
        is_active=membership.is_active,
        created_at=membership.created_at,
    )


def _add_membership(
    *,
    session: Session,
    user: User,
    workspace: Workspace,
    role: WorkspaceRole,
    set_current: bool = False,
    invitation_status: InvitationStatus = InvitationStatus.ACCEPTED,
) -> WorkspaceMembership:
    membership = WorkspaceMembership(
        user_id=user.id,
        workspace_id=workspace.id,
        role=role,
        is_active=True,
        invitation_status=invitation_status,
    )
    session.add(membership)
    if invitation_status == InvitationStatus.ACCEPTED and (
        set_current or user.workspace_id is None
    ):
        user.workspace_id = workspace.id
        session.add(user)
    return membership


def create_and_attach_workspace(
    *,
    session: Session,
    user: User,
    name: str | None = None,
    exist_ok: bool = False,
) -> Workspace:
    session.add(user)
    session.flush()
    locked_user = session.exec(
        select(User).where(User.id == user.id).with_for_update()
    ).one()
    existing = created_workspace(session=session, user_id=locked_user.id)
    if existing is not None:
        if exist_ok:
            if locked_user.workspace_id is None:
                locked_user.workspace_id = existing.id
                session.add(locked_user)
                session.commit()
                session.refresh(locked_user)
            return existing
        raise UserAlreadyCreatedWorkspaceError

    workspace = Workspace(
        name=name_for_new_workspace(email=locked_user.email, name=name),
        created_by_id=locked_user.id,
    )
    session.add(workspace)
    session.flush()
    _add_membership(
        session=session,
        user=locked_user,
        workspace=workspace,
        role=WorkspaceRole.ADMIN,
        set_current=True,
    )
    session.commit()
    session.refresh(workspace)
    session.refresh(locked_user)
    return workspace


def rename_workspace(
    *,
    session: Session,
    user: User,
    workspace: Workspace,
    name: str,
) -> Workspace:
    _require_admin(session=session, user=user, workspace=workspace)
    workspace.name = name
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


def _require_admin(*, session: Session, user: User, workspace: Workspace) -> None:
    membership = get_membership(
        session=session, user_id=user.id, workspace_id=workspace.id
    )
    if (
        membership is None
        or not is_joined_member(membership)
        or membership.role != WorkspaceRole.ADMIN
    ):
        raise WorkspaceNotAdminError


def _active_admin_count(session: Session, workspace_id: uuid.UUID) -> int:
    return session.exec(
        select(func.count())
        .select_from(WorkspaceMembership)
        .join(User, col(User.id) == col(WorkspaceMembership.user_id))
        .where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.role == WorkspaceRole.ADMIN,
            *_joined_membership_filters(),
            col(User.is_active).is_(True),
        )
    ).one()


def list_user_workspaces(*, session: Session, user: User) -> WorkspacesPublic:
    rows = session.exec(
        select(Workspace, WorkspaceMembership)
        .join(
            WorkspaceMembership,
            col(WorkspaceMembership.workspace_id) == col(Workspace.id),
        )
        .where(
            WorkspaceMembership.user_id == user.id,
            *_joined_membership_filters(),
        )
        .order_by(col(Workspace.created_at).desc())
    ).all()
    data = [
        WorkspaceListItem(
            id=workspace.id,
            name=workspace.name,
            created_at=workspace.created_at,
            role=membership.role,
            is_current=workspace.id == user.workspace_id,
        )
        for workspace, membership in rows
    ]
    return WorkspacesPublic(
        data=data,
        count=len(data),
        can_create=user_can_create_workspace(session=session, user_id=user.id),
    )


def set_current_workspace(
    *, session: Session, user: User, workspace_id: uuid.UUID
) -> Workspace:
    membership = get_membership(
        session=session, user_id=user.id, workspace_id=workspace_id
    )
    if membership is None or not is_joined_member(membership):
        raise WorkspaceNotMemberError
    workspace = session.get(Workspace, workspace_id)
    if workspace is None:
        raise WorkspaceNotMemberError
    user.workspace_id = workspace.id
    session.add(user)
    session.commit()
    session.refresh(workspace)
    session.refresh(user)
    return workspace


def list_members(
    *, session: Session, workspace: Workspace
) -> tuple[list[WorkspaceMemberPublic], int]:
    rows = session.exec(
        select(User, WorkspaceMembership)
        .join(
            WorkspaceMembership,
            col(WorkspaceMembership.user_id) == col(User.id),
        )
        .where(WorkspaceMembership.workspace_id == workspace.id)
        .order_by(col(WorkspaceMembership.created_at).desc())
    ).all()
    members = [member_public(user, membership) for user, membership in rows]
    return members, len(members)


def invite_member(
    *,
    session: Session,
    admin: User,
    workspace: Workspace,
    email: str,
    role: WorkspaceRole,
    full_name: str | None = None,
) -> tuple[User, WorkspaceMembership, bool]:
    _require_admin(session=session, user=admin, workspace=workspace)
    existing = crud.get_user_by_email(session=session, email=email)
    if existing:
        membership = get_membership(
            session=session, user_id=existing.id, workspace_id=workspace.id
        )
        if membership is not None and is_joined_member(membership):
            raise UserAlreadyMemberError
        if membership is None:
            membership = _add_membership(
                session=session,
                user=existing,
                workspace=workspace,
                role=role,
                invitation_status=InvitationStatus.PENDING,
            )
        elif (
            not membership.is_active
            and membership.invitation_status == InvitationStatus.ACCEPTED
        ):
            membership.role = role
            membership.is_active = True
            if existing.workspace_id is None:
                existing.workspace_id = workspace.id
                session.add(existing)
            session.add(membership)
        else:
            membership.role = role
            membership.is_active = True
            membership.invitation_status = InvitationStatus.PENDING
            session.add(membership)
        session.commit()
        session.refresh(existing)
        session.refresh(membership)
        return existing, membership, False

    user_create = UserCreate(
        email=email,
        password=secrets.token_urlsafe(32),
        full_name=full_name,
    )
    user = crud.create_user(session=session, user_create=user_create, commit=False)
    user.must_set_password = True
    session.add(user)
    membership = _add_membership(
        session=session,
        user=user,
        workspace=workspace,
        role=role,
        invitation_status=InvitationStatus.PENDING,
    )
    session.commit()
    session.refresh(user)
    session.refresh(membership)
    return user, membership, True


def _membership_from_invite_token(
    *, session: Session, token: str
) -> tuple[User, Workspace, WorkspaceMembership]:
    from app.utils import verify_workspace_invite_token

    token_data = verify_workspace_invite_token(token)
    if token_data is None:
        raise InviteTokenInvalidError
    user = crud.get_user_by_email(session=session, email=token_data.email)
    workspace = session.get(Workspace, token_data.workspace_id)
    if user is None or workspace is None:
        raise InviteTokenInvalidError
    membership = get_membership(
        session=session, user_id=user.id, workspace_id=workspace.id
    )
    if membership is None:
        raise InviteTokenInvalidError
    return user, workspace, membership


def preview_invite(*, session: Session, token: str) -> WorkspaceInvitePreview:
    user, workspace, membership = _membership_from_invite_token(
        session=session, token=token
    )
    return WorkspaceInvitePreview(
        email=user.email,
        workspace_name=workspace.name,
        role=membership.role,
        status=membership.invitation_status,
        needs_password=user.must_set_password,
    )


def accept_invite(
    *, session: Session, token: str, password: str | None = None
) -> tuple[User, WorkspaceMembership]:
    user, _workspace, membership = _membership_from_invite_token(
        session=session, token=token
    )
    if is_joined_member(membership):
        return user, membership
    if user.must_set_password and not password:
        raise InvitePasswordRequiredError
    membership.invitation_status = InvitationStatus.ACCEPTED
    membership.is_active = True
    session.add(membership)
    if user.workspace_id is None:
        user.workspace_id = membership.workspace_id
        session.add(user)
    if password:
        crud.update_user(
            session=session,
            db_user=user,
            user_in=UserUpdate(password=password),
        )
        session.refresh(membership)
    else:
        session.commit()
        session.refresh(user)
        session.refresh(membership)
    return user, membership


def decline_invite(*, session: Session, token: str) -> tuple[User, WorkspaceMembership]:
    user, _workspace, membership = _membership_from_invite_token(
        session=session, token=token
    )
    if is_joined_member(membership):
        raise InviteAlreadyAcceptedError
    membership.invitation_status = InvitationStatus.DECLINED
    session.add(membership)
    session.commit()
    session.refresh(user)
    session.refresh(membership)
    return user, membership


def _other_active_workspace_id(
    *, session: Session, user_id: uuid.UUID, exclude_workspace_id: uuid.UUID
) -> uuid.UUID | None:
    membership = session.exec(
        select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.workspace_id != exclude_workspace_id,
            *_joined_membership_filters(),
        )
    ).first()
    return membership.workspace_id if membership else None


def update_member(
    *,
    session: Session,
    admin: User,
    workspace: Workspace,
    user_id: uuid.UUID,
    role: WorkspaceRole | None = None,
    is_active: bool | None = None,
) -> tuple[User, WorkspaceMembership]:
    _require_admin(session=session, user=admin, workspace=workspace)
    member = session.get(User, user_id)
    membership = get_membership(
        session=session, user_id=user_id, workspace_id=workspace.id
    )
    if member is None or membership is None:
        raise MemberNotFoundError

    new_role = role if role is not None else membership.role
    new_active = is_active if is_active is not None else membership.is_active
    is_last_active_admin = (
        membership.role == WorkspaceRole.ADMIN
        and is_joined_member(membership)
        and member.is_active
        and _active_admin_count(session, workspace.id) == 1
    )
    losing_admin = new_role != WorkspaceRole.ADMIN or not new_active
    if is_last_active_admin and losing_admin:
        raise CannotModifyLastAdminError

    if role is not None:
        membership.role = role
    if is_active is not None:
        membership.is_active = is_active
        if not is_active and member.workspace_id == workspace.id:
            member.workspace_id = _other_active_workspace_id(
                session=session,
                user_id=member.id,
                exclude_workspace_id=workspace.id,
            )
            session.add(member)
    session.add(membership)
    session.commit()
    session.refresh(member)
    session.refresh(membership)
    return member, membership


def _other_active_member_count(
    session: Session, workspace_id: uuid.UUID, user_id: uuid.UUID
) -> int:
    return session.exec(
        select(func.count())
        .select_from(WorkspaceMembership)
        .join(User, col(User.id) == col(WorkspaceMembership.user_id))
        .where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id != user_id,
            *_joined_membership_filters(),
            col(User.is_active).is_(True),
        )
    ).one()


def assert_can_delete_user(*, session: Session, user: User) -> None:
    if not user.is_active:
        return
    admin_memberships = session.exec(
        select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == user.id,
            WorkspaceMembership.role == WorkspaceRole.ADMIN,
            *_joined_membership_filters(),
        )
    ).all()
    for membership in admin_memberships:
        if (
            _active_admin_count(session, membership.workspace_id) == 1
            and _other_active_member_count(session, membership.workspace_id, user.id)
            > 0
        ):
            raise CannotDeleteLastAdminError
