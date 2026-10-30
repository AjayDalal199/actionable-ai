"""Internal chat SSE. The widget channel is not accepted here."""

from collections.abc import AsyncIterable
from typing import Annotated

from asyncer import asyncify
from fastapi import APIRouter, Depends, HTTPException
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.api.deps import CurrentUser, CurrentWorkspace, TokenDep
from app.models import ChatStreamRequest, HitlConfirmRequest
from app.services.chat.errors import ChatSessionNotFound, InvalidChatMessage
from app.services.chat.hitl_store import PendingAction, peek_pending, take_pending
from app.services.chat.orchestrate import run_approve, run_reject, run_turn_for_member
from app.services.chat.session import PreparedTurn, prepare_turn, session_in_workspace

router = APIRouter(prefix="/chat", tags=["chat"])


def get_prepared_turn(
    body: ChatStreamRequest,
    workspace: CurrentWorkspace,
    user: CurrentUser,
) -> PreparedTurn:
    """Open the session before the stream starts so errors stay HTTP responses."""
    try:
        return prepare_turn(
            workspace_id=workspace.id,
            user_id=user.id,
            session_id=body.session_id,
            message=body.message,
        )
    except InvalidChatMessage as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc
    except ChatSessionNotFound as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


PreparedTurnDep = Annotated[PreparedTurn, Depends(get_prepared_turn)]


async def get_pending_action(
    body: HitlConfirmRequest,
    workspace: CurrentWorkspace,
) -> PendingAction:
    """Claim the pause before streaming. A miss is a 404, not an SSE error."""
    peeked = await peek_pending(body.pending_action_id)
    if peeked is None or peeked.workspace_id != workspace.id:
        raise HTTPException(status_code=404, detail="Pending action not found")
    belongs = await asyncify(session_in_workspace)(
        session_id=peeked.session_id,
        workspace_id=workspace.id,
    )
    if not belongs:
        await take_pending(body.pending_action_id, workspace_id=workspace.id)
        raise HTTPException(status_code=404, detail="Pending action not found")
    action = await take_pending(body.pending_action_id, workspace_id=workspace.id)
    if action is None:
        raise HTTPException(status_code=404, detail="Pending action not found")
    return action


PendingActionDep = Annotated[PendingAction, Depends(get_pending_action)]


@router.post("/stream", response_class=EventSourceResponse)
async def stream_chat(
    prepared: PreparedTurnDep,
    token: TokenDep,
) -> AsyncIterable[ServerSentEvent]:
    """Stream an internal chat turn for a logged-in workspace member.

    The member's access token is the bearer for HTTP tools. Writes pause for
    confirmation before the API request engine is called.
    """
    async for event in run_turn_for_member(
        prepared, bearer=token, user_id=prepared.user_id
    ):
        yield ServerSentEvent(data=event.data, event=event.event)


@router.post("/hitl-confirm", response_class=EventSourceResponse)
async def confirm_hitl(
    body: HitlConfirmRequest,
    action: PendingActionDep,
    token: TokenDep,
) -> AsyncIterable[ServerSentEvent]:
    """Approve or reject a paused action for the current workspace.

    Approval calls the registered HTTP tool with this member's token and
    streams the outcome. Rejection does not call the tool.
    """
    events = (
        run_reject(action)
        if body.decision == "rejected"
        else run_approve(action, bearer=token)
    )
    async for event in events:
        yield ServerSentEvent(data=event.data, event=event.event)
