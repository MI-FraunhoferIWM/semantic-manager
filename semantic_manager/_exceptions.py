class SemanticManagerError(Exception):
    """Base exception for all SemanticManager errors."""


class AuthenticationError(SemanticManagerError):
    """Raised when authentication fails (401)."""


class NotFoundError(SemanticManagerError):
    """Raised when a requested resource does not exist (404)."""


class APIError(SemanticManagerError):
    """Raised for unexpected HTTP errors."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")