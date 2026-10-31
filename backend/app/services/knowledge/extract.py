"""Turn an uploaded file into plain text.

Markdown and text are decoded as UTF-8. PDFs go through pypdf. Callers
treat an empty result as a failed document.
"""

import logging
from io import BytesIO

from pypdf import PdfReader

from app.models import DocumentType
from app.services.knowledge.errors import IngestError
from app.services.knowledge.limits import MAX_EXTRACT_CHARS, MAX_PDF_PAGES

logger = logging.getLogger(__name__)


def extract_text(document_type: DocumentType, data: bytes) -> str:
    if document_type == DocumentType.PDF:
        text = _extract_pdf(data)
    elif document_type in (DocumentType.MARKDOWN, DocumentType.TEXT):
        text = _decode_text(data)
    else:
        raise IngestError(
            "Unsupported file type. Only PDF, Markdown, and text files are supported."
        )
    if text.startswith("\ufeff"):
        text = text[1:]
    if len(text) > MAX_EXTRACT_CHARS:
        logger.info("Capping extracted text at %s characters", MAX_EXTRACT_CHARS)
        text = text[:MAX_EXTRACT_CHARS]
    return text


def _decode_text(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IngestError("File is not valid UTF-8 text.") from exc


def _extract_pdf(data: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(data))
        pages = reader.pages[:MAX_PDF_PAGES]
        parts = [(page.extract_text() or "") for page in pages]
    except Exception as exc:
        raise IngestError("Could not read the PDF.") from exc
    return "\n\n".join(parts)
