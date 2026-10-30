"""Redis pause/resume for one approved-or-rejected action. The bearer is not stored."""

import json
import uuid
from typing import Any

from pydantic import BaseModel, ValidationError
from redis.exceptions import RedisError

from app.core.redis import open_redis
from app.services.chat.limits import HITL_TTL_SECONDS


class PendingAction(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    tool_id: uuid.UUID
    arguments: dict[str, Any]
    title: str
    summary: str
    function_name: str
    function_args: dict[str, Any]
    model_text: str


def _key(pending_id: uuid.UUID) -> str:
    return f"chat:hitl:{pending_id}"


async def save_pending(action: PendingAction) -> None:
    async with open_redis() as client:
        await client.set(
            _key(action.id),
            action.model_dump_json(),
            ex=HITL_TTL_SECONDS,
        )


async def peek_pending(pending_id: uuid.UUID) -> PendingAction | None:
    try:
        async with open_redis() as client:
            raw = await client.get(_key(pending_id))
    except RedisError:
        return None
    if not isinstance(raw, str):
        return None
    return _parse(raw)


async def take_pending(
    pending_id: uuid.UUID, *, workspace_id: uuid.UUID
) -> PendingAction | None:
    """Remove the action only when it belongs to ``workspace_id``."""
    key = _key(pending_id)
    try:
        async with open_redis() as client:
            raw = await client.get(key)
            peeked = _parse(raw) if isinstance(raw, str) else None
            if peeked is None or peeked.workspace_id != workspace_id:
                return None
            deleted = await client.getdel(key)
    except RedisError:
        return None
    if not isinstance(deleted, str):
        return None
    taken = _parse(deleted)
    if taken is None or taken.workspace_id != workspace_id:
        return None
    return taken


def _parse(raw: str) -> PendingAction | None:
    try:
        payload = json.loads(raw)
        return PendingAction.model_validate(payload)
    except json.JSONDecodeError, ValidationError, ValueError:
        return None
