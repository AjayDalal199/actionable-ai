"""Contract for ``document_chunk.embedding``.

Gemini ``gemini-embedding-2`` is requested at 1536 floats. That size is one
of the model's normalized outputs, and the pgvector column uses it.
Changing the dimension requires an Alembic migration.
"""

EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSION = 1536
