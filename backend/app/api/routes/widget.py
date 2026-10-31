"""Widget channel. End-user JWTs are verified here, never with get_current_user."""

import uuid
from collections.abc import AsyncIterable
from dataclasses import dataclass
from typing import Annotated

from asyncer import asyncify
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.api.deps import SessionDep
from app.models import WidgetChatRequest, WidgetHitlRequest, WidgetToolResultRequest
from app.services.chat.errors import ChatSessionNotFound, InvalidChatMessage
from app.services.chat.hitl_store import (
    AwaitingToolCall,
    PendingAction,
    peek_awaiting,
    peek_pending,
    take_awaiting,
    take_pending,
)
from app.services.chat.orchestrate import (
    run_approve,
    run_reject,
    run_tool_result,
    run_turn_for_widget,
)
from app.services.chat.session import PreparedTurn, prepare_turn, session_in_workspace
from app.services.widget_auth import WidgetAccess, WidgetWorkspaceNotFound
from app.services.widget_auth import resolve_widget_access as resolve_access

router = APIRouter(prefix="/widget/chat", tags=["widget"])
_bearer = HTTPBearer(auto_error=False)


def _token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str | None:
    if credentials is None:
        return None
    return credentials.credentials


WidgetToken = Annotated[str | None, Depends(_token)]


def _access(
    session: SessionDep, *, workspace_key: uuid.UUID, token: str | None
) -> WidgetAccess:
    try:
        return resolve_access(session, workspace_key=workspace_key, token=token)
    except WidgetWorkspaceNotFound:
        raise HTTPException(status_code=404, detail="Workspace not found") from None


@dataclass(frozen=True, kw_only=True)
class WidgetTurn:
    prepared: PreparedTurn
    access: WidgetAccess


@dataclass(frozen=True, kw_only=True)
class WidgetDecision:
    action: PendingAction
    access: WidgetAccess
    decision: str


@dataclass(frozen=True, kw_only=True)
class WidgetToolOutcome:
    waiting: AwaitingToolCall
    ok: bool
    result: object
    error: str | None


def get_widget_turn(
    body: WidgetChatRequest, session: SessionDep, token: WidgetToken
) -> WidgetTurn:
    """Open the session before the stream so a missing session stays an HTTP 404."""
    access = _access(session, workspace_key=body.workspace_key, token=token)
    try:
        prepared = prepare_turn(
            workspace_id=access.workspace.id,
            user_id=None,
            session_id=body.session_id,
            message=body.message,
            channel="widget",
            include_js=True,
            writes=access.writes,
        )
    except InvalidChatMessage as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc
    except ChatSessionNotFound as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    return WidgetTurn(prepared=prepared, access=access)


async def get_widget_decision(
    body: WidgetHitlRequest, session: SessionDep, token: WidgetToken
) -> WidgetDecision:
    """Claim the pause before streaming. A miss is a 404, not an SSE error."""
    access = _access(session, workspace_key=body.workspace_key, token=token)
    if body.decision == "approved" and not access.writes:
        raise HTTPException(status_code=403, detail="Sign in to confirm this action.")
    action = await _take_widget_action(body.pending_action_id, access)
    return WidgetDecision(action=action, access=access, decision=body.decision)


async def get_widget_tool_outcome(
    body: WidgetToolResultRequest, session: SessionDep, token: WidgetToken
) -> WidgetToolOutcome:
    access = _access(session, workspace_key=body.workspace_key, token=token)
    waiting = await _take_widget_call(body.call_id, access)
    return WidgetToolOutcome(
        waiting=waiting, ok=body.ok, result=body.result, error=body.error
    )


WidgetTurnDep = Annotated[WidgetTurn, Depends(get_widget_turn)]
WidgetDecisionDep = Annotated[WidgetDecision, Depends(get_widget_decision)]
WidgetToolOutcomeDep = Annotated[WidgetToolOutcome, Depends(get_widget_tool_outcome)]


@router.post("/stream", response_class=EventSourceResponse)
async def stream_widget_chat(turn: WidgetTurnDep) -> AsyncIterable[ServerSentEvent]:
    """Stream a widget turn. A missing or invalid end-user JWT stays read-only."""
    async for event in run_turn_for_widget(
        turn.prepared, bearer=turn.access.token, notice=turn.access.notice
    ):
        yield ServerSentEvent(data=event.data, event=event.event)


@router.post("/hitl-confirm", response_class=EventSourceResponse)
async def confirm_widget_hitl(
    decision: WidgetDecisionDep,
) -> AsyncIterable[ServerSentEvent]:
    """Approve or reject a paused widget action.

    Approval needs a valid end-user JWT. Rejection does not call the tool.
    """
    events = (
        run_reject(decision.action)
        if decision.decision == "rejected"
        else run_approve(decision.action, bearer=decision.access.token or "")
    )
    async for event in events:
        yield ServerSentEvent(data=event.data, event=event.event)


@router.post("/tool-result", response_class=EventSourceResponse)
async def submit_widget_tool_result(
    outcome: WidgetToolOutcomeDep,
) -> AsyncIterable[ServerSentEvent]:
    """Resume after the host page runs a JavaScript tool."""
    async for event in run_tool_result(
        outcome.waiting, ok=outcome.ok, result=outcome.result, error=outcome.error
    ):
        yield ServerSentEvent(data=event.data, event=event.event)


async def _take_widget_action(
    pending_action_id: uuid.UUID, access: WidgetAccess
) -> PendingAction:
    peeked = await peek_pending(pending_action_id)
    if peeked is None or peeked.workspace_id != access.workspace.id:
        raise HTTPException(status_code=404, detail="Pending action not found")
    belongs = await asyncify(session_in_workspace)(
        session_id=peeked.session_id,
        workspace_id=access.workspace.id,
    )
    if not belongs:
        await take_pending(pending_action_id, workspace_id=access.workspace.id)
        raise HTTPException(status_code=404, detail="Pending action not found")
    action = await take_pending(pending_action_id, workspace_id=access.workspace.id)
    if action is None:
        raise HTTPException(status_code=404, detail="Pending action not found")
    return action


async def _take_widget_call(
    call_id: uuid.UUID, access: WidgetAccess
) -> AwaitingToolCall:
    peeked = await peek_awaiting(call_id)
    if peeked is None or peeked.workspace_id != access.workspace.id:
        raise HTTPException(status_code=404, detail="Tool call not found")
    if peeked.requires_hitl and not access.writes:
        raise HTTPException(status_code=403, detail="Sign in to finish this action.")
    waiting = await take_awaiting(call_id, workspace_id=access.workspace.id)
    if waiting is None:
        raise HTTPException(status_code=404, detail="Tool call not found")
    return waiting
