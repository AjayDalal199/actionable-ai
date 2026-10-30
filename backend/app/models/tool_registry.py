import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy import Column, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.models.workspace import Workspace


class ToolKind(StrEnum):
    HTTP = "http"
    JS = "js"


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class ToolRegistry(SQLModel, table=True):
    __tablename__ = "tool_registry"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "name", name="uq_tool_registry_workspace_name"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(
        foreign_key="workspace.id", nullable=False, ondelete="CASCADE"
    )
    name: str = Field(min_length=1, max_length=128)
    kind: ToolKind = Field(sa_type=String(32))
    http_method: HttpMethod | None = Field(default=None, sa_type=String(32))
    url: str | None = Field(default=None, max_length=2048)
    tool_schema: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("schema", JSONB, nullable=False, default=dict),
    )
    requires_hitl: bool = False
    description: str = Field(default="", sa_type=Text())
    is_active: bool = True
    workspace: Workspace | None = Relationship(back_populates="tools")
