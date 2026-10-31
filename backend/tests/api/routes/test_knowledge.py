import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, select

from app.core.config import settings
from app.core.embeddings import EMBEDDING_DIMENSION
from app.models import Document, DocumentChunk, DocumentStatus, WorkspaceRole
from app.services.knowledge.storage import path_for
from tests.utils.pdf import pdf_bytes
from tests.utils.workspace import auth_headers_for_role, create_workspace


def _vectors(texts: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for index, _text in enumerate(texts):
        values = [0.0] * EMBEDDING_DIMENSION
        values[index % EMBEDDING_DIMENSION] = 1.0
        vectors.append(values)
    return vectors


def _long_markdown() -> bytes:
    return b"Refunds are allowed when the order is unopened.\n\n" + b"policy " * 900


def _upload(
    client: TestClient,
    headers: dict[str, str],
    filename: str,
    content: bytes,
    content_type: str,
    form: dict[str, str] | None = None,
):
    return client.post(
        f"{settings.API_V1_STR}/knowledge/upload",
        headers=headers,
        files={"file": (filename, content, content_type)},
        data=form,
    )


def test_upload_happy_path_returns_processing_then_active_chunks(
    client: TestClient,
    db: Session,
    knowledge_storage: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.services.knowledge.ingest.embed_texts", _vectors)
    headers, _email, workspace_id = create_workspace(client, db, name="Acme")
    response = _upload(
        client, headers, "handbook.md", _long_markdown(), "text/markdown"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processing"
    assert body["message"] == "Document uploaded and chunking initiated."
    document_id = uuid.UUID(body["document_id"])

    detail = client.get(
        f"{settings.API_V1_STR}/knowledge/documents/{document_id}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["status"] == "active"
    assert detail.json()["error_message"] is None
    assert detail.json()["original_filename"] == "handbook.md"
    assert detail.json()["type"] == "markdown"

    db.expire_all()
    document = db.get(Document, document_id)
    assert document is not None
    assert document.workspace_id == uuid.UUID(workspace_id)
    assert document.status == DocumentStatus.ACTIVE
    chunks = db.exec(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    ).all()
    assert len(chunks) > 1
    assert path_for(document_id) == knowledge_storage / str(document_id)
    assert path_for(document_id).read_bytes() == _long_markdown()

    nearest_id = db.execute(
        text(
            "SELECT document_chunk.id FROM document_chunk "
            "JOIN document ON document.id = document_chunk.document_id "
            "WHERE document.workspace_id = :workspace_id "
            "ORDER BY document_chunk.embedding <=> CAST(:query AS vector) "
            "LIMIT 1"
        ),
        {
            "workspace_id": document.workspace_id,
            "query": str(list(chunks[0].embedding)),
        },
    ).scalar_one()
    assert nearest_id == chunks[0].id

    listed = client.get(f"{settings.API_V1_STR}/knowledge/documents", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["count"] == 1
    assert listed.json()["data"][0]["id"] == str(document_id)
    assert listed.json()["data"][0]["status"] == "active"


def test_upload_text_file_becomes_active(
    client: TestClient, db: Session, monkeypatch
) -> None:
    monkeypatch.setattr("app.services.knowledge.ingest.embed_texts", _vectors)
    headers, _email, _workspace_id = create_workspace(client, db)
    response = _upload(client, headers, "notes.txt", b"Plain note.", "text/plain")
    assert response.status_code == 200
    document_id = response.json()["document_id"]
    detail = client.get(
        f"{settings.API_V1_STR}/knowledge/documents/{document_id}",
        headers=headers,
    )
    assert detail.json()["status"] == "active"
    assert detail.json()["type"] == "text"


def test_documents_are_isolated_across_workspaces(
    client: TestClient, db: Session, monkeypatch
) -> None:
    monkeypatch.setattr("app.services.knowledge.ingest.embed_texts", _vectors)
    headers_a, _email_a, workspace_a = create_workspace(client, db, name="A")
    headers_b, _email_b, workspace_b = create_workspace(client, db, name="B")
    created = _upload(
        client,
        headers_a,
        "secret.md",
        b"Workspace A only.",
        "text/markdown",
        form={"workspace_id": workspace_b},
    )
    assert created.status_code == 200
    document_id = created.json()["document_id"]

    db.expire_all()
    document = db.get(Document, uuid.UUID(document_id))
    assert document is not None
    assert str(document.workspace_id) == workspace_a

    listed = client.get(f"{settings.API_V1_STR}/knowledge/documents", headers=headers_b)
    assert listed.status_code == 200
    assert listed.json()["data"] == []
    assert listed.json()["count"] == 0

    hidden = client.get(
        f"{settings.API_V1_STR}/knowledge/documents/{document_id}",
        headers=headers_b,
    )
    assert hidden.status_code == 404
    assert hidden.json()["detail"] == "Document not found"

    denied = client.delete(
        f"{settings.API_V1_STR}/knowledge/documents/{document_id}",
        headers=headers_b,
    )
    assert denied.status_code == 404
    assert path_for(uuid.UUID(document_id)).is_file()
    assert (
        client.get(
            f"{settings.API_V1_STR}/knowledge/documents/{document_id}",
            headers=headers_a,
        ).status_code
        == 200
    )


def test_upload_rejects_unsupported_type(
    client: TestClient, db: Session, knowledge_storage: Path
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    response = _upload(
        client,
        headers,
        "notes.docx",
        b"not a pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert response.status_code == 415
    assert "PDF, Markdown, and text" in response.json()["detail"]
    listed = client.get(f"{settings.API_V1_STR}/knowledge/documents", headers=headers)
    assert listed.json()["count"] == 0
    assert list(knowledge_storage.iterdir()) == []


def test_upload_failed_parse_ends_as_failed(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    response = _upload(
        client,
        headers,
        "broken.pdf",
        b"%PDF-1.4\nthis is not a pdf",
        "application/pdf",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "processing"
    document_id = response.json()["document_id"]

    detail = client.get(
        f"{settings.API_V1_STR}/knowledge/documents/{document_id}",
        headers=headers,
    )
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "failed"
    assert body["error_message"] == "Could not read the PDF."

    db.expire_all()
    chunks = db.exec(
        select(DocumentChunk).where(DocumentChunk.document_id == uuid.UUID(document_id))
    ).all()
    assert chunks == []
    assert path_for(uuid.UUID(document_id)).is_file()

    listed = client.get(f"{settings.API_V1_STR}/knowledge/documents", headers=headers)
    row = listed.json()["data"][0]
    assert row["status"] == "failed"
    assert row["error_message"] == "Could not read the PDF."


def test_upload_empty_extract_ends_as_failed(client: TestClient, db: Session) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    response = _upload(client, headers, "blank.pdf", pdf_bytes(""), "application/pdf")
    assert response.status_code == 200
    document_id = response.json()["document_id"]
    detail = client.get(
        f"{settings.API_V1_STR}/knowledge/documents/{document_id}",
        headers=headers,
    )
    assert detail.json()["status"] == "failed"
    assert detail.json()["error_message"] == "No text could be extracted from the file."


def test_duplicate_filename_gets_a_timestamp(
    client: TestClient, db: Session, monkeypatch
) -> None:
    monkeypatch.setattr("app.services.knowledge.ingest.embed_texts", _vectors)
    headers, _email, _workspace_id = create_workspace(client, db, name="Acme")
    other_headers, _other_email, _other_workspace = create_workspace(
        client, db, name="Other"
    )
    first = _upload(client, headers, "notes.md", b"one", "text/markdown")
    second = _upload(client, headers, "notes.md", b"two", "text/markdown")
    elsewhere = _upload(client, other_headers, "notes.md", b"three", "text/markdown")
    assert first.status_code == 200
    assert second.status_code == 200
    assert elsewhere.status_code == 200

    def filename(document_id: str) -> str:
        detail = client.get(
            f"{settings.API_V1_STR}/knowledge/documents/{document_id}",
            headers=headers
            if document_id != elsewhere.json()["document_id"]
            else other_headers,
        )
        assert detail.status_code == 200
        return detail.json()["original_filename"]

    assert filename(first.json()["document_id"]) == "notes.md"
    renamed = filename(second.json()["document_id"])
    assert renamed.startswith("notes-")
    assert renamed.endswith(".md")
    assert "T" in renamed
    assert filename(elsewhere.json()["document_id"]) == "notes.md"


def test_viewer_can_list_but_cannot_upload_or_delete(
    client: TestClient, db: Session, monkeypatch
) -> None:
    monkeypatch.setattr("app.services.knowledge.ingest.embed_texts", _vectors)
    admin_headers, _email, workspace_id = create_workspace(client, db)
    viewer_headers, _viewer = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.VIEWER
    )
    editor_headers, _editor = auth_headers_for_role(
        client, db, workspace_id, WorkspaceRole.EDITOR
    )
    created = _upload(client, editor_headers, "faq.md", b"Answers.", "text/markdown")
    assert created.status_code == 200
    document_id = created.json()["document_id"]

    forbidden = _upload(client, viewer_headers, "nope.md", b"nope", "text/markdown")
    assert forbidden.status_code == 403
    assert (
        forbidden.json()["detail"] == "Only workspace editors can perform this action"
    )

    listed = client.get(
        f"{settings.API_V1_STR}/knowledge/documents", headers=viewer_headers
    )
    assert listed.status_code == 200
    assert listed.json()["count"] == 1

    denied_delete = client.delete(
        f"{settings.API_V1_STR}/knowledge/documents/{document_id}",
        headers=viewer_headers,
    )
    assert denied_delete.status_code == 403

    removed = client.delete(
        f"{settings.API_V1_STR}/knowledge/documents/{document_id}",
        headers=editor_headers,
    )
    assert removed.status_code == 200
    assert (
        client.get(
            f"{settings.API_V1_STR}/knowledge/documents/{document_id}",
            headers=admin_headers,
        ).status_code
        == 404
    )
    assert not path_for(uuid.UUID(document_id)).exists()
    db.expire_all()
    assert (
        db.exec(
            select(DocumentChunk).where(
                DocumentChunk.document_id == uuid.UUID(document_id)
            )
        ).all()
        == []
    )


def test_upload_rejects_empty_and_oversized_files(
    client: TestClient, db: Session, monkeypatch
) -> None:
    headers, _email, _workspace_id = create_workspace(client, db)
    empty = _upload(client, headers, "empty.md", b"", "text/markdown")
    assert empty.status_code == 400
    assert empty.json()["detail"] == "File is empty."

    monkeypatch.setattr("app.services.knowledge.documents.MAX_UPLOAD_BYTES", 4)
    oversized = _upload(client, headers, "big.md", b"12345", "text/markdown")
    assert oversized.status_code == 413
    assert oversized.json()["detail"] == "File exceeds the 10MB limit."


def test_upload_requires_a_workspace(client: TestClient, db: Session) -> None:
    from tests.utils.workspace import auth_headers_for_new_user

    headers, _email = auth_headers_for_new_user(client, db)
    response = _upload(client, headers, "notes.md", b"hello", "text/markdown")
    assert response.status_code == 403
    assert response.json()["detail"] == "User is not a member of a workspace"
