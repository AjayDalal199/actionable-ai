"""Run one chat turn and the HITL or JavaScript-tool resume that follows it."""

import json
import logging
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, cast

from asyncer import asyncify
from pydantic import ValidationError
from redis.exceptions import RedisError

from app.services.chat.errors import (
    DONE_MESSAGE,
    EMPTY_ANSWER,
    PROVIDER_MESSAGE,
    REJECT_MESSAGE,
    UNAVAILABLE_MESSAGE,
    UNKNOWN_MESSAGE,
)
from app.services.chat.graph import ChatState, chat_graph
from app.services.chat.hitl_store import (
    AwaitingToolCall,
    PendingAction,
    save_awaiting,
    save_pending,
)
from app.services.chat.limits import MAX_TOOL_RESULT_CHARS
from app.services.chat.plain import plain_summary, plain_title
from app.services.chat.session import (
    PreparedTurn,
    record_assistant,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ChatEvent:
    event: str
    data: dict[str, Any]


async def run_turn_for_member(
    prepared: PreparedTurn, *, bearer: str, user_id: uuid.UUID
) -> AsyncIterator[ChatEvent]:
    state = _base_state(prepared, bearer=bearer, user_id=user_id, audience="internal")
    async for event in _finish(state, user_id=user_id):
        yield event


async def run_turn_for_widget(
    prepared: PreparedTurn, *, bearer: str | None, notice: str | None
) -> AsyncIterator[ChatEvent]:
    if notice:
        yield ChatEvent(event="notice", data={"message": notice})
    state = _base_state(prepared, bearer=bearer or "", user_id=None, audience="widget")
    async for event in _finish(state, user_id=None):
        yield event


async def run_reject(action: PendingAction) -> AsyncIterator[ChatEvent]:
    await _record(action.session_id, action.workspace_id, REJECT_MESSAGE)
    yield ChatEvent(event="message", data={"text": REJECT_MESSAGE})
    yield _done()


async def run_approve(
    action: PendingAction, *, bearer: str
) -> AsyncIterator[ChatEvent]:
    if action.kind == "js":
        async for event in _emit_js(
            session_id=action.session_id,
            workspace_id=action.workspace_id,
            tool_name=action.tool_name or action.function_name,
            arguments=action.arguments,
            function_name=action.function_name,
            function_args=action.function_args,
            model_text=action.model_text,
            requires_hitl=True,
        ):
            yield event
        return
    from app.services.chat.session import load_transcript

    history = await asyncify(load_transcript)(
        session_id=action.session_id,
        workspace_id=action.workspace_id,
    )
    transcript: list[dict[str, Any]] = [
        {
            "role": "user" if turn.role == "user" else "model",
            "text": turn.content,
        }
        for turn in history
    ]
    transcript.append(
        {
            "role": "model",
            "text": action.model_text,
            "call": {
                "name": action.function_name,
                "args": action.function_args,
            },
        }
    )
    state: ChatState = {
        "session_id": str(action.session_id),
        "workspace_id": str(action.workspace_id),
        "user_id": str(action.user_id),
        "bearer": bearer,
        "user_text": "",
        "context": None,
        "has_context": True,
        "tools": [],
        "transcript": transcript,
        "visible": "",
        "iteration": 0,
        "approved": True,
        "tool_call": {
            "tool_id": str(action.tool_id),
            "arguments": action.arguments,
            "function_name": action.function_name,
            "function_args": action.function_args,
        },
        "pending": None,
        "force_answer": False,
        "cap_note": None,
        "continue_reason": False,
        "finished": False,
        "error_code": None,
        "tool_error": None,
        "answer": "",
    }
    async for event in _finish(state, user_id=action.user_id):
        yield event


async def run_tool_result(
    waiting: AwaitingToolCall, *, ok: bool, result: object, error: str | None
) -> AsyncIterator[ChatEvent]:
    from app.services.chat.session import load_transcript

    history = await asyncify(load_transcript)(
        session_id=waiting.session_id,
        workspace_id=waiting.workspace_id,
    )
    transcript: list[dict[str, Any]] = [
        {
            "role": "user" if turn.role == "user" else "model",
            "text": turn.content,
        }
        for turn in history
    ]
    transcript.append(
        {
            "role": "model",
            "text": waiting.model_text,
            "call": {"name": waiting.function_name, "args": waiting.function_args},
        }
    )
    transcript.append(
        {
            "role": "tool",
            "name": waiting.function_name,
            "response": _js_response(ok=ok, result=result, error=error),
        }
    )
    state: ChatState = {
        "session_id": str(waiting.session_id),
        "workspace_id": str(waiting.workspace_id),
        "user_id": "",
        "bearer": "",
        "user_text": "",
        "context": None,
        "has_context": True,
        "tools": [],
        "transcript": transcript,
        "visible": "",
        "iteration": 0,
        "approved": False,
        "tool_call": None,
        "pending": None,
        "force_answer": False,
        "cap_note": None,
        "continue_reason": False,
        "finished": False,
        "error_code": None,
        "tool_error": None,
        "answer": "",
        "js_call": None,
        "resume_answer": True,
        "audience": "widget",
    }
    async for event in _finish(state, user_id=None):
        yield event


def _base_state(
    prepared: PreparedTurn,
    *,
    bearer: str,
    user_id: uuid.UUID | None,
    audience: str,
) -> ChatState:
    return {
        "session_id": str(prepared.session_id),
        "workspace_id": str(prepared.workspace_id),
        "user_id": "" if user_id is None else str(user_id),
        "bearer": bearer,
        "audience": audience,
        "user_text": prepared.text,
        "context": None,
        "has_context": False,
        "tools": [tool.as_dict() for tool in prepared.tools],
        "transcript": [
            {
                "role": "user" if turn.role == "user" else "model",
                "text": turn.content,
            }
            for turn in prepared.history
        ],
        "visible": "",
        "iteration": 0,
        "approved": False,
        "tool_call": None,
        "pending": None,
        "force_answer": False,
        "cap_note": None,
        "continue_reason": False,
        "finished": False,
        "error_code": None,
        "tool_error": None,
        "answer": "",
        "js_call": None,
        "resume_answer": False,
    }


async def _finish(
    state: ChatState, *, user_id: uuid.UUID | None
) -> AsyncIterator[ChatEvent]:
    final: ChatState = {}
    try:
        async for mode, chunk in chat_graph.astream(
            state, stream_mode=["custom", "values"]
        ):
            if mode == "custom" and isinstance(chunk, dict):
                event_name = chunk.get("event")
                data = chunk.get("data")
                if isinstance(event_name, str) and isinstance(data, dict):
                    yield ChatEvent(event=event_name, data=data)
            elif mode == "values" and isinstance(chunk, dict):
                final = cast(ChatState, chunk)
    except Exception:
        logger.exception("Chat graph failed")
        yield _error("provider_error", PROVIDER_MESSAGE)
        yield _done()
        return

    session_id = _uuid(final.get("session_id"))
    workspace_id = _uuid(final.get("workspace_id"))
    if final.get("error_code"):
        await _record(session_id, workspace_id, str(final.get("visible") or ""))
        yield _error("provider_error", PROVIDER_MESSAGE)
        yield _done()
        return
    pending = final.get("pending")
    if isinstance(pending, dict):
        async for event in _pause(pending, user_id=user_id):
            yield event
        return
    js_call = final.get("js_call")
    if isinstance(js_call, dict):
        async for event in _emit_js_from_call(js_call, final):
            yield event
        return
    tool_error = final.get("tool_error")
    if isinstance(tool_error, dict):
        message = str(tool_error.get("message") or "The action failed.")
        await _record(session_id, workspace_id, message)
        payload: dict[str, Any] = {"code": "tool_failed", "message": message}
        status_code = tool_error.get("status_code")
        if isinstance(status_code, int):
            payload["status_code"] = status_code
        yield ChatEvent(event="error", data=payload)
        yield _done()
        return

    visible = str(final.get("visible") or "").strip()
    if not visible:
        if final.get("approved"):
            visible = DONE_MESSAGE
        elif final.get("has_context"):
            visible = EMPTY_ANSWER
        else:
            visible = UNKNOWN_MESSAGE
        yield ChatEvent(event="message", data={"text": visible})
    await _record(session_id, workspace_id, visible)
    yield _done()


async def _pause(
    pending: dict[str, Any], *, user_id: uuid.UUID | None
) -> AsyncIterator[ChatEvent]:
    try:
        pending = {**pending, "user_id": None if user_id is None else str(user_id)}
        action = PendingAction.model_validate(pending)
    except ValidationError:
        logger.exception("Pending action was not valid")
        yield _error("provider_error", PROVIDER_MESSAGE)
        yield _done()
        return
    summary = plain_summary(action.summary)
    card = {
        "pending_action_id": str(action.id),
        "title": plain_title(summary),
        "summary": summary,
    }
    try:
        await save_pending(
            action.model_copy(update={"title": card["title"], "summary": summary})
        )
    except RedisError:
        logger.exception("Could not store the pending action")
        yield _error("unavailable", UNAVAILABLE_MESSAGE)
        yield _done()
        return
    visible = str(pending.get("model_text") or "").strip()
    if visible and visible != summary:
        await _record(action.session_id, action.workspace_id, visible)
    await _record(action.session_id, action.workspace_id, summary)
    yield ChatEvent(event="hitl_required", data=card)
    yield _done()


async def _record(
    session_id: uuid.UUID | None, workspace_id: uuid.UUID | None, content: str
) -> None:
    if session_id is None or workspace_id is None or not content.strip():
        return
    try:
        await asyncify(record_assistant)(
            session_id=session_id,
            workspace_id=workspace_id,
            content=content,
        )
    except Exception:
        logger.exception("Could not store the chat transcript")


def _uuid(value: object) -> uuid.UUID | None:
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            return None
    return None


async def _emit_js_from_call(
    js_call: dict[str, Any], final: ChatState
) -> AsyncIterator[ChatEvent]:
    session_id = _uuid(final.get("session_id"))
    workspace_id = _uuid(final.get("workspace_id"))
    if session_id is None or workspace_id is None:
        yield _error("provider_error", PROVIDER_MESSAGE)
        yield _done()
        return
    arguments = js_call.get("arguments")
    function_args = js_call.get("function_args")
    tool_name = js_call.get("tool_name")
    function_name = js_call.get("function_name")
    if not isinstance(tool_name, str) or not tool_name:
        tool_name = function_name if isinstance(function_name, str) else ""
    if not isinstance(function_name, str) or not function_name:
        function_name = tool_name
    model_text = ""
    transcript = final.get("transcript")
    if isinstance(transcript, list):
        for turn in reversed(transcript):
            if (
                isinstance(turn, dict)
                and turn.get("role") == "model"
                and isinstance(turn.get("text"), str)
            ):
                model_text = turn["text"]
                break
    async for event in _emit_js(
        session_id=session_id,
        workspace_id=workspace_id,
        tool_name=tool_name,
        arguments=arguments if isinstance(arguments, dict) else {},
        function_name=function_name,
        function_args=function_args if isinstance(function_args, dict) else {},
        model_text=model_text,
        requires_hitl=bool(js_call.get("requires_hitl")),
    ):
        yield event


async def _emit_js(
    *,
    session_id: uuid.UUID,
    workspace_id: uuid.UUID,
    tool_name: str,
    arguments: dict[str, Any],
    function_name: str,
    function_args: dict[str, Any],
    model_text: str,
    requires_hitl: bool,
) -> AsyncIterator[ChatEvent]:
    waiting = AwaitingToolCall(
        id=uuid.uuid4(),
        session_id=session_id,
        workspace_id=workspace_id,
        tool_name=tool_name,
        arguments=arguments,
        function_name=function_name,
        function_args=function_args,
        model_text=model_text,
        requires_hitl=requires_hitl,
    )
    visible = model_text.strip()
    if visible:
        await _record(session_id, workspace_id, visible)
    try:
        await save_awaiting(waiting)
    except RedisError:
        logger.exception("Could not store the JavaScript tool call")
        yield _error("unavailable", UNAVAILABLE_MESSAGE)
        yield _done()
        return
    yield ChatEvent(
        event="tool_js",
        data={
            "call_id": str(waiting.id),
            "name": waiting.tool_name,
            "arguments": waiting.arguments,
        },
    )
    yield _done()


def _js_response(*, ok: bool, result: object, error: str | None) -> dict[str, Any]:
    if not ok:
        message = (error or "The action failed.").strip() or "The action failed."
        return {"ok": False, "error": message[:500]}
    return {"ok": True, "result": _bounded_result(result)}


def _bounded_result(result: object) -> object:
    try:
        encoded = json.dumps(result, default=str)
    except TypeError, ValueError:
        encoded = json.dumps(str(result))
    if len(encoded) <= MAX_TOOL_RESULT_CHARS:
        return result
    return encoded[:MAX_TOOL_RESULT_CHARS]


def _error(code: str, message: str) -> ChatEvent:
    return ChatEvent(event="error", data={"code": code, "message": message})


def _done() -> ChatEvent:
    return ChatEvent(event="done", data={"status": "done"})
