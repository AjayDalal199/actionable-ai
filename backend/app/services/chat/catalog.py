"""Workspace HTTP tools as model functions, plus the HITL interceptor."""

import json
import uuid
from dataclasses import dataclass
from typing import Any

from google.genai import types
from sqlalchemy import true
from sqlmodel import Session, col, select

from app.models import ToolKind, ToolRegistry
from app.services.chat.errors import ACTION_UNAVAILABLE
from app.services.chat.plain import plain_summary

HITL_FUNCTION = "request_hitl_approval"

_HITL_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "tool_name": {
            "type": "string",
            "description": "The exact name of the registered tool you want to run.",
        },
        "tool_arguments": {
            "type": "object",
            "description": "The JSON object containing the parsed arguments for the tool.",
        },
        "human_readable_summary": {
            "type": "string",
            "description": (
                "A 1-sentence summary explaining to the user exactly what this "
                "action will do, so they can make an informed decision to approve "
                "or reject."
            ),
        },
    },
    "required": ["tool_name", "tool_arguments", "human_readable_summary"],
}

_HITL_DESCRIPTION = (
    "Call this tool whenever you need to execute an action that is flagged as "
    "'requires_hitl: true'. This will pause your execution and trigger a warning "
    "card on the user's screen."
)


@dataclass(frozen=True, kw_only=True)
class ToolView:
    id: str
    name: str
    description: str
    requires_hitl: bool
    schema: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "requires_hitl": self.requires_hitl,
            "schema": self.schema,
        }


@dataclass(frozen=True, kw_only=True)
class RunTool:
    tool_id: str
    arguments: dict[str, Any]
    function_name: str
    function_args: dict[str, Any]
    requires_hitl: bool
    description: str


@dataclass(frozen=True, kw_only=True)
class RejectCall:
    function_name: str
    function_args: dict[str, Any]
    message: str


def load_http_tools(*, session: Session, workspace_id: uuid.UUID) -> list[ToolView]:
    """Active HTTP tools only. JS tools stay in the registry and are not offered."""
    rows = session.exec(
        select(ToolRegistry)
        .where(ToolRegistry.workspace_id == workspace_id)
        .where(ToolRegistry.is_active == true())
        .where(ToolRegistry.kind == ToolKind.HTTP)
        .order_by(col(ToolRegistry.name))
    ).all()
    return [
        ToolView(
            id=str(row.id),
            name=row.name,
            description=row.description,
            requires_hitl=row.requires_hitl,
            schema=row.tool_schema,
        )
        for row in rows
    ]


def function_declarations(
    tools: list[dict[str, Any]],
) -> list[types.FunctionDeclaration]:
    declarations = [
        types.FunctionDeclaration(
            name=HITL_FUNCTION,
            description=_HITL_DESCRIPTION,
            parameters_json_schema=_HITL_PARAMETERS,
        )
    ]
    for tool in tools:
        description = tool["description"].strip() or tool["name"]
        if tool["requires_hitl"]:
            description += (
                " Requires confirmation before it runs. "
                "Call request_hitl_approval instead of this function."
            )
        schema = tool["schema"] if isinstance(tool["schema"], dict) else {}
        if schema.get("type") != "object":
            schema = {"type": "object", "properties": {}}
        declarations.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=description,
                parameters_json_schema=schema,
            )
        )
    return declarations


def interpret(
    name: str, args: dict[str, Any], tools: list[dict[str, Any]]
) -> RunTool | RejectCall:
    """Decide whether a model call may run, must pause, or is unavailable.

    A write the model calls directly is still returned as ``RunTool`` with
    ``requires_hitl`` true. The graph turns that into a pause and does not
    call the HTTP engine.
    """
    by_name = {tool["name"]: tool for tool in tools}
    if name == HITL_FUNCTION:
        return _interpret_hitl(args, by_name)
    tool = by_name.get(name)
    if tool is None:
        return RejectCall(
            function_name=name,
            function_args=args,
            message=ACTION_UNAVAILABLE,
        )
    arguments = _object(args)
    if arguments is None:
        return RejectCall(
            function_name=name,
            function_args=args,
            message="Tool arguments must be an object.",
        )
    return RunTool(
        tool_id=tool["id"],
        arguments=arguments,
        function_name=name,
        function_args=args,
        requires_hitl=bool(tool["requires_hitl"]),
        description=tool["description"],
    )


def summary_for(decision: RunTool, args: dict[str, Any]) -> str:
    if decision.function_name == HITL_FUNCTION:
        raw = args.get("human_readable_summary")
        source = raw if isinstance(raw, str) else ""
    else:
        source = decision.description
    return plain_summary(source)


def _interpret_hitl(
    args: dict[str, Any], by_name: dict[str, dict[str, Any]]
) -> RunTool | RejectCall:
    tool_name = args.get("tool_name")
    tool = by_name.get(tool_name) if isinstance(tool_name, str) else None
    if tool is None:
        return RejectCall(
            function_name=HITL_FUNCTION,
            function_args=args,
            message=ACTION_UNAVAILABLE,
        )
    arguments = _object(args.get("tool_arguments", {}))
    if arguments is None:
        return RejectCall(
            function_name=HITL_FUNCTION,
            function_args=args,
            message="Tool arguments must be an object.",
        )
    return RunTool(
        tool_id=tool["id"],
        arguments=arguments,
        function_name=HITL_FUNCTION,
        function_args=args,
        requires_hitl=bool(tool["requires_hitl"]),
        description=tool["description"],
    )


def _object(value: object) -> dict[str, Any] | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    if not isinstance(value, dict):
        return None
    if any(not isinstance(key, str) for key in value):
        return None
    return dict(value)
