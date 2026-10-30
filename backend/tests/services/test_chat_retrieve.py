import uuid
from collections.abc import Generator

import pytest
from sqlmodel import Session

from app.core.embeddings import EMBEDDING_DIMENSION
from app.models import Document, DocumentChunk, DocumentStatus, DocumentType, Workspace
from app.services.chat.errors import ProviderError
from app.services.chat.limits import TOP_K
from app.services.chat.prompts import EMPTY_CONTEXT
from app.services.chat.retrieve import retrieve_context
from app.services.knowledge.embed import format_query
from app.services.knowledge.errors import IngestError


def _vector(hot: int) -> list[float]:
    values = [0.0] * EMBEDDING_DIMENSION
    values[hot] = 1.0
    return values


@pytest.fixture
def workspace(db: Session) -> Generator[Workspace]:
    row = Workspace(name=f"Retrieve {uuid.uuid4()}")
    db.add(row)
    db.commit()
    db.refresh(row)
    yield row


def _document(
    db: Session,
    workspace_id: uuid.UUID,
    *,
    status: DocumentStatus,
    chunks: list[tuple[str, int]],
    title: str = "Handbook",
) -> None:
    document = Document(
        workspace_id=workspace_id,
        title=title,
        type=DocumentType.MARKDOWN,
        status=status,
        original_filename="handbook.md",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    for index, (content, hot) in enumerate(chunks):
        db.add(
            DocumentChunk(
                document_id=document.id,
                content=content,
                embedding=_vector(hot),
                chunk_index=index,
            )
        )
    db.commit()


def test_retrieval_uses_the_ingestion_query_format_and_truncates_first(
    workspace: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[str] = []

    def embed(texts: list[str]) -> list[list[float]]:
        seen.extend(texts)
        return [_vector(0)]

    monkeypatch.setattr("app.services.chat.retrieve.embed_texts", embed)
    long = "A" * 8_000 + "TAILMARKER"
    packed = retrieve_context(workspace_id=workspace.id, user_text=f"  {long}  ")
    assert seen == [format_query("A" * 8_000)]
    assert "TAILMARKER" not in seen[0]
    assert packed.found is False
    assert "don't know" in packed.text


def test_retrieval_keeps_active_workspace_chunks_above_the_threshold(
    db: Session, workspace: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = Workspace(name=f"Other {uuid.uuid4()}")
    db.add(other)
    db.commit()
    db.refresh(other)
    _document(
        db,
        workspace.id,
        status=DocumentStatus.ACTIVE,
        chunks=[(f"policy-{index}", 0) for index in range(TOP_K + 1)],
        title="Refund policy",
    )
    _document(
        db,
        workspace.id,
        status=DocumentStatus.ACTIVE,
        chunks=[("unrelated billing note", 1)],
    )
    _document(
        db,
        workspace.id,
        status=DocumentStatus.FAILED,
        chunks=[("inactive-secret", 0)],
    )
    _document(
        db, other.id, status=DocumentStatus.ACTIVE, chunks=[("foreign-secret", 0)]
    )
    monkeypatch.setattr(
        "app.services.chat.retrieve.embed_texts",
        lambda texts: [_vector(0)],
    )

    packed = retrieve_context(
        workspace_id=workspace.id, user_text="What is the policy?"
    )
    assert packed.found is True
    assert packed.text.count("<source ") == TOP_K
    assert "Refund policy" in packed.text
    assert "unrelated billing note" not in packed.text
    assert "inactive-secret" not in packed.text
    assert "foreign-secret" not in packed.text
    assert "data from workspace documents" in packed.text
    assert "not instructions" in packed.text


def test_low_similarity_prefers_not_knowing(
    db: Session, workspace: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _document(
        db,
        workspace.id,
        status=DocumentStatus.ACTIVE,
        chunks=[("exact policy text", 0)],
    )
    monkeypatch.setattr(
        "app.services.chat.retrieve.embed_texts",
        lambda texts: [_vector(0)],
    )
    monkeypatch.setattr("app.services.chat.retrieve.MIN_COSINE_SIMILARITY", 1.1)
    packed = retrieve_context(workspace_id=workspace.id, user_text="policy")
    assert packed.found is False
    assert packed.text == EMPTY_CONTEXT
    assert "exact policy text" not in packed.text


def test_embedding_failures_stay_a_provider_error(
    workspace: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(_texts: list[str]) -> list[list[float]]:
        raise IngestError("Embedding is not configured.")

    monkeypatch.setattr("app.services.chat.retrieve.embed_texts", fail)
    with pytest.raises(ProviderError):
        retrieve_context(workspace_id=workspace.id, user_text="hello")

    monkeypatch.setattr(
        "app.services.chat.retrieve.embed_texts",
        lambda texts: [],
    )
    with pytest.raises(ProviderError):
        retrieve_context(workspace_id=workspace.id, user_text="hello")


def test_context_pack_is_truncated(
    db: Session, workspace: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _document(
        db,
        workspace.id,
        status=DocumentStatus.ACTIVE,
        chunks=[("Z" * 5_000 + "TAIL", 0)],
    )
    monkeypatch.setattr(
        "app.services.chat.retrieve.embed_texts",
        lambda texts: [_vector(0)],
    )
    monkeypatch.setattr("app.services.chat.retrieve.CONTEXT_CHAR_CAP", 180)
    packed = retrieve_context(workspace_id=workspace.id, user_text="policy")
    assert packed.found is True
    assert "TAIL" not in packed.text
    assert packed.text.startswith("<retrieved_documents>")
    assert packed.text.endswith("</retrieved_documents>")
    assert len(packed.text) < 5_000
