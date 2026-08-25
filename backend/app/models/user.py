import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import EmailStr, field_validator
from sqlalchemy import DateTime, String
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc
from app.models.workspace import Workspace, WorkspaceRole, normalize_workspace_name

if TYPE_CHECKING:
    from app.models.item import Item


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    workspace_name: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("workspace_name")
    @classmethod
    def workspace_name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_workspace_name(value)


class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    workspace_id: uuid.UUID | None = Field(
        default=None, foreign_key="workspace.id", ondelete="SET NULL", index=True
    )
    role: WorkspaceRole | None = Field(default=None, sa_type=String(32))  # type: ignore
    workspace: Workspace | None = Relationship(back_populates="users")
    items: list[Item] = Relationship(back_populates="owner", cascade_delete=True)


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int
