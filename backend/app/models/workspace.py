import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import EmailStr, field_validator
from sqlalchemy import DateTime, String
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc

if TYPE_CHECKING:
    from app.models.user import User


class WorkspaceRole(StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


def normalize_workspace_name(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Name cannot be blank")
    return stripped


class WorkspaceMembership(SQLModel, table=True):
    __tablename__ = "workspace_membership"

    user_id: uuid.UUID = Field(
        foreign_key="user.id", primary_key=True, ondelete="CASCADE"
    )
    workspace_id: uuid.UUID = Field(
        foreign_key="workspace.id", primary_key=True, ondelete="CASCADE", index=True
    )
    role: WorkspaceRole = Field(sa_type=String(32))  # type: ignore
    invitation_status: InvitationStatus = Field(
        default=InvitationStatus.ACCEPTED,
        sa_type=String(32),  # type: ignore
    )
    is_active: bool = True
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    user: "User" = Relationship(back_populates="memberships")  # noqa: UP037
    workspace: "Workspace" = Relationship(back_populates="memberships")  # noqa: UP037


class Workspace(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(min_length=1, max_length=255)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    created_by_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        ondelete="SET NULL",
        unique=True,
    )
    memberships: list[WorkspaceMembership] = Relationship(
        back_populates="workspace", cascade_delete=True
    )


class WorkspaceCreate(SQLModel):
    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        return normalize_workspace_name(value)


class WorkspaceUpdate(WorkspaceCreate):
    pass


class WorkspaceSelect(SQLModel):
    workspace_id: uuid.UUID


class WorkspacePublic(SQLModel):
    id: uuid.UUID
    name: str
    created_at: datetime | None = None


class WorkspaceListItem(WorkspacePublic):
    role: WorkspaceRole
    is_current: bool


class WorkspacesPublic(SQLModel):
    data: list[WorkspaceListItem]
    count: int
    can_create: bool


class WorkspaceInvite(SQLModel):
    email: EmailStr = Field(max_length=255)
    role: WorkspaceRole
    full_name: str | None = Field(default=None, max_length=255)


class WorkspaceMemberUpdate(SQLModel):
    role: WorkspaceRole | None = None
    is_active: bool | None = None


class WorkspaceMemberPublic(SQLModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    role: WorkspaceRole
    invitation_status: InvitationStatus
    is_active: bool
    created_at: datetime | None = None


class WorkspaceInvitePreview(SQLModel):
    email: EmailStr
    workspace_name: str
    role: WorkspaceRole
    status: InvitationStatus
    needs_password: bool


class WorkspaceInviteAction(SQLModel):
    token: str
    password: str | None = Field(default=None, min_length=8, max_length=128)


class WorkspaceMembersPublic(SQLModel):
    data: list[WorkspaceMemberPublic]
    count: int
