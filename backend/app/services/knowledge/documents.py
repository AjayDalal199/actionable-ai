"""Create, list, and delete workspace documents. No extraction or embeddings."""

import uuid
from collections.abc import Sequence
from pathlib import Path

from sqlmodel import Session, col, func, select

from app.models import Document, DocumentChunk, DocumentStatus, DocumentType
from app.models.base import get_datetime_utc
from app.services.knowledge.errors import (
    DocumentNotFoundError,
    DocumentTooLargeError,
    EmptyDocumentError,
    InvalidDocumentNameError,
    UnsupportedDocumentTypeError,
)
from app.services.knowledge.limits import MAX_UPLOAD_BYTES
from app.services.knowledge.storage import delete_original, save_original

_SUFFIXES: dict[str, DocumentType] = {
    ".pdf": DocumentType.PDF,
    ".md": DocumentType.MARKDOWN,
    ".markdown": DocumentType.MARKDOWN,
    ".txt": DocumentType.TEXT,
}
_FILENAME_LIMIT = 512
_TITLE_LIMIT = 255


def upload_document(
    *,
    session: Session,
    workspace_id: uuid.UUID,
    filename: str,
    data: bytes,
) -> Document:
    stored_name = _normalize_filename(filename)
    document_type = _document_type(stored_name)
    if len(data) == 0:
        raise EmptyDocumentError("File is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise DocumentTooLargeError("File exceeds the 10MB limit.")
    stored_name = _unique_filename(
        session=session, workspace_id=workspace_id, filename=stored_name
    )
    document_id = uuid.uuid4()
    save_original(document_id=document_id, data=data)
    document = Document(
        id=document_id,
        workspace_id=workspace_id,
        title=_clip(stored_name, _TITLE_LIMIT),
        type=document_type,
        status=DocumentStatus.PROCESSING,
        original_filename=_clip(stored_name, _FILENAME_LIMIT),
    )
    session.add(document)
    try:
        session.commit()
    except Exception:
        session.rollback()
        delete_original(document_id=document_id)
        raise
    session.refresh(document)
    return document


def list_documents(
    *,
    session: Session,
    workspace_id: uuid.UUID,
    skip: int,
    limit: int,
) -> tuple[Sequence[Document], int]:
    count = session.exec(
        select(func.count())
        .select_from(Document)
        .where(Document.workspace_id == workspace_id)
    ).one()
    documents = session.exec(
        select(Document)
        .where(Document.workspace_id == workspace_id)
        .order_by(col(Document.created_at).desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return documents, count


def get_document(
    *,
    session: Session,
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
) -> Document:
    document = session.get(Document, document_id)
    if document is None or document.workspace_id != workspace_id:
        raise DocumentNotFoundError("Document not found")
    return document


def delete_document(
    *,
    session: Session,
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
) -> None:
    document = get_document(
        session=session, workspace_id=workspace_id, document_id=document_id
    )
    chunks = session.exec(
        select(DocumentChunk).where(DocumentChunk.document_id == document.id)
    ).all()
    for chunk in chunks:
        session.delete(chunk)
    session.delete(document)
    session.commit()
    delete_original(document_id=document_id)


def _normalize_filename(filename: str) -> str:
    name = Path(filename.replace("\x00", "")).name.strip()
    if not name or name in {".", ".."}:
        raise InvalidDocumentNameError("A file name is required.")
    return _clip(name, _FILENAME_LIMIT)


def _document_type(filename: str) -> DocumentType:
    kind = _SUFFIXES.get(Path(filename).suffix.lower())
    if kind is None:
        raise UnsupportedDocumentTypeError(
            "Unsupported file type. Only PDF, Markdown, and text files are supported."
        )
    return kind


def _unique_filename(
    *, session: Session, workspace_id: uuid.UUID, filename: str
) -> str:
    if not _filename_taken(session, workspace_id, filename):
        return filename
    stamp = get_datetime_utc().strftime("%Y%m%dT%H%M%S%fZ")
    suffix = Path(filename).suffix
    stem = filename[: -len(suffix)] if suffix else filename
    candidate = _clip(f"{stem}-{stamp}{suffix}", _FILENAME_LIMIT)
    counter = 1
    while _filename_taken(session, workspace_id, candidate):
        candidate = _clip(f"{stem}-{stamp}-{counter}{suffix}", _FILENAME_LIMIT)
        counter += 1
        if counter > 100:
            raise InvalidDocumentNameError("Could not store a unique file name.")
    return candidate


def _filename_taken(session: Session, workspace_id: uuid.UUID, filename: str) -> bool:
    found = session.exec(
        select(Document.id).where(
            Document.workspace_id == workspace_id,
            Document.original_filename == filename,
        )
    ).first()
    return found is not None


def _clip(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    suffix = Path(value).suffix
    if not suffix or len(suffix) >= limit:
        return value[:limit]
    return f"{value[: limit - len(suffix)]}{suffix}"
