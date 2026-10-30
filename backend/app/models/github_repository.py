import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from app.models.workspace import Workspace


class GithubRepository(SQLModel, table=True):
    """Table only. No OAuth, webhooks, or sync workers in the MVP."""

    __tablename__ = "github_repository"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(
        foreign_key="workspace.id", nullable=False, ondelete="CASCADE", index=True
    )
    url: str = Field(min_length=1, max_length=2048)
    target_branch: str = Field(min_length=1, max_length=255)
    last_sync: datetime | None = Field(default=None)
    workspace: Workspace | None = Relationship(back_populates="github_repositories")
