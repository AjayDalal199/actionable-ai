import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.core.embeddings import EMBEDDING_DIMENSION
from app.models.base import get_datetime_utc
from app.models.workspace import Workspace


class DocumentType(StrEnum):
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"


class DocumentStatus(StrEnum):
    PROCESSING = "processing"
    ACTIVE = "active"
    FAILED = "failed"


class Document(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(
        foreign_key="workspace.id", nullable=False, ondelete="CASCADE", index=True
    )
    title: str = Field(min_length=1, max_length=255)
    type: DocumentType = Field(sa_type=String(32))
    status: DocumentStatus = Field(sa_type=String(32))
    original_filename: str = Field(min_length=1, max_length=512)
    error_message: str | None = Field(default=None, sa_type=Text())
    created_at: datetime | None = Field(default_factory=get_datetime_utc)
    workspace: Workspace | None = Relationship(back_populates="documents")
    chunks: list["DocumentChunk"] = Relationship(  # noqa: UP037
        back_populates="document", cascade_delete=True
    )


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunk"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "chunk_index", name="uq_document_chunk_position"
        ),
        Index(
            "ix_document_chunk_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(
        foreign_key="document.id", nullable=False, ondelete="CASCADE"
    )
    content: str = Field(sa_type=Text())
    embedding: list[float] = Field(
        sa_column=Column(Vector(EMBEDDING_DIMENSION), nullable=False)
    )
    chunk_index: int = Field(ge=0)
    chunk_metadata: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column("metadata", JSONB, nullable=True),
    )
    document: Document | None = Relationship(back_populates="chunks")


class DocumentPublic(SQLModel):
    id: uuid.UUID
    title: str
    original_filename: str
    type: DocumentType
    status: DocumentStatus
    error_message: str | None
    created_at: datetime | None


class DocumentsPublic(SQLModel):
    data: list[DocumentPublic]
    count: int


class DocumentUploadResponse(SQLModel):
    document_id: uuid.UUID
    status: DocumentStatus
    message: str
