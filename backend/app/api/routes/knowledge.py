import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from app.api.deps import (
    CurrentWorkspace,
    SessionDep,
    get_current_workspace_editor,
)
from app.jobs.knowledge import run_document_ingestion
from app.models import (
    DocumentPublic,
    DocumentsPublic,
    DocumentUploadResponse,
    Message,
)
from app.services.knowledge.documents import (
    delete_document,
    get_document,
    list_documents,
    upload_document,
)
from app.services.knowledge.errors import (
    DocumentNotFoundError,
    DocumentTooLargeError,
    EmptyDocumentError,
    InvalidDocumentNameError,
    UnsupportedDocumentTypeError,
)
from app.services.knowledge.limits import MAX_UPLOAD_BYTES

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post(
    "/upload",
    dependencies=[Depends(get_current_workspace_editor)],
)
def upload_knowledge(
    *,
    session: SessionDep,
    workspace: CurrentWorkspace,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
) -> DocumentUploadResponse:
    """Store an upload and return while ingestion runs."""
    payload = file.file.read(MAX_UPLOAD_BYTES + 1)
    try:
        document = upload_document(
            session=session,
            workspace_id=workspace.id,
            filename=file.filename or "",
            data=payload,
        )
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(status_code=415, detail=exc.message) from exc
    except DocumentTooLargeError as exc:
        raise HTTPException(status_code=413, detail=exc.message) from exc
    except (EmptyDocumentError, InvalidDocumentNameError) as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    background_tasks.add_task(run_document_ingestion, document.id)
    return DocumentUploadResponse(
        document_id=document.id,
        status=document.status,
        message="Document uploaded and chunking initiated.",
    )


@router.get("/documents")
def read_documents(
    session: SessionDep,
    workspace: CurrentWorkspace,
    skip: int = 0,
    limit: int = 100,
) -> DocumentsPublic:
    """List documents in the current workspace."""
    documents, count = list_documents(
        session=session, workspace_id=workspace.id, skip=skip, limit=limit
    )
    return DocumentsPublic(
        data=[DocumentPublic.model_validate(document) for document in documents],
        count=count,
    )


@router.get("/documents/{document_id}")
def read_document(
    session: SessionDep, workspace: CurrentWorkspace, document_id: uuid.UUID
) -> DocumentPublic:
    """Get one document in the current workspace."""
    try:
        document = get_document(
            session=session, workspace_id=workspace.id, document_id=document_id
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    return DocumentPublic.model_validate(document)


@router.delete(
    "/documents/{document_id}",
    dependencies=[Depends(get_current_workspace_editor)],
)
def remove_document(
    session: SessionDep, workspace: CurrentWorkspace, document_id: uuid.UUID
) -> Message:
    """Delete a document, its chunks, and the stored file."""
    try:
        delete_document(
            session=session, workspace_id=workspace.id, document_id=document_id
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    return Message(message="Document deleted successfully")
