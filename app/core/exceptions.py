class AppError(Exception):
    """Base platform error."""


class NotFoundError(AppError):
    """Raised when a resource does not exist."""


class ValidationError(AppError):
    """Raised when input validation fails."""

