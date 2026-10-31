"""Truncate user text and keep HITL copy free of implementation details."""

import re

from app.services.chat.limits import USER_CHAR_CAP

_URL = re.compile(r"https?://\S+", re.IGNORECASE)
_UUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
_API_WORD = re.compile(r"\bAPIs?\b", re.IGNORECASE)
_CAPS_METHOD = re.compile(r"\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b")
_PATH = re.compile(r"(?:^|[\s(])/(?:[A-Za-z0-9._~{}%-]+/)*[A-Za-z0-9._~{}%-]*")
_PLACEHOLDER = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}")
_WORD = re.compile(r"[A-Za-z][A-Za-z']*")
_FILLER = frozenset(
    {
        "a",
        "an",
        "and",
        "at",
        "by",
        "for",
        "from",
        "into",
        "of",
        "on",
        "or",
        "the",
        "this",
        "that",
        "to",
        "tool",
        "tools",
        "using",
        "via",
        "with",
    }
)

FALLBACK_TITLE = "Confirm this action"
FALLBACK_SUMMARY = "This will change saved information. Confirm to continue."
TITLE_MAX = 80
SUMMARY_MAX = 400


def truncate_user_text(text: str) -> str:
    """Hard cap applied before embedding and before the model sees the text."""
    stripped = text.strip()
    if len(stripped) <= USER_CHAR_CAP:
        return stripped
    return stripped[:USER_CHAR_CAP]


def plain_summary(text: str | None) -> str:
    cleaned = _clean(text or "")
    if cleaned == FALLBACK_SUMMARY:
        return FALLBACK_SUMMARY
    content = [
        word for word in _WORD.findall(cleaned) if word.casefold() not in _FILLER
    ]
    if sum(len(word) for word in content) < 8:
        return FALLBACK_SUMMARY
    if len(cleaned) > SUMMARY_MAX:
        return cleaned[: SUMMARY_MAX - 3].rstrip() + "..."
    return cleaned


def plain_title(summary: str) -> str:
    if summary == FALLBACK_SUMMARY:
        return FALLBACK_TITLE
    sentence = re.split(r"(?<=[.!?])\s", summary, maxsplit=1)[0].strip()
    if len(sentence) < 8:
        return FALLBACK_TITLE
    if len(sentence) > TITLE_MAX:
        return sentence[: TITLE_MAX - 3].rstrip() + "..."
    return sentence


def _clean(text: str) -> str:
    cleaned = _URL.sub(" ", text)
    cleaned = _UUID.sub(" ", cleaned)
    cleaned = _API_WORD.sub(" ", cleaned)
    cleaned = _CAPS_METHOD.sub(" ", cleaned)
    cleaned = _PATH.sub(" ", cleaned)
    cleaned = _PLACEHOLDER.sub(" ", cleaned)
    cleaned = " ".join(cleaned.split())
    return cleaned.strip(" -:,;")
