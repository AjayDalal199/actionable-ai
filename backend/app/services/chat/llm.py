"""Stream one Gemini reply. Automatic function calling stays off.

The orchestrator decides which calls run. This module only reads the model's
text and function calls.
"""

import json
import logging
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types

from app.core.config import settings
from app.services.chat.errors import PROVIDER_MESSAGE, ProviderError
from app.services.gemini import gemini_client

logger = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class TextDelta:
    text: str


@dataclass(frozen=True, kw_only=True)
class ToolRequest:
    name: str
    args: dict[str, Any]


def build_contents(transcript: list[dict[str, Any]]) -> list[types.Content]:
    contents: list[types.Content] = []
    for turn in transcript:
        content = _content(turn)
        if content is None:
            continue
        if contents and contents[-1].role == content.role:
            parts = list(contents[-1].parts or [])
            parts.extend(content.parts or [])
            contents[-1] = types.Content(role=content.role, parts=parts)
        else:
            contents.append(content)
    return contents


async def stream_model(
    *,
    system_prompt: str,
    contents: list[types.Content],
    tools: list[types.FunctionDeclaration] | None,
) -> AsyncIterator[TextDelta | ToolRequest]:
    client = _client()
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        tools=[types.Tool(function_declarations=tools)] if tools else None,
    )
    found: dict[str, ToolRequest] = {}
    try:
        stream = await client.aio.models.generate_content_stream(
            model=settings.CHAT_MODEL,
            contents=contents,
            config=config,
        )
        async for chunk in stream:
            text = chunk.text
            if text:
                yield TextDelta(text=text)
            for call in chunk.function_calls or []:
                if not call.name or call.will_continue:
                    continue
                found[call.id or call.name] = ToolRequest(
                    name=call.name,
                    args=_plain_args(call.args),
                )
    except ProviderError:
        raise
    except Exception as exc:
        logger.exception("Chat provider request failed")
        raise ProviderError(PROVIDER_MESSAGE) from exc
    for request in found.values():
        yield request


def _client() -> genai.Client:
    if not settings.GEMINI_API_KEY:
        raise ProviderError(PROVIDER_MESSAGE)
    return gemini_client()


def _content(turn: dict[str, Any]) -> types.Content | None:
    role = turn.get("role")
    if role == "tool":
        response = turn.get("response")
        name = turn.get("name")
        if not isinstance(name, str) or not isinstance(response, dict):
            return None
        return types.Content(
            role="user",
            parts=[types.Part.from_function_response(name=name, response=response)],
        )
    parts: list[types.Part] = []
    text = turn.get("text")
    if isinstance(text, str) and text:
        parts.append(types.Part.from_text(text=text))
    call = turn.get("call")
    if isinstance(call, dict) and isinstance(call.get("name"), str):
        args = call.get("args")
        parts.append(
            types.Part.from_function_call(
                name=call["name"],
                args=args if isinstance(args, dict) else {},
            )
        )
    if not parts:
        return None
    gemini_role = "model" if role == "model" else "user"
    return types.Content(role=gemini_role, parts=parts)


def _plain_args(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    try:
        dumped = json.loads(json.dumps(dict(value), default=str))
    except TypeError, ValueError:
        return {}
    if not isinstance(dumped, dict):
        return {}
    return {str(key): item for key, item in dumped.items()}
