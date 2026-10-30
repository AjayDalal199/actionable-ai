"""Run knowledge ingestion after the upload response.

FastAPI BackgroundTasks run in this API process (decision B5). A Redis
worker replaces this module later. The task opens its own database
session because the request session is already closed.
"""

import uuid

from sqlmodel import Session

from app.core.db import engine
from app.services.knowledge.ingest import ingest_document


def run_document_ingestion(document_id: uuid.UUID) -> None:
    with Session(engine) as session:
        ingest_document(session=session, document_id=document_id)
