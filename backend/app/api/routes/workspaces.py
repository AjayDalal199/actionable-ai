from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, CurrentWorkspace, SessionDep
from app.models import WorkspaceCreate, WorkspacePublic, WorkspaceUpdate
from app.services.workspaces import (
    UserAlreadyInWorkspaceError,
    WorkspaceNotAdminError,
    create_and_attach_workspace,
    rename_workspace,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("/", response_model=WorkspacePublic)
def create_workspace(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    workspace_in: WorkspaceCreate,
) -> Any:
    """
    Create a workspace and attach the current user as Admin.
    Skip this if you will join an existing workspace via invite.
    """
    try:
        return create_and_attach_workspace(
            session=session,
            user=current_user,
            name=workspace_in.name,
        )
    except UserAlreadyInWorkspaceError:
        raise HTTPException(
            status_code=409, detail="User already belongs to a workspace"
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
    current_user: CurrentUser,
    workspace: CurrentWorkspace,
    workspace_in: WorkspaceUpdate,
) -> Any:
    """
    Rename the current workspace. Admin only.
    """
    try:
        return rename_workspace(
            session=session,
            user=current_user,
            workspace=workspace,
            name=workspace_in.name,
        )
    except WorkspaceNotAdminError:
        raise HTTPException(
            status_code=403,
            detail="Only workspace admins can rename the workspace",
        )
