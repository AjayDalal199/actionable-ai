import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import (
    CurrentUser,
    CurrentWorkspace,
    CurrentWorkspaceAdmin,
    SessionDep,
)
from app.core.config import settings
from app.models import (
    WorkspaceCreate,
    WorkspaceInvite,
    WorkspaceInviteAction,
    WorkspaceInvitePreview,
    WorkspaceMemberPublic,
    WorkspaceMembersPublic,
    WorkspaceMemberUpdate,
    WorkspacePublic,
    WorkspaceSelect,
    WorkspacesPublic,
    WorkspaceUpdate,
)
from app.services.workspaces import (
    CannotModifyLastAdminError,
    InviteAlreadyAcceptedError,
    InvitePasswordRequiredError,
    InviteTokenInvalidError,
    MemberNotFoundError,
    UserAlreadyCreatedWorkspaceError,
    UserAlreadyMemberError,
    WorkspaceNotMemberError,
    accept_invite,
    create_and_attach_workspace,
    decline_invite,
    invite_member,
    list_members,
    list_user_workspaces,
    member_public,
    preview_invite,
    rename_workspace,
    set_current_workspace,
    update_member,
)
from app.utils import (
    generate_workspace_invite_email,
    generate_workspace_invite_token,
    send_email,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=WorkspacePublic)
def create_workspace(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    workspace_in: WorkspaceCreate,
) -> Any:
    """
    Create a workspace and attach the current user as Admin.
    Each user may create at most one workspace; join others via invite.
    """
    try:
        return create_and_attach_workspace(
            session=session,
            user=current_user,
            name=workspace_in.name,
        )
    except UserAlreadyCreatedWorkspaceError:
        raise HTTPException(
            status_code=409, detail="User has already created a workspace"
        )


@router.get("/", response_model=WorkspacesPublic)
def read_workspaces(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Workspaces the current user belongs to.
    """
    return list_user_workspaces(session=session, user=current_user)


@router.put("/current", response_model=WorkspacePublic)
def select_current_workspace(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: WorkspaceSelect,
) -> Any:
    """
    Switch the current workspace. Must already be an active member.
    """
    try:
        return set_current_workspace(
            session=session,
            user=current_user,
            workspace_id=body.workspace_id,
        )
    except WorkspaceNotMemberError:
        raise HTTPException(
            status_code=403,
            detail="User is not a member of a workspace",
        )


@router.get("/me", response_model=WorkspacePublic)
def read_workspace_me(workspace: CurrentWorkspace) -> Any:
    """
    Current workspace for the session user.
    """
    return workspace


@router.patch("/me", response_model=WorkspacePublic)
def update_workspace_me(
    *,
    session: SessionDep,
    current_user: CurrentWorkspaceAdmin,
    workspace: CurrentWorkspace,
    workspace_in: WorkspaceUpdate,
) -> Any:
    """
    Rename the current workspace. Admin only.
    """
    return rename_workspace(
        session=session,
        user=current_user,
        workspace=workspace,
        name=workspace_in.name,
    )


@router.get("/me/members", response_model=WorkspaceMembersPublic)
def read_workspace_members(session: SessionDep, workspace: CurrentWorkspace) -> Any:
    """
    List members of the current workspace.
    """
    members, count = list_members(session=session, workspace=workspace)
    return WorkspaceMembersPublic(data=members, count=count)


def _send_member_invite_email(
    *, member_email: str, workspace_name: str, workspace_id: uuid.UUID, role: str
) -> None:
    token = generate_workspace_invite_token(
        email=member_email, workspace_id=workspace_id
    )
    email_data = generate_workspace_invite_email(
        email_to=member_email,
        email=member_email,
        workspace_name=workspace_name,
        role=str(role).capitalize(),
        token=token,
    )
    if not settings.emails_enabled:
        logger.warning(
            "Skipping workspace invite email to %s; SMTP is not configured",
            member_email,
        )
        return
    try:
        send_email(
            email_to=member_email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    except Exception:
        logger.exception("Failed to send workspace invite email to %s", member_email)


@router.post("/me/members", response_model=WorkspaceMemberPublic, status_code=201)
def invite_workspace_member(
    *,
    session: SessionDep,
    current_user: CurrentWorkspaceAdmin,
    workspace: CurrentWorkspace,
    invite_in: WorkspaceInvite,
) -> Any:
    """
    Invite a user by email and role. Admin only.
    The invite stays pending until they accept or decline from the email.
    """
    try:
        member, membership, _created = invite_member(
            session=session,
            admin=current_user,
            workspace=workspace,
            email=invite_in.email,
            role=invite_in.role,
            full_name=invite_in.full_name,
        )
    except UserAlreadyMemberError:
        raise HTTPException(
            status_code=409, detail="User is already a member of this workspace"
        )

    _send_member_invite_email(
        member_email=member.email,
        workspace_name=workspace.name,
        workspace_id=workspace.id,
        role=membership.role,
    )
    return member_public(member, membership)


@router.get("/invites", response_model=WorkspaceInvitePreview)
def read_workspace_invite(session: SessionDep, token: str) -> Any:
    """
    Preview a workspace invite from the emailed token.
    """
    try:
        return preview_invite(session=session, token=token)
    except InviteTokenInvalidError:
        raise HTTPException(status_code=400, detail="Invalid token")


@router.post("/invites/accept", response_model=WorkspaceMemberPublic)
def accept_workspace_invite(*, session: SessionDep, body: WorkspaceInviteAction) -> Any:
    """
    Accept a workspace invite. New accounts must include a password.
    """
    try:
        member, membership = accept_invite(
            session=session, token=body.token, password=body.password
        )
    except InviteTokenInvalidError:
        raise HTTPException(status_code=400, detail="Invalid token")
    except InvitePasswordRequiredError:
        raise HTTPException(
            status_code=422,
            detail="Password is required to accept this invite",
        )
    return member_public(member, membership)


@router.post("/invites/decline", response_model=WorkspaceMemberPublic)
def decline_workspace_invite(
    *, session: SessionDep, body: WorkspaceInviteAction
) -> Any:
    """
    Decline a workspace invite.
    """
    try:
        member, membership = decline_invite(session=session, token=body.token)
    except InviteTokenInvalidError:
        raise HTTPException(status_code=400, detail="Invalid token")
    except InviteAlreadyAcceptedError:
        raise HTTPException(
            status_code=409,
            detail="Invite was already accepted",
        )
    return member_public(member, membership)


@router.patch("/me/members/{user_id}", response_model=WorkspaceMemberPublic)
def update_workspace_member(
    *,
    session: SessionDep,
    current_user: CurrentWorkspaceAdmin,
    workspace: CurrentWorkspace,
    user_id: uuid.UUID,
    member_in: WorkspaceMemberUpdate,
) -> Any:
    """
    Change a member's role or deactivate them in this workspace. Admin only.
    """
    try:
        member, membership = update_member(
            session=session,
            admin=current_user,
            workspace=workspace,
            user_id=user_id,
            role=member_in.role,
            is_active=member_in.is_active,
        )
    except MemberNotFoundError:
        raise HTTPException(status_code=404, detail="Member not found")
    except CannotModifyLastAdminError:
        raise HTTPException(
            status_code=409,
            detail="Cannot demote or deactivate the last admin",
        )
    return member_public(member, membership)
