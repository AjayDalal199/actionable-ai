import uuid
from enum import StrEnum
from typing import Any, Literal

from sqlalchemy import Column, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.main import SQLModelConfig

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


class ToolRegister(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str
    kind: ToolKind | None = None
    http_method: HttpMethod | None = None
    url: str | None = None
    requires_hitl: bool = False
    description: str = ""
    tool_schema: dict[str, Any] = Field(alias="schema")


class ToolUpdate(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    http_method: HttpMethod | None = None
    url: str | None = None
    description: str | None = None
    requires_hitl: bool | None = None
    tool_schema: dict[str, Any] | None = Field(default=None, alias="schema")


class ToolPublic(SQLModel):
    id: uuid.UUID
    name: str
    kind: ToolKind
    http_method: HttpMethod | None
    url: str | None
    tool_schema: dict[str, Any] = Field(serialization_alias="schema")
    requires_hitl: bool
    description: str
    is_active: bool


class ToolsPublic(SQLModel):
    data: list[ToolPublic]
    count: int


class ToolRegisterResponse(SQLModel):
    tool_id: uuid.UUID
    status: Literal["active"]
