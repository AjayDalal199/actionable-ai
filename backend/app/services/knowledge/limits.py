"""Caps for one upload. These keep a single file from filling the worker."""

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 100
MAX_EXTRACT_CHARS = 200_000
# About 500–800 tokens, approximated at 4 characters per token.
TARGET_CHUNK_TOKENS = 650
# About 10–20% of the chunk.
CHUNK_OVERLAP_RATIO = 0.15
APPROX_CHARS_PER_TOKEN = 4
EMBEDDING_BATCH_SIZE = 64
ERROR_MESSAGE_MAX_CHARS = 2_000
