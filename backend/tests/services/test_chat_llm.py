import asyncio
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services.chat.errors import PROVIDER_MESSAGE, ProviderError
from app.services.chat.llm import TextDelta, ToolRequest, stream_model


def test_stream_model_yields_text_and_disables_automatic_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    class Models:
        async def generate_content_stream(
            self, *, model: str, contents: list, config: object
        ):
            seen["model"] = model
            seen["config"] = config

            async def chunks():
                yield SimpleNamespace(text="Hello ", function_calls=None)
                yield SimpleNamespace(
                    text=None,
                    function_calls=[
                        SimpleNamespace(
                            id="call-1",
                            name="lookup_order",
                            args={"id": "ada"},
                            will_continue=False,
                        )
                    ],
                )

            return chunks()

    class Client:
        def __init__(self) -> None:
            models = Models()
            self.aio = SimpleNamespace(models=models)

    monkeypatch.setattr("app.services.chat.llm._client", lambda: Client())

    async def collect() -> list[TextDelta | ToolRequest]:
        events = []
        async for event in stream_model(
            system_prompt="Be brief.",
            contents=[],
            tools=None,
        ):
            events.append(event)
        return events

    events = asyncio.run(collect())
    assert events == [
        TextDelta(text="Hello "),
        ToolRequest(name="lookup_order", args={"id": "ada"}),
    ]
    assert seen["model"] == settings.CHAT_MODEL
    config = seen["config"]
    assert getattr(config, "system_instruction", None) == "Be brief."
    automatic = getattr(config, "automatic_function_calling", None)
    assert automatic is not None
    assert automatic.disable is True
    assert getattr(config, "tools", None) is None


def test_provider_errors_hide_the_exception_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Models:
        async def generate_content_stream(
            self, *, model: str, contents: list, config: object
        ):
            raise RuntimeError("secret-key-boom")

    monkeypatch.setattr(
        "app.services.chat.llm._client",
        lambda: SimpleNamespace(aio=SimpleNamespace(models=Models())),
    )

    async def collect() -> None:
        async for _event in stream_model(system_prompt="x", contents=[], tools=None):
            pass

    with pytest.raises(ProviderError) as caught:
        asyncio.run(collect())
    assert str(caught.value) == PROVIDER_MESSAGE
    assert "secret-key-boom" not in str(caught.value)


def test_missing_gemini_key_is_a_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)

    async def collect() -> None:
        async for _event in stream_model(system_prompt="x", contents=[], tools=None):
            pass

    with pytest.raises(ProviderError, match="unavailable"):
        asyncio.run(collect())
