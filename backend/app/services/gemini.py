"""Shared Gemini client.

``gemini-3.5-flash-lite`` often answers 503 while demand is high. The SDK
does not retry unless retry options are set, and a single 503 becomes
"The assistant is unavailable right now."
"""

from google import genai
from google.genai import types

from app.core.config import settings

def gemini_client() -> genai.Client:
    # Four tries, about 0.5s then 1s then 2s apart. Long enough for a demand
    # spike to clear, short enough that chat does not sit on a dead model.
    return genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=4,
                initial_delay=0.5,
                max_delay=4.0,
            )
        ),
    )
