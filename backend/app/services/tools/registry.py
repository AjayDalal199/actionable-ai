"""Register, list, update, and delete workspace tools. Does not call tool URLs."""

import uuid
from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, func, select

from app.models import HttpMethod, ToolKind, ToolRegistry
from app.services.tools.errors import (
    DuplicateToolNameError,
    InvalidToolError,
    ToolNotFoundError,
)
from app.services.tools.validation import (
    requires_hitl_for,
    validate_name,
    validate_schema,
    validate_url,
)

_DUPLICATE_NAME = "A tool with this name already exists."
_HTTP_FIELDS = "HTTP tools require an HTTP method and URL."
_JS_FIELDS = "JS tools are registered with a name and schema only."
_UNIQUE_CONSTRAINT = "uq_tool_registry_workspace_name"


def register_tool(
    *,
    session: Session,
    workspace_id: uuid.UUID,
    name: str,
    kind: ToolKind | None,
    http_method: HttpMethod | None,
    url: str | None,
    requires_hitl: bool,
    tool_schema: dict[str, Any],
    description: str,
) -> ToolRegistry:
    stored_name = validate_name(name)
    schema = validate_schema(tool_schema)
    if not isinstance(description, str):
        raise InvalidToolError("Description must be a string.")
    resolved_kind = _resolve_kind(kind, http_method=http_method, url=url)
    method, stored_url = _endpoints(
        kind=resolved_kind, http_method=http_method, url=url
    )
    if _name_taken(session, workspace_id, stored_name):
        raise DuplicateToolNameError(_DUPLICATE_NAME)
    tool = ToolRegistry(
        workspace_id=workspace_id,
        name=stored_name,
        kind=resolved_kind,
        http_method=method,
        url=stored_url,
        tool_schema=schema,
        requires_hitl=requires_hitl_for(method, requires_hitl),
        description=description,
        is_active=True,
    )
    return _commit(session, tool)


def list_tools(
    *,
    session: Session,
    workspace_id: uuid.UUID,
    skip: int,
    limit: int,
) -> tuple[Sequence[ToolRegistry], int]:
    count = session.exec(
        select(func.count())
        .select_from(ToolRegistry)
        .where(ToolRegistry.workspace_id == workspace_id)
    ).one()
    tools = session.exec(
        select(ToolRegistry)
        .where(ToolRegistry.workspace_id == workspace_id)
        .order_by(col(ToolRegistry.name))
        .offset(skip)
        .limit(limit)
    ).all()
    return tools, count


def get_tool(
    *,
    session: Session,
    workspace_id: uuid.UUID,
    tool_id: uuid.UUID,
) -> ToolRegistry:
    tool = session.get(ToolRegistry, tool_id)
    if tool is None or tool.workspace_id != workspace_id:
        raise ToolNotFoundError("Tool not found")
    return tool


def update_tool(
    *,
    session: Session,
    workspace_id: uuid.UUID,
    tool_id: uuid.UUID,
    changes: Mapping[str, Any],
) -> ToolRegistry:
    tool = get_tool(session=session, workspace_id=workspace_id, tool_id=tool_id)
    schema = (
        validate_schema(changes["tool_schema"])
        if "tool_schema" in changes
        else tool.tool_schema
    )
    description = (
        _description(changes["description"])
        if "description" in changes
        else tool.description
    )
    requested_hitl = (
        _flag(changes["requires_hitl"])
        if "requires_hitl" in changes
        else tool.requires_hitl
    )
    method = tool.http_method
    url = tool.url
    if tool.kind == ToolKind.JS:
        if "url" in changes or "http_method" in changes:
            raise InvalidToolError(_JS_FIELDS)
    else:
        if "url" in changes:
            url = validate_url(changes["url"])
        if "http_method" in changes:
            method = _method(changes["http_method"])
        if method is None or url is None:
            raise InvalidToolError(_HTTP_FIELDS)
    tool.tool_schema = schema
    tool.description = description
    tool.http_method = method
    tool.url = url
    tool.requires_hitl = requires_hitl_for(method, requested_hitl)
    session.add(tool)
    session.commit()
    session.refresh(tool)
    return tool


def delete_tool(
    *,
    session: Session,
    workspace_id: uuid.UUID,
    tool_id: uuid.UUID,
) -> None:
    tool = get_tool(session=session, workspace_id=workspace_id, tool_id=tool_id)
    session.delete(tool)
    session.commit()


def _resolve_kind(
    kind: ToolKind | None, *, http_method: HttpMethod | None, url: str | None
) -> ToolKind:
    if kind is not None:
        return kind
    if http_method is None and url is None:
        return ToolKind.JS
    return ToolKind.HTTP


def _endpoints(
    *,
    kind: ToolKind,
    http_method: HttpMethod | None,
    url: str | None,
) -> tuple[HttpMethod | None, str | None]:
    if kind == ToolKind.HTTP:
        if http_method is None or url is None:
            raise InvalidToolError(_HTTP_FIELDS)
        return http_method, validate_url(url)
    if kind == ToolKind.JS:
        if http_method is not None or url is not None:
            raise InvalidToolError(_JS_FIELDS)
        return None, None
    raise InvalidToolError("Unsupported tool kind.")


def _description(value: object) -> str:
    if not isinstance(value, str):
        raise InvalidToolError("Description must be a string.")
    return value


def _flag(value: object) -> bool:
    if not isinstance(value, bool):
        raise InvalidToolError("requires_hitl must be true or false.")
    return value


def _method(value: object) -> HttpMethod:
    if isinstance(value, HttpMethod):
        return value
    if isinstance(value, str):
        try:
            return HttpMethod(value)
        except ValueError:
            pass
    raise InvalidToolError(_HTTP_FIELDS)


def _name_taken(session: Session, workspace_id: uuid.UUID, name: str) -> bool:
    found = session.exec(
        select(ToolRegistry.id).where(
            ToolRegistry.workspace_id == workspace_id,
            ToolRegistry.name == name,
        )
    ).first()
    return found is not None


def _commit(session: Session, tool: ToolRegistry) -> ToolRegistry:
    session.add(tool)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        if _is_duplicate_name(exc):
            raise DuplicateToolNameError(_DUPLICATE_NAME) from exc
        raise
    session.refresh(tool)
    return tool


def _is_duplicate_name(exc: IntegrityError) -> bool:
    orig = getattr(exc, "orig", None)
    diag = getattr(orig, "diag", None)
    constraint = getattr(diag, "constraint_name", None)
    return constraint == _UNIQUE_CONSTRAINT or _UNIQUE_CONSTRAINT in str(exc)
