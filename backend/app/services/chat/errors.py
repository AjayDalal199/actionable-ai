PROVIDER_MESSAGE = "The assistant is unavailable right now."
UNAVAILABLE_MESSAGE = "The assistant is unavailable right now."
REJECT_MESSAGE = "No problem, I won't do that."
UNKNOWN_MESSAGE = "I don't know."
EMPTY_ANSWER = "I couldn't produce an answer."
DONE_MESSAGE = "Done."
TOOL_FAILED = "The action failed."
ACTION_UNAVAILABLE = "That action is not available."


class ChatServiceError(Exception):
    """Expected chat failure whose message is safe to return before a stream starts."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidChatMessage(ChatServiceError):
    """The user text is empty after truncation."""


class ChatSessionNotFound(ChatServiceError):
    """The session id belongs to another workspace, or it cannot be resumed."""


class PendingActionNotFound(ChatServiceError):
    """No pending action for this workspace."""


class ProviderError(ChatServiceError):
    """The embedding or chat provider failed. The SSE event stays generic."""
