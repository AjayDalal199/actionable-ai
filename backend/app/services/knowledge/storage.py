"""Original upload bytes on the boot-volume disk.

Files are named by document id under ``KNOWLEDGE_STORAGE_DIR``. Compose
mounts a Docker named volume at that path. This module is the only place
that knows the directory.
"""

import uuid
from pathlib import Path

from app.core.config import settings


def save_original(*, document_id: uuid.UUID, data: bytes) -> None:
    path = path_for(document_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{document_id}.part")
    temporary.write_bytes(data)
    temporary.replace(path)


def read_original(*, document_id: uuid.UUID) -> bytes:
    return path_for(document_id).read_bytes()


def delete_original(*, document_id: uuid.UUID) -> None:
    path_for(document_id).unlink(missing_ok=True)


def path_for(document_id: uuid.UUID) -> Path:
    return Path(settings.KNOWLEDGE_STORAGE_DIR) / str(document_id)
