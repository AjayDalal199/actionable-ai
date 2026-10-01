from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload, User, Workspace, WorkspaceMembership, WorkspaceRole
from app.services.workspaces import get_membership, is_joined_member

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except InvalidTokenError, ValidationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_membership(
    session: SessionDep, current_user: CurrentUser
) -> WorkspaceMembership:
    if current_user.workspace_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of a workspace",
        )
    membership = get_membership(
        session=session,
        user_id=current_user.id,
        workspace_id=current_user.workspace_id,
    )
    if membership is None or not is_joined_member(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of a workspace",
        )
    return membership


CurrentMembership = Annotated[WorkspaceMembership, Depends(get_current_membership)]


def get_current_workspace(
    session: SessionDep, membership: CurrentMembership
) -> Workspace:
    workspace = session.get(Workspace, membership.workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    return workspace


CurrentWorkspace = Annotated[Workspace, Depends(get_current_workspace)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


def _require_workspace_roles(
    membership: WorkspaceMembership, allowed: tuple[WorkspaceRole, ...]
) -> None:
    if membership.role not in allowed:
        if allowed == (WorkspaceRole.ADMIN,):
            detail = "Only workspace admins can perform this action"
        elif allowed == (WorkspaceRole.ADMIN, WorkspaceRole.EDITOR):
            detail = "Only workspace editors can perform this action"
        else:
            detail = "The user doesn't have enough privileges"
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def get_current_workspace_admin(
    current_user: CurrentUser,
    membership: CurrentMembership,
) -> User:
    _require_workspace_roles(membership, (WorkspaceRole.ADMIN,))
    return current_user


def get_current_workspace_editor(
    current_user: CurrentUser,
    membership: CurrentMembership,
) -> User:
    _require_workspace_roles(membership, (WorkspaceRole.ADMIN, WorkspaceRole.EDITOR))
    return current_user


CurrentWorkspaceAdmin = Annotated[User, Depends(get_current_workspace_admin)]
CurrentWorkspaceEditor = Annotated[User, Depends(get_current_workspace_editor)]
