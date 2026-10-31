"""Call Gemini embeddings. The upload request must not import this.

``gemini-embedding-2`` collapses a list of plain strings into one vector.
Each chunk is sent as its own content object so the response has one
1536-float vector per chunk. The model normalizes that size itself.
"""

from google.genai import types

from app.core.config import settings
from app.core.embeddings import EMBEDDING_DIMENSION, EMBEDDING_MODEL
from app.services.gemini import gemini_client
from app.services.knowledge.errors import IngestError
from app.services.knowledge.limits import EMBEDDING_BATCH_SIZE


def format_document_chunk(text: str, *, title: str | None) -> str:
    """Document side of an asymmetric Gemini embedding."""
    label = " ".join((title or "").split()) or "none"
    return f"title: {label} | text: {text}"


def format_query(text: str) -> str:
    """Query side. Use this when retrieval is built, not for stored chunks."""
    return f"task: question answering | query: {text}"


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if not settings.GEMINI_API_KEY:
        raise IngestError("Embedding is not configured.")
    client = gemini_client()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[start : start + EMBEDDING_BATCH_SIZE]
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=[
                types.Content(parts=[types.Part.from_text(text=text)]) for text in batch
            ],
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSION),
        )
        embeddings = list(response.embeddings or [])
        if len(embeddings) != len(batch):
            raise RuntimeError("Embedding response did not match the input batch.")
        for item in embeddings:
            values = list(item.values or [])
            if len(values) != EMBEDDING_DIMENSION:
                raise RuntimeError(
                    f"Expected {EMBEDDING_DIMENSION} dimensions, got {len(values)}."
                )
            vectors.append(values)
    return vectors
