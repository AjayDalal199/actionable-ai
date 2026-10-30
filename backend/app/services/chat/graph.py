"""LangGraph for one internal turn: retrieve, reason, pause or run, then answer.

Writes never reach the HTTP engine from the reason node. ``execute`` calls
``execute_http_tool`` only for a read, or for a write after approval.
"""

import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Literal, TypedDict, cast

from asyncer import asyncify
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from sqlmodel import Session

from app.core.db import engine
from app.models import ToolKind, ToolRegistry
from app.services.chat.catalog import (
    RejectCall,
    RunTool,
    function_declarations,
    interpret,
    summary_for,
)
from app.services.chat.errors import (
    ACTION_UNAVAILABLE,
    TOOL_FAILED,
    ProviderError,
)
from app.services.chat.limits import MAX_TOOL_ITERATIONS, MAX_TOOL_RESULT_CHARS
from app.services.chat.llm import TextDelta, ToolRequest, build_contents, stream_model
from app.services.chat.plain import plain_title
from app.services.chat.prompts import CAP_NOTE, system_prompt
from app.services.chat.retrieve import retrieve_context
from app.services.tools.http_engine import HttpToolResult, execute_http_tool

logger = logging.getLogger(__name__)


class ChatState(TypedDict, total=False):
    session_id: str
    workspace_id: str
    user_id: str
    bearer: str
    user_text: str
    context: str | None
    has_context: bool
    tools: list[dict[str, Any]]
    transcript: list[dict[str, Any]]
    visible: str
    iteration: int
    approved: bool
    tool_call: dict[str, Any] | None
    pending: dict[str, Any] | None
    force_answer: bool
    cap_note: str | None
    continue_reason: bool
    finished: bool
    error_code: str | None
    tool_error: dict[str, Any] | None
    answer: str


@dataclass(frozen=True, kw_only=True)
class _Pause:
    description: str


def _route(**updates: Any) -> ChatState:
    state: ChatState = {
        "tool_call": None,
        "pending": None,
        "force_answer": False,
        "cap_note": None,
        "continue_reason": False,
        "finished": False,
        "error_code": None,
        "tool_error": None,
    }
    state.update(cast(ChatState, updates))
    return state


def _visible(state: ChatState, parts: list[str]) -> str:
    return state.get("visible", "") + "".join(parts)


async def retrieve(state: ChatState) -> ChatState:
    try:
        packed = await asyncify(retrieve_context)(
            workspace_id=uuid.UUID(state["workspace_id"]),
            user_text=state.get("user_text", ""),
        )
    except ProviderError:
        logger.exception("Chat retrieval failed")
        return _route(error_code="provider_error")
    return {"context": packed.text, "has_context": packed.found}


async def reason(state: ChatState) -> ChatState:
    text_parts: list[str] = []
    calls: list[ToolRequest] = []
    try:
        async for event in stream_model(
            system_prompt=system_prompt(state.get("context")),
            contents=build_contents(state.get("transcript", [])),
            tools=function_declarations(state.get("tools", [])),
        ):
            if isinstance(event, TextDelta):
                if event.text:
                    text_parts.append(event.text)
                    get_stream_writer()(
                        {"event": "message", "data": {"text": event.text}}
                    )
            else:
                calls.append(event)
    except ProviderError:
        logger.exception("Chat model failed")
        return _route(error_code="provider_error", visible=_visible(state, text_parts))
    visible = _visible(state, text_parts)
    if not calls:
        return _route(finished=True, visible=visible, answer=visible.strip())
    call = calls[0]
    decision = interpret(call.name, call.args, state.get("tools", []))
    transcript = list(state.get("transcript", []))
    transcript.append(
        {
            "role": "model",
            "text": "".join(text_parts),
            "call": {"name": call.name, "args": call.args},
        }
    )
    if isinstance(decision, RejectCall):
        return _rejected(state, decision, transcript, visible)
    if decision.requires_hitl:
        return _route(
            pending=_pending(state, decision, "".join(text_parts)),
            visible=visible,
            transcript=transcript,
        )
    if state.get("iteration", 0) >= MAX_TOOL_ITERATIONS:
        return _route(
            force_answer=True,
            cap_note=CAP_NOTE,
            visible=visible,
            transcript=transcript,
        )
    return _route(
        tool_call=_tool_call(decision),
        visible=visible,
        transcript=transcript,
    )


