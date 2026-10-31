"""Extract, chunk, and embed one document. Safe to run again."""

import logging
import uuid

from sqlmodel import Session, select

from app.models import Document, DocumentChunk, DocumentStatus
from app.services.knowledge.chunk import chunk_text
from app.services.knowledge.embed import embed_texts, format_document_chunk
from app.services.knowledge.errors import IngestError
from app.services.knowledge.extract import extract_text
from app.services.knowledge.limits import ERROR_MESSAGE_MAX_CHARS
from app.services.knowledge.storage import read_original

logger = logging.getLogger(__name__)

_EMPTY_EXTRACT = "No text could be extracted from the file."
_GENERIC_FAILURE = "Could not process the file."


def ingest_document(*, session: Session, document_id: uuid.UUID) -> None:
    document = session.get(Document, document_id)
    if document is None:
        return
    try:
        _replace_chunks(session, document)
    except IngestError as exc:
        _mark_failed(session, document_id, exc.message)
    except Exception:
        logger.exception("Document %s failed ingestion", document_id)
        _mark_failed(session, document_id, _GENERIC_FAILURE)


def _replace_chunks(session: Session, document: Document) -> None:
    document_id = document.id
    try:
        data = read_original(document_id=document_id)
    except FileNotFoundError as exc:
        raise IngestError("The original file is missing.") from exc
    text = extract_text(document.type, data)
    chunks = chunk_text(text)
    if not chunks:
        raise IngestError(_EMPTY_EXTRACT)
    _delete_chunks(session, document_id)
    session.commit()
    vectors = embed_texts(
        [format_document_chunk(chunk, title=document.title) for chunk in chunks]
    )
    if len(vectors) != len(chunks):
        raise RuntimeError("Embedding count did not match the chunks.")
    current = session.get(Document, document_id)
    if current is None:
        return
    for index, content in enumerate(chunks):
        session.add(
            DocumentChunk(
                document_id=document_id,
                content=content,
                embedding=vectors[index],
                chunk_index=index,
            )
        )
    current.status = DocumentStatus.ACTIVE
    current.error_message = None
    session.add(current)
    session.commit()


def _delete_chunks(session: Session, document_id: uuid.UUID) -> None:
    chunks = session.exec(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id)
    ).all()
    for chunk in chunks:
        session.delete(chunk)


def _mark_failed(session: Session, document_id: uuid.UUID, message: str) -> None:
    session.rollback()
    document = session.get(Document, document_id)
    if document is None:
        return
    document.status = DocumentStatus.FAILED
    document.error_message = message[:ERROR_MESSAGE_MAX_CHARS] or _GENERIC_FAILURE
    session.add(document)
    session.commit()
