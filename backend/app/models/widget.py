import uuid
from typing import Any, Literal

from sqlmodel import Field, SQLModel


class WidgetInstallPublic(SQLModel):
    workspace_key: uuid.UUID
    secret: str | None = None


class WidgetPreviewToken(SQLModel):
    token: str
    expires_in: int


class WidgetChatRequest(SQLModel):
    session_id: uuid.UUID
    message: str = Field(min_length=1, max_length=100_000)
    workspace_key: uuid.UUID


class WidgetHitlRequest(SQLModel):
    pending_action_id: uuid.UUID
    decision: Literal["approved", "rejected"]
    workspace_key: uuid.UUID


class WidgetToolResultRequest(SQLModel):
    call_id: uuid.UUID
    workspace_key: uuid.UUID
    ok: bool
    result: Any = None
    error: str | None = Field(default=None, max_length=500)
