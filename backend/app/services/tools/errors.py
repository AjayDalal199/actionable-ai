class ToolServiceError(Exception):
    """Expected tool-registry failure whose message is safe to return."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidToolError(ToolServiceError):
    """Name, schema, URL, or kind does not match the registry rules."""


class DuplicateToolNameError(ToolServiceError):
    """This workspace already has a tool with this name."""


class ToolNotFoundError(ToolServiceError):
    """No tool with this id exists in the current workspace."""
