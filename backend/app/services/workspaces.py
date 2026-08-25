from sqlmodel import Session, select

from app.models import User, Workspace, WorkspaceRole


class UserAlreadyInWorkspaceError(Exception):
    """The user already belongs to a workspace (MVP: one workspace per user)."""


class WorkspaceNotAdminError(Exception):
    """The user is not an Admin of the current workspace."""


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
    if locked_user.workspace_id is not None:
        existing = session.get(Workspace, locked_user.workspace_id)
        if existing is not None:
            if exist_ok:
                return existing
            raise UserAlreadyInWorkspaceError

    workspace = Workspace(
        name=name_for_new_workspace(email=locked_user.email, name=name)
    )
    session.add(workspace)
    session.flush()
    locked_user.workspace_id = workspace.id
    locked_user.role = WorkspaceRole.ADMIN
    session.add(locked_user)
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
    if user.workspace_id != workspace.id or user.role != WorkspaceRole.ADMIN:
        raise WorkspaceNotAdminError
    workspace.name = name
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace
