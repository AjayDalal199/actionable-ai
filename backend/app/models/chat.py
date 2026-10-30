import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import Text
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc
from app.models.workspace import Workspace


class ChatSession(SQLModel, table=True):
    """One internal conversation, keyed by the client session id and workspace."""

    __tablename__ = "chat_session"

    id: uuid.UUID = Field(primary_key=True)
    workspace_id: uuid.UUID = Field(
        foreign_key="workspace.id", nullable=False, ondelete="CASCADE", index=True
    )
    user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL"
    )
    channel: str = Field(default="internal", max_length=32)
    created_at: datetime | None = Field(default_factory=get_datetime_utc)
    workspace: Workspace | None = Relationship(back_populates="chat_sessions")
    messages: list["ChatMessage"] = Relationship(  # noqa: UP037
        back_populates="session", cascade_delete=True
    )


class ChatMessage(SQLModel, table=True):
    """A user or assistant turn, kept so HITL can resume and escalation can attach a transcript."""

    __tablename__ = "chat_message"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(
        foreign_key="chat_session.id", nullable=False, ondelete="CASCADE", index=True
    )
    workspace_id: uuid.UUID = Field(
        foreign_key="workspace.id", nullable=False, ondelete="CASCADE", index=True
    )
    role: str = Field(max_length=32)
    content: str = Field(sa_type=Text())
    created_at: datetime | None = Field(default_factory=get_datetime_utc)
    session: ChatSession | None = Relationship(back_populates="messages")


class ChatStreamRequest(SQLModel):
    session_id: uuid.UUID
    message: str = Field(min_length=1, max_length=100_000)
    channel: Literal["internal"]


class HitlConfirmRequest(SQLModel):
    pending_action_id: uuid.UUID
    decision: Literal["approved", "rejected"]
