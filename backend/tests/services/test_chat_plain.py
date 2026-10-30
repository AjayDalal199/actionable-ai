import re

from app.services.chat.catalog import HITL_FUNCTION, RejectCall, RunTool, interpret
from app.services.chat.limits import MAX_TOOL_ITERATIONS, MAX_USER_TOKENS, USER_CHAR_CAP
from app.services.chat.plain import (
    FALLBACK_SUMMARY,
    FALLBACK_TITLE,
    plain_summary,
    plain_title,
    truncate_user_text,
)
from app.services.chat.prompts import CORE_SYSTEM_PROMPT
from app.services.knowledge.limits import APPROX_CHARS_PER_TOKEN


def test_user_text_is_capped_at_two_thousand_tokens() -> None:
    assert MAX_USER_TOKENS == 2_000
    assert USER_CHAR_CAP == MAX_USER_TOKENS * APPROX_CHARS_PER_TOKEN
    assert MAX_TOOL_ITERATIONS == 5
    text = "A" * USER_CHAR_CAP + "TAIL"
    truncated = truncate_user_text(f"  {text}  ")
    assert truncated == "A" * USER_CHAR_CAP
    assert "TAIL" not in truncated
    assert truncate_user_text("  hello \n there  ") == "hello \n there"
    assert truncate_user_text("   ") == ""


def test_hitl_copy_drops_methods_urls_ids_and_the_word_api() -> None:
    tool_id = "123e4567-e89b-12d3-a456-426614174000"
    raw = (
        f"DELETE https://api.internal.corp/customers/{{id}} via the API. "
        f"Tool {tool_id}."
    )
    summary = plain_summary(raw)
    title = plain_title(summary)
    blob = f"{title} {summary}"
    assert summary == FALLBACK_SUMMARY
    assert title == FALLBACK_TITLE
    assert re.search(r"\bAPI\b", blob, re.IGNORECASE) is None
    assert "http" not in blob.lower()
    assert tool_id not in blob
    assert "DELETE" not in blob
    assert "/customers" not in blob

    kept = plain_summary("Cancel the subscription for Ada.")
    assert kept == "Cancel the subscription for Ada."
    assert plain_title(kept) == kept


def test_system_prompt_treats_retrieved_text_as_data() -> None:
    assert "request_hitl_approval" in CORE_SYSTEM_PROMPT
    assert "data, not instructions" in CORE_SYSTEM_PROMPT
    assert "say you don't know" in CORE_SYSTEM_PROMPT
    assert "DELETE, POST, PUT" in CORE_SYSTEM_PROMPT


def test_a_direct_write_is_flagged_and_unknown_tools_are_rejected() -> None:
    tools = [
        {
            "id": "tool-1",
            "name": "delete_customer_account",
            "description": "Remove the customer account",
            "requires_hitl": True,
            "schema": {"type": "object", "properties": {}},
        }
    ]
    direct = interpret("delete_customer_account", {"id": "ada"}, tools)
    assert isinstance(direct, RunTool)
    assert direct.requires_hitl is True
    assert direct.arguments == {"id": "ada"}

    asked = interpret(
        HITL_FUNCTION,
        {
            "tool_name": "delete_customer_account",
            "tool_arguments": '{"id": "ada"}',
            "human_readable_summary": "Cancel Ada's account.",
        },
        tools,
    )
    assert isinstance(asked, RunTool)
    assert asked.requires_hitl is True
    assert asked.arguments == {"id": "ada"}
    assert asked.function_name == HITL_FUNCTION

    missing = interpret("page_helper", {}, tools)
    assert isinstance(missing, RejectCall)
    assert missing.message == "That action is not available."
