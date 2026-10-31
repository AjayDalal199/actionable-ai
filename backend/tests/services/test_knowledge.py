import uuid
from collections.abc import Generator
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlmodel import Session, select

from app.core.config import Settings, settings
from app.core.embeddings import EMBEDDING_DIMENSION, EMBEDDING_MODEL
from app.models import DocumentChunk, DocumentStatus, DocumentType, Workspace
from app.services.knowledge.chunk import chunk_text
from app.services.knowledge.documents import upload_document
from app.services.knowledge.embed import (
    embed_texts,
    format_document_chunk,
    format_query,
)
from app.services.knowledge.errors import (
    DocumentTooLargeError,
    EmptyDocumentError,
    IngestError,
    InvalidDocumentNameError,
    UnsupportedDocumentTypeError,
)
from app.services.knowledge.extract import extract_text
from app.services.knowledge.ingest import ingest_document
from app.services.knowledge.limits import (
    APPROX_CHARS_PER_TOKEN,
    CHUNK_OVERLAP_RATIO,
    EMBEDDING_BATCH_SIZE,
    MAX_EXTRACT_CHARS,
    MAX_PDF_PAGES,
    TARGET_CHUNK_TOKENS,
)
from app.services.knowledge.storage import (
    delete_original,
    path_for,
    read_original,
    save_original,
)
from tests.utils.pdf import pdf_bytes


@pytest.fixture
def workspace(db: Session) -> Generator[Workspace]:
    row = Workspace(name=f"Knowledge {uuid.uuid4()}")
    db.add(row)
    db.commit()
    db.refresh(row)
    yield row


