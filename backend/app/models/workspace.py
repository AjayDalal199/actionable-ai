import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import field_validator
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc

if TYPE_CHECKING:
    from app.models.user import User


class WorkspaceRole(StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


def normalize_workspace_name(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Name cannot be blank")
    return stripped


class Workspace(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(min_length=1, max_length=255)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    users: list[User] = Relationship(back_populates="workspace")


class WorkspaceCreate(SQLModel):
    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        return normalize_workspace_name(value)


class WorkspaceUpdate(WorkspaceCreate):
    pass


class WorkspacePublic(SQLModel):
    id: uuid.UUID
    name: str
    created_at: datetime | None = None
