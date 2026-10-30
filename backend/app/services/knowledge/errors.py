class KnowledgeServiceError(Exception):
    """Expected knowledge failure whose message is safe to show or store."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class UnsupportedDocumentTypeError(KnowledgeServiceError):
    """The upload is not PDF, Markdown, or text."""


class EmptyDocumentError(KnowledgeServiceError):
    """The upload has no bytes."""


class DocumentTooLargeError(KnowledgeServiceError):
    """The upload is over the 10MB cap."""


class InvalidDocumentNameError(KnowledgeServiceError):
    """The upload has no usable file name."""


class DocumentNotFoundError(KnowledgeServiceError):
    """No document with this id exists in the current workspace."""


class IngestError(KnowledgeServiceError):
    """Extraction or embedding cannot produce chunks for this file."""
