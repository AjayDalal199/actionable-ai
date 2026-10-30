"""Contract for ``document_chunk.embedding``.

OpenAI ``text-embedding-3-small`` vectors are 1536 floats. The pgvector column
uses that size. Changing either value requires an Alembic migration.
"""

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