def _vectors(texts: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for index, _text in enumerate(texts):
        values = [0.0] * EMBEDDING_DIMENSION
        values[index % EMBEDDING_DIMENSION] = 1.0
        vectors.append(values)
    return vectors


def test_chunk_defaults_stay_in_the_decided_range() -> None:
    assert 500 <= TARGET_CHUNK_TOKENS <= 800
    assert 0.10 <= CHUNK_OVERLAP_RATIO <= 0.20
    assert APPROX_CHARS_PER_TOKEN == 4


def test_chunk_text_overlaps_long_input() -> None:
    size = TARGET_CHUNK_TOKENS * APPROX_CHARS_PER_TOKEN
    overlap = int(size * CHUNK_OVERLAP_RATIO)
    text = "".join(str(index % 10) for index in range(size * 3))
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert len(chunks[0]) == size
    assert chunks[1][:overlap] == chunks[0][-overlap:]
    assert 500 <= len(chunks[0]) / APPROX_CHARS_PER_TOKEN <= 800
    assert 0.10 <= overlap / len(chunks[0]) <= 0.20


def test_chunk_text_prefers_a_paragraph_break() -> None:
    size = TARGET_CHUNK_TOKENS * APPROX_CHARS_PER_TOKEN
    head = "a" * int(size * 0.7)
    tail = "b" * size
    chunks = chunk_text(f"{head}\n\n{tail}")
    assert "b" not in chunks[0]
    assert len(chunks[0]) < size
    assert "b" in chunks[1]


def test_chunk_text_skips_empty_input() -> None:
    assert chunk_text("") == []
    assert chunk_text("  \n\t") == []
    assert chunk_text("Refunds are allowed.") == ["Refunds are allowed."]


def test_chunk_text_rejects_overlap_outside_the_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.knowledge.chunk.CHUNK_OVERLAP_RATIO", 0.5)
    with pytest.raises(ValueError, match="10% and 20%"):
        chunk_text("hello")


def test_extract_uses_markdown_and_text_as_is() -> None:
    assert extract_text(DocumentType.MARKDOWN, b"# Title\n\nBody") == "# Title\n\nBody"
    assert extract_text(DocumentType.TEXT, b"plain words") == "plain words"
    assert extract_text(DocumentType.TEXT, "\ufeffplain".encode()) == "plain"


def test_extract_pdf_text_and_empty_page() -> None:
    assert (
        "handbook"
        in extract_text(DocumentType.PDF, pdf_bytes("Hello from the handbook")).lower()
    )
    assert extract_text(DocumentType.PDF, pdf_bytes("")).strip() == ""


def test_extract_pdf_read_failure_and_page_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(IngestError, match="Could not read the PDF"):
        extract_text(DocumentType.PDF, b"%PDF-1.4\nthis is not a pdf")
    monkeypatch.setattr("app.services.knowledge.extract.MAX_PDF_PAGES", 1)
    assert MAX_PDF_PAGES >= 1
    capped = extract_text(DocumentType.PDF, pdf_bytes("", "Only on page two"))
    assert "page two" not in capped.lower()


def test_extract_caps_characters(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.knowledge.extract.MAX_EXTRACT_CHARS", 11)
    assert extract_text(DocumentType.MARKDOWN, b"hello world extra") == "hello world"
    assert MAX_EXTRACT_CHARS > 11


def test_extract_rejects_invalid_utf8() -> None:
    with pytest.raises(IngestError, match="UTF-8"):
        extract_text(DocumentType.TEXT, b"\xff")


def test_storage_is_keyed_by_document_id(knowledge_storage: Path) -> None:
    document_id = uuid.uuid4()
    upload_name = "notes.md"
    save_original(document_id=document_id, data=b"hello")
    path = path_for(document_id)
    assert path == knowledge_storage / str(document_id)
    assert path.name != upload_name
    assert read_original(document_id=document_id) == b"hello"
    delete_original(document_id=document_id)
    assert not path.exists()


def test_upload_document_does_not_embed(
    db: Session, workspace: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(texts: list[str]) -> list[list[float]]:
        raise AssertionError(texts)

    monkeypatch.setattr("app.services.knowledge.ingest.embed_texts", explode)
    document = upload_document(
        session=db,
        workspace_id=workspace.id,
        filename="notes.md",
        data=b"# Hello",
    )
    assert document.status == DocumentStatus.PROCESSING
    assert document.type == DocumentType.MARKDOWN
    assert read_original(document_id=document.id) == b"# Hello"


def test_upload_document_accepts_text_and_markdown_suffixes(
    db: Session, workspace: Workspace
) -> None:
    text = upload_document(
        session=db,
        workspace_id=workspace.id,
        filename="notes.TXT",
        data=b"hello",
    )
    markdown = upload_document(
        session=db,
        workspace_id=workspace.id,
        filename="guide.markdown",
        data=b"# guide",
    )
    assert text.type == DocumentType.TEXT
    assert markdown.type == DocumentType.MARKDOWN


def test_upload_document_strips_directory_prefixes(
    db: Session, workspace: Workspace, knowledge_storage: Path
) -> None:
    document = upload_document(
        session=db,
        workspace_id=workspace.id,
        filename="../../notes.md",
        data=b"hello",
    )
    assert document.original_filename == "notes.md"
    assert path_for(document.id).is_relative_to(knowledge_storage)
    with pytest.raises(InvalidDocumentNameError):
        upload_document(
            session=db,
            workspace_id=workspace.id,
            filename="",
            data=b"hello",
        )


def test_missing_file_fails_ingestion(db: Session, workspace: Workspace) -> None:
    document = upload_document(
        session=db,
        workspace_id=workspace.id,
        filename="notes.md",
        data=b"hello",
    )
    delete_original(document_id=document.id)
    ingest_document(session=db, document_id=document.id)
    db.refresh(document)
    assert document.status == DocumentStatus.FAILED
    assert document.error_message == "The original file is missing."
    ingest_document(session=db, document_id=uuid.uuid4())


def test_upload_document_rejects_type_empty_and_size(
    db: Session, workspace: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(UnsupportedDocumentTypeError):
        upload_document(
            session=db,
            workspace_id=workspace.id,
            filename="notes.docx",
            data=b"nope",
        )
    with pytest.raises(EmptyDocumentError):
        upload_document(
            session=db,
            workspace_id=workspace.id,
            filename="empty.md",
            data=b"",
        )
    monkeypatch.setattr("app.services.knowledge.documents.MAX_UPLOAD_BYTES", 4)
    with pytest.raises(DocumentTooLargeError):
        upload_document(
            session=db,
            workspace_id=workspace.id,
            filename="big.md",
            data=b"12345",
        )


def test_reingest_deletes_old_chunks_before_embedding(
    db: Session, workspace: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = upload_document(
        session=db,
        workspace_id=workspace.id,
        filename="handbook.md",
        data=b"First version is long enough. " + b"word " * 800,
    )
    seen: list[int] = []

    def fake_embed(texts: list[str]) -> list[list[float]]:
        remaining = db.exec(
            select(DocumentChunk).where(DocumentChunk.document_id == document.id)
        ).all()
        seen.append(len(remaining))
        return _vectors(texts)

    monkeypatch.setattr("app.services.knowledge.ingest.embed_texts", fake_embed)
    ingest_document(session=db, document_id=document.id)
    db.refresh(document)
    assert document.status == DocumentStatus.ACTIVE
    first_count = len(
        db.exec(
            select(DocumentChunk).where(DocumentChunk.document_id == document.id)
        ).all()
    )
    assert first_count > 1

    save_original(document_id=document.id, data=b"Second version.")
    ingest_document(session=db, document_id=document.id)
    db.refresh(document)
    chunks = db.exec(
        select(DocumentChunk).where(DocumentChunk.document_id == document.id)
    ).all()
    assert seen == [0, 0]
    assert document.status == DocumentStatus.ACTIVE
    assert [chunk.content for chunk in chunks] == ["Second version."]


def test_failed_embed_marks_the_document_failed_and_drops_chunks(
    db: Session, workspace: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = upload_document(
        session=db,
        workspace_id=workspace.id,
        filename="handbook.md",
        data=b"Refunds are allowed.",
    )

    def fake_embed(texts: list[str]) -> list[list[float]]:
        return _vectors(texts)

    monkeypatch.setattr("app.services.knowledge.ingest.embed_texts", fake_embed)
    ingest_document(session=db, document_id=document.id)

    def explode(texts: list[str]) -> list[list[float]]:
        raise RuntimeError(texts)

    monkeypatch.setattr("app.services.knowledge.ingest.embed_texts", explode)
    ingest_document(session=db, document_id=document.id)
    db.refresh(document)
    chunks = db.exec(
        select(DocumentChunk).where(DocumentChunk.document_id == document.id)
    ).all()
    assert document.status == DocumentStatus.FAILED
    assert document.error_message == "Could not process the file."
    assert chunks == []


def test_missing_embedding_key_fails_the_document(
    db: Session, workspace: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = upload_document(
        session=db,
        workspace_id=workspace.id,
        filename="notes.md",
        data=b"hello",
    )
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    ingest_document(session=db, document_id=document.id)
    db.refresh(document)
    assert document.status == DocumentStatus.FAILED
    assert document.error_message == "Embedding is not configured."


def test_gemini_prefixes_documents_and_queries() -> None:
    assert (
        format_document_chunk("Refunds are allowed.", title="Handbook")
        == "title: Handbook | text: Refunds are allowed."
    )
    assert (
        format_document_chunk("Refunds", title="  \n") == "title: none | text: Refunds"
    )
    assert (
        format_query("Can I get a refund?")
        == "task: question answering | query: Can I get a refund?"
    )


def test_embed_texts_orders_batches_and_checks_width(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    class _Models:
        def embed_content(
            self, *, model: str, contents: list[object], config: SimpleNamespace
        ) -> SimpleNamespace:
            assert model == EMBEDDING_MODEL
            assert config.output_dimensionality == EMBEDDING_DIMENSION
            texts = [content.parts[0].text for content in contents]  # type: ignore[attr-defined]
            calls.append(texts)
            embeddings = []
            for index, _text in enumerate(texts):
                vector = [0.0] * EMBEDDING_DIMENSION
                vector[0] = float(index + 1)
                embeddings.append(SimpleNamespace(values=vector))
            return SimpleNamespace(embeddings=embeddings)

    class _Client:
        def __init__(self, *, api_key: str, http_options: object = None) -> None:
            assert api_key == "test-key"
            assert http_options is not None
            self.models = _Models()

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.gemini.genai.Client", _Client)
    monkeypatch.setattr("app.services.knowledge.embed.EMBEDDING_BATCH_SIZE", 2)
    assert EMBEDDING_BATCH_SIZE == 64
    vectors = embed_texts(["one", "two", "three"])
    assert calls == [["one", "two"], ["three"]]
    assert [vector[0] for vector in vectors] == [1.0, 2.0, 1.0]


def test_embed_texts_rejects_the_wrong_dimension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Models:
        def embed_content(
            self, *, model: str, contents: list[object], config: SimpleNamespace
        ) -> SimpleNamespace:
            assert model == EMBEDDING_MODEL
            assert config.output_dimensionality == EMBEDDING_DIMENSION
            assert contents
            return SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0, 0.0])])

    class _Client:
        def __init__(self, *, api_key: str, http_options: object = None) -> None:
            self.models = _Models()

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.gemini.genai.Client", _Client)
    with pytest.raises(RuntimeError, match="1536"):
        embed_texts(["hello"])


def test_blank_gemini_key_and_chat_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "  ")
    loaded = Settings()  # type: ignore[call-arg]
    assert loaded.GEMINI_API_KEY is None
    assert loaded.CHAT_MODEL == "gemini-3.5-flash-lite"
    assert loaded.EMBEDDING_MODEL == EMBEDDING_MODEL

    monkeypatch.setenv("CHAT_MODEL", "  ")
    with pytest.raises(ValueError, match="CHAT_MODEL"):
        Settings()  # type: ignore[call-arg]

    monkeypatch.setenv("CHAT_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setenv("KNOWLEDGE_STORAGE_DIR", "  ")
    with pytest.raises(ValueError, match="KNOWLEDGE_STORAGE_DIR"):
        Settings()  # type: ignore[call-arg]
