import uuid
from collections.abc import Generator

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError
from sqlmodel import Session, select

from app.core.config import Settings, settings
from app.core.embeddings import EMBEDDING_DIMENSION, EMBEDDING_MODEL
from app.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    DocumentType,
    GithubRepository,
    HttpMethod,
    ToolKind,
    ToolRegistry,
    Workspace,
)


def _vector(*hot_indexes: int) -> list[float]:
    values = [0.0] * EMBEDDING_DIMENSION
    for index in hot_indexes:
        values[index] = 1.0
    return values


@pytest.fixture
def workspace(db: Session) -> Generator[Workspace]:
    row = Workspace(name=f"Vector lab {uuid.uuid4()}")
    db.add(row)
    db.commit()
    db.refresh(row)
    try:
        yield row
    finally:
        db.rollback()
        documents = db.exec(
            select(Document).where(Document.workspace_id == row.id)
        ).all()
        for document in documents:
            for chunk in db.exec(
                select(DocumentChunk).where(DocumentChunk.document_id == document.id)
            ).all():
                db.delete(chunk)
            db.delete(document)
        for tool in db.exec(
            select(ToolRegistry).where(ToolRegistry.workspace_id == row.id)
        ).all():
            db.delete(tool)
        for repo in db.exec(
            select(GithubRepository).where(GithubRepository.workspace_id == row.id)
        ).all():
            db.delete(repo)
        db.delete(row)
        db.commit()


def test_vector_extension_is_installed(db: Session) -> None:
    name = db.execute(
        text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
    ).scalar_one()
    index = db.execute(
        text(
            "SELECT indexdef FROM pg_indexes "
            "WHERE indexname = 'ix_document_chunk_embedding_hnsw'"
        )
    ).scalar_one()
    assert name == "vector"
    assert "hnsw" in index
    assert "vector_cosine_ops" in index


def test_embedding_settings_match_the_column() -> None:
    assert settings.EMBEDDING_MODEL == EMBEDDING_MODEL
    assert settings.EMBEDDING_DIMENSION == EMBEDDING_DIMENSION == 1536


def test_embedding_dimension_rejects_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_DIMENSION", "3")
    with pytest.raises(ValidationError, match="document_chunk.embedding"):
        Settings()  # type: ignore[call-arg]


def test_embedding_model_rejects_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_MODEL", "gemini-embedding-001")
    with pytest.raises(ValidationError, match="document_chunk.embedding"):
        Settings()  # type: ignore[call-arg]


def test_document_chunk_round_trip_and_cosine_order(
    db: Session, workspace: Workspace
) -> None:
    document = Document(
        workspace_id=workspace.id,
        title="Handbook",
        type=DocumentType.MARKDOWN,
        status=DocumentStatus.ACTIVE,
        original_filename="handbook.md",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    near = DocumentChunk(
        document_id=document.id,
        content="refunds",
        embedding=_vector(0),
        chunk_index=0,
        chunk_metadata={"page": 1},
    )
    far = DocumentChunk(
        document_id=document.id,
        content="billing",
        embedding=_vector(1),
        chunk_index=1,
    )
    db.add(near)
    db.add(far)
    db.commit()

    nearest_id = db.execute(
        text(
            "SELECT id FROM document_chunk "
            "WHERE document_id = :document_id "
            "ORDER BY embedding <=> CAST(:query AS vector) "
            "LIMIT 1"
        ),
        {"document_id": document.id, "query": str(_vector(0))},
    ).scalar_one()
    stored = db.get(DocumentChunk, near.id)
    assert stored is not None
    assert stored.chunk_metadata == {"page": 1}
    assert len(stored.embedding) == EMBEDDING_DIMENSION
    assert nearest_id == near.id

    db.add(
        DocumentChunk(
            document_id=document.id,
            content="duplicate",
            embedding=_vector(2),
            chunk_index=0,
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_embedding_rejects_the_wrong_dimension(
    db: Session, workspace: Workspace
) -> None:
    document = Document(
        workspace_id=workspace.id,
        title="Short",
        type=DocumentType.TEXT,
        status=DocumentStatus.PROCESSING,
        original_filename="note.txt",
    )
    db.add(document)
    db.commit()
    db.add(
        DocumentChunk(
            document_id=document.id,
            content="nope",
            embedding=[1.0, 0.0],
            chunk_index=0,
        )
    )
    with pytest.raises(DataError):
        db.commit()
    db.rollback()


def test_tool_name_is_unique_per_workspace(db: Session, workspace: Workspace) -> None:
    other = Workspace(name=f"Other {uuid.uuid4()}")
    db.add(other)
    db.commit()
    db.refresh(other)
    try:
        shared = {
            "name": "refund_user",
            "kind": ToolKind.HTTP,
            "http_method": HttpMethod.POST,
            "url": "https://example.com/refund",
            "tool_schema": {"type": "object", "properties": {}},
            "requires_hitl": True,
            "description": "Refund a customer",
        }
        db.add(ToolRegistry(workspace_id=workspace.id, **shared))
        db.add(ToolRegistry(workspace_id=other.id, **shared))
        db.commit()
        db.add(
            ToolRegistry(
                workspace_id=workspace.id,
                name="lookup",
                kind=ToolKind.JS,
                description="Runs in the host page",
            )
        )
        db.commit()
        db.add(ToolRegistry(workspace_id=workspace.id, **shared))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    finally:
        db.rollback()
        for tool in db.exec(
            select(ToolRegistry).where(ToolRegistry.workspace_id == other.id)
        ).all():
            db.delete(tool)
        db.delete(other)
        db.commit()


def test_github_repository_is_a_table_only(db: Session, workspace: Workspace) -> None:
    repo = GithubRepository(
        workspace_id=workspace.id,
        url="https://github.com/example/docs",
        target_branch="main",
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    assert repo.last_sync is None
