import uuid
from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    CurrentWorkspace,
    SessionDep,
    get_current_workspace_editor,
)
from app.models import (
    Message,
    ToolPublic,
    ToolRegister,
    ToolRegisterResponse,
    ToolRegistry,
    ToolsPublic,
    ToolUpdate,
)
from app.services.tools import registry
from app.services.tools.errors import (
    DuplicateToolNameError,
    ToolNotFoundError,
    ToolServiceError,
)

router = APIRouter(prefix="/tools", tags=["tools"])


def _public(tool: ToolRegistry) -> ToolPublic:
    return ToolPublic.model_validate(tool)


def _raise(exc: ToolServiceError) -> NoReturn:
    if isinstance(exc, DuplicateToolNameError):
        status_code = 409
    elif isinstance(exc, ToolNotFoundError):
        status_code = 404
    else:
        status_code = 422
    raise HTTPException(status_code=status_code, detail=exc.message) from exc


@router.post(
    "/register",
    status_code=201,
    dependencies=[Depends(get_current_workspace_editor)],
)
def register_tool(
    *,
    session: SessionDep,
    workspace: CurrentWorkspace,
    body: ToolRegister,
) -> ToolRegisterResponse:
    """Register an HTTP or JS tool for the current workspace.

    HTTP tools include a method and URL. JS tools send a name and schema, with
    kind "js" or with no method and no URL. POST, PUT, and DELETE are stored
    with requires_hitl true. The URL is not called.
    """
    try:
        tool = registry.register_tool(
            session=session,
            workspace_id=workspace.id,
            name=body.name,
            kind=body.kind,
            http_method=body.http_method,
            url=body.url,
            requires_hitl=body.requires_hitl,
            tool_schema=body.tool_schema,
            description=body.description,
        )
    except ToolServiceError as exc:
        _raise(exc)
    return ToolRegisterResponse(tool_id=tool.id, status="active")


@router.get("")
def read_tools(
    session: SessionDep,
    workspace: CurrentWorkspace,
    skip: int = 0,
    limit: int = 100,
) -> ToolsPublic:
    """List tools in the current workspace."""
    tools, count = registry.list_tools(
        session=session, workspace_id=workspace.id, skip=skip, limit=limit
    )
    return ToolsPublic(data=[_public(tool) for tool in tools], count=count)


@router.get("/{tool_id}")
def read_tool(
    session: SessionDep, workspace: CurrentWorkspace, tool_id: uuid.UUID
) -> ToolPublic:
    """Get one tool in the current workspace."""
    try:
        tool = registry.get_tool(
            session=session, workspace_id=workspace.id, tool_id=tool_id
        )
    except ToolServiceError as exc:
        _raise(exc)
    return _public(tool)


@router.patch(
    "/{tool_id}",
    dependencies=[Depends(get_current_workspace_editor)],
)
def update_tool(
    *,
    session: SessionDep,
    workspace: CurrentWorkspace,
    tool_id: uuid.UUID,
    body: ToolUpdate,
) -> ToolPublic:
    """Edit schema, URL, description, or method for a tool in this workspace."""
    try:
        tool = registry.update_tool(
            session=session,
            workspace_id=workspace.id,
            tool_id=tool_id,
            changes=body.model_dump(exclude_unset=True),
        )
    except ToolServiceError as exc:
        _raise(exc)
    return _public(tool)


@router.delete(
    "/{tool_id}",
    dependencies=[Depends(get_current_workspace_editor)],
)
def remove_tool(
    session: SessionDep, workspace: CurrentWorkspace, tool_id: uuid.UUID
) -> Message:
    """Delete a tool row from the current workspace."""
    try:
        registry.delete_tool(
            session=session, workspace_id=workspace.id, tool_id=tool_id
        )
    except ToolServiceError as exc:
        _raise(exc)
    return Message(message="Tool deleted successfully")
