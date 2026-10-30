"""Run one internal turn and the HITL resume that follows it."""

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
from app.services.chat.hitl_store import PendingAction, save_pending
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
    state = _base_state(prepared, bearer=bearer, user_id=user_id)
    async for event in _finish(state, user_id=user_id):
        yield event


async def run_reject(action: PendingAction) -> AsyncIterator[ChatEvent]:
    await _record(action.session_id, action.workspace_id, REJECT_MESSAGE)
    yield ChatEvent(event="message", data={"text": REJECT_MESSAGE})
    yield _done()


async def run_approve(
    action: PendingAction, *, bearer: str
) -> AsyncIterator[ChatEvent]:
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


def _base_state(
    prepared: PreparedTurn, *, bearer: str, user_id: uuid.UUID
) -> ChatState:
    return {
        "session_id": str(prepared.session_id),
        "workspace_id": str(prepared.workspace_id),
        "user_id": str(user_id),
        "bearer": bearer,
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
    }


async def _finish(state: ChatState, *, user_id: uuid.UUID) -> AsyncIterator[ChatEvent]:
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
    pending: dict[str, Any], *, user_id: uuid.UUID
) -> AsyncIterator[ChatEvent]:
    try:
        pending = {**pending, "user_id": str(user_id)}
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


def _error(code: str, message: str) -> ChatEvent:
    return ChatEvent(event="error", data={"code": code, "message": message})


def _done() -> ChatEvent:
    return ChatEvent(event="done", data={"status": "done"})
