"""Persist internal chat sessions and the transcript used to resume HITL."""

import uuid
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.core.db import engine
from app.models import ChatMessage, ChatSession
from app.services.chat.catalog import ToolView, load_http_tools
from app.services.chat.errors import ChatSessionNotFound, InvalidChatMessage
from app.services.chat.limits import MAX_HISTORY_MESSAGES, MAX_HISTORY_TOKENS
from app.services.chat.plain import truncate_user_text
from app.services.knowledge.limits import APPROX_CHARS_PER_TOKEN


@dataclass(frozen=True, kw_only=True)
class TranscriptTurn:
    role: str
    content: str


@dataclass(frozen=True, kw_only=True)
class PreparedTurn:
    session_id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    text: str
    history: list[TranscriptTurn]
    tools: list[ToolView]


def prepare_turn(
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    message: str,
) -> PreparedTurn:
    text = truncate_user_text(message)
    if not text:
        raise InvalidChatMessage("Message cannot be blank.")
    with Session(engine) as session:
        _open_session(
            session,
            session_id=session_id,
            workspace_id=workspace_id,
            user_id=user_id,
        )
        _record(
            session,
            session_id=session_id,
            workspace_id=workspace_id,
            role="user",
            content=text,
        )
        history = _history(session, session_id=session_id, workspace_id=workspace_id)
        tools = load_http_tools(session=session, workspace_id=workspace_id)
    return PreparedTurn(
        session_id=session_id,
        workspace_id=workspace_id,
        user_id=user_id,
        text=text,
        history=history,
        tools=tools,
    )


def record_assistant(
    *, session_id: uuid.UUID, workspace_id: uuid.UUID, content: str
) -> None:
    text = content.strip()
    if not text:
        return
    with Session(engine) as session:
        row = session.get(ChatSession, session_id)
        if row is None or row.workspace_id != workspace_id:
            return
        _record(
            session,
            session_id=session_id,
            workspace_id=workspace_id,
            role="assistant",
            content=text,
        )


def load_transcript(
    *, session_id: uuid.UUID, workspace_id: uuid.UUID
) -> list[TranscriptTurn]:
    with Session(engine) as session:
        return _history(session, session_id=session_id, workspace_id=workspace_id)


def session_in_workspace(*, session_id: uuid.UUID, workspace_id: uuid.UUID) -> bool:
    with Session(engine) as session:
        row = session.get(ChatSession, session_id)
        return row is not None and row.workspace_id == workspace_id


def _open_session(
    session: Session,
    *,
    session_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ChatSession:
    existing = session.get(ChatSession, session_id)
    if existing is not None:
        if existing.workspace_id != workspace_id:
            raise ChatSessionNotFound("Chat session not found")
        return existing
    created = ChatSession(
        id=session_id,
        workspace_id=workspace_id,
        user_id=user_id,
        channel="internal",
    )
    session.add(created)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.get(ChatSession, session_id)
        if existing is None or existing.workspace_id != workspace_id:
            raise ChatSessionNotFound("Chat session not found") from None
        return existing
    session.refresh(created)
    return created


def _record(
    session: Session,
    *,
    session_id: uuid.UUID,
    workspace_id: uuid.UUID,
    role: str,
    content: str,
) -> None:
    session.add(
        ChatMessage(
            session_id=session_id,
            workspace_id=workspace_id,
            role=role,
            content=content,
        )
    )
    session.commit()


def _history(
    session: Session, *, session_id: uuid.UUID, workspace_id: uuid.UUID
) -> list[TranscriptTurn]:
    rows = session.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .where(ChatMessage.workspace_id == workspace_id)
        .order_by(col(ChatMessage.created_at), col(ChatMessage.id))
    ).all()
    turns = [
        TranscriptTurn(role=row.role, content=row.content)
        for row in rows
        if row.role in {"user", "assistant"} and row.content.strip()
    ]
    if len(turns) > MAX_HISTORY_MESSAGES:
        turns = turns[-MAX_HISTORY_MESSAGES:]
    kept: list[TranscriptTurn] = []
    used = 0
    for turn in reversed(turns):
        cost = max(1, len(turn.content) // APPROX_CHARS_PER_TOKEN)
        if kept and used + cost > MAX_HISTORY_TOKENS:
            break
        kept.append(turn)
        used += cost
    kept.reverse()
    return kept