async def execute(state: ChatState) -> ChatState:
    call = state.get("tool_call")
    if not call:
        return _route(error_code="provider_error")
    outcome = await asyncify(invoke_tool)(
        tool_id=str(call["tool_id"]),
        workspace_id=state["workspace_id"],
        arguments=_arguments(call),
        bearer=state.get("bearer") or None,
        approved=bool(state.get("approved")),
    )
    transcript = list(state.get("transcript", []))
    if isinstance(outcome, _Pause):
        pending = _pending_from_pause(state, call, outcome.description)
        return _route(
            pending=pending, visible=state.get("visible", ""), transcript=transcript
        )
    result = outcome
    if state.get("approved") and not result.ok:
        return _route(
            tool_error={
                "message": result.error or TOOL_FAILED,
                "status_code": result.status_code,
            },
            transcript=transcript,
            visible=state.get("visible", ""),
        )
    transcript.append(
        {
            "role": "tool",
            "name": str(call.get("function_name") or ""),
            "response": _response_body(result),
        }
    )
    iteration = state.get("iteration", 0) + 1
    if state.get("approved") or iteration >= MAX_TOOL_ITERATIONS:
        return _route(
            force_answer=True,
            cap_note=None if state.get("approved") else CAP_NOTE,
            visible=state.get("visible", ""),
            transcript=transcript,
            iteration=iteration,
        )
    return _route(
        visible=state.get("visible", ""),
        transcript=transcript,
        iteration=iteration,
    )


async def answer(state: ChatState) -> ChatState:
    transcript = list(state.get("transcript", []))
    note = state.get("cap_note")
    if note:
        transcript.append({"role": "user", "text": note})
    context = None if state.get("approved") else state.get("context")
    text_parts: list[str] = []
    try:
        async for event in stream_model(
            system_prompt=system_prompt(context),
            contents=build_contents(transcript),
            tools=None,
        ):
            if isinstance(event, TextDelta) and event.text:
                text_parts.append(event.text)
                get_stream_writer()({"event": "message", "data": {"text": event.text}})
    except ProviderError:
        logger.exception("Chat model failed")
        return _route(error_code="provider_error", visible=_visible(state, text_parts))
    visible = _visible(state, text_parts)
    return _route(
        finished=True,
        answer=visible.strip(),
        visible=visible,
        transcript=transcript,
    )


def invoke_tool(
    *,
    tool_id: str,
    workspace_id: str,
    arguments: dict[str, Any],
    bearer: str | None,
    approved: bool,
) -> HttpToolResult | _Pause:
    """Load the tool and call the HTTP engine, or pause when HITL was skipped."""
    try:
        parsed_id = uuid.UUID(tool_id)
    except ValueError:
        return HttpToolResult(ok=False, error=ACTION_UNAVAILABLE)
    with Session(engine) as session:
        tool = session.get(ToolRegistry, parsed_id)
        if (
            tool is None
            or str(tool.workspace_id) != workspace_id
            or not tool.is_active
            or tool.kind != ToolKind.HTTP
        ):
            return HttpToolResult(ok=False, error=ACTION_UNAVAILABLE)
        if tool.requires_hitl and not approved:
            return _Pause(description=tool.description)
        return execute_http_tool(tool=tool, arguments=arguments, bearer=bearer)


def _rejected(
    state: ChatState,
    decision: RejectCall,
    transcript: list[dict[str, Any]],
    visible: str,
) -> ChatState:
    if state.get("iteration", 0) >= MAX_TOOL_ITERATIONS:
        return _route(
            force_answer=True,
            cap_note=CAP_NOTE,
            visible=visible,
            transcript=transcript,
        )
    transcript.append(
        {
            "role": "tool",
            "name": decision.function_name,
            "response": {"ok": False, "error": decision.message},
        }
    )
    return _route(
        continue_reason=True,
        iteration=state.get("iteration", 0) + 1,
        visible=visible,
        transcript=transcript,
    )


def _pending(state: ChatState, decision: RunTool, model_text: str) -> dict[str, Any]:
    summary = summary_for(decision, decision.function_args)
    return {
        "id": str(uuid.uuid4()),
        "session_id": state.get("session_id", ""),
        "workspace_id": state.get("workspace_id", ""),
        "user_id": state.get("user_id", ""),
        "tool_id": decision.tool_id,
        "arguments": decision.arguments,
        "title": plain_title(summary),
        "summary": summary,
        "function_name": decision.function_name,
        "function_args": decision.function_args,
        "model_text": model_text,
    }


def _pending_from_pause(
    state: ChatState, call: dict[str, Any], description: str
) -> dict[str, Any]:
    function_args = call.get("function_args")
    args = function_args if isinstance(function_args, dict) else {}
    arguments = call.get("arguments")
    decision = RunTool(
        tool_id=str(call.get("tool_id") or ""),
        arguments=arguments if isinstance(arguments, dict) else {},
        function_name=str(call.get("function_name") or ""),
        function_args=args,
        requires_hitl=True,
        description=description,
    )
    model_text = ""
    for turn in reversed(state.get("transcript", [])):
        if turn.get("role") == "model" and isinstance(turn.get("text"), str):
            model_text = turn["text"]
            break
    return _pending(state, decision, model_text)


def _arguments(call: dict[str, Any]) -> dict[str, Any]:
    raw = call.get("arguments")
    if isinstance(raw, dict):
        return raw
    return {}


def _tool_call(decision: RunTool) -> dict[str, Any]:
    return {
        "tool_id": decision.tool_id,
        "arguments": decision.arguments,
        "function_name": decision.function_name,
        "function_args": decision.function_args,
    }


def _response_body(result: HttpToolResult) -> dict[str, Any]:
    if not result.ok:
        return {"ok": False, "error": result.error or TOOL_FAILED}
    if result.body is None:
        return {"ok": True, "result": None}
    encoded = _bounded(result.body)
    return {"ok": True, "result": encoded}


def _bounded(body: object) -> object:
    try:
        encoded = json.dumps(body)
    except TypeError, ValueError:
        encoded = json.dumps(str(body))
    if len(encoded) <= MAX_TOOL_RESULT_CHARS:
        return body
    return encoded[:MAX_TOOL_RESULT_CHARS]


def route_start(state: ChatState) -> Literal["retrieve", "execute"]:
    if state.get("approved"):
        return "execute"
    return "retrieve"


def route_after_retrieve(state: ChatState) -> Literal["reason"] | str:
    if state.get("error_code"):
        return END
    return "reason"


def route_after_reason(
    state: ChatState,
) -> Literal["execute", "answer", "reason"] | str:
    if state.get("error_code") or state.get("pending") or state.get("finished"):
        return END
    if state.get("force_answer"):
        return "answer"
    if state.get("tool_call"):
        return "execute"
    if state.get("continue_reason"):
        return "reason"
    return END


def route_after_execute(state: ChatState) -> Literal["answer", "reason"] | str:
    if state.get("error_code") or state.get("pending") or state.get("tool_error"):
        return END
    if state.get("force_answer"):
        return "answer"
    return "reason"


def build_graph() -> Any:
    graph = StateGraph(cast(Any, ChatState))
    graph.add_node("retrieve", retrieve)
    graph.add_node("reason", reason)
    graph.add_node("execute", execute)
    graph.add_node("answer", answer)
    graph.add_conditional_edges(
        START,
        route_start,
        {"retrieve": "retrieve", "execute": "execute"},
    )
    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {"reason": "reason", END: END},
    )
    graph.add_conditional_edges(
        "reason",
        route_after_reason,
        {"execute": "execute", "answer": "answer", "reason": "reason", END: END},
    )
    graph.add_conditional_edges(
        "execute",
        route_after_execute,
        {"answer": "answer", "reason": "reason", END: END},
    )
    graph.add_edge("answer", END)
    return graph.compile()


chat_graph = build_graph()
