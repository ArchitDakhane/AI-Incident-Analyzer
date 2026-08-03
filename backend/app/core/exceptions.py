"""Custom exception classes for the application."""


class AppException(Exception):
    """Base exception class for the application."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        """Initialize exception with message and status code.

        Args:
            message: Exception message
            status_code: HTTP status code

        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationException(AppException):
    """Raised when validation fails."""

    def __init__(self, message: str) -> None:
        """Initialize validation exception."""
        super().__init__(message, status_code=422)


class AuthenticationException(AppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        """Initialize authentication exception."""
        super().__init__(message, status_code=401)


class AuthorizationException(AppException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Not authorized") -> None:
        """Initialize authorization exception."""
        super().__init__(message, status_code=403)


class ResourceNotFoundException(AppException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, resource_id: str | int) -> None:
        """Initialize resource not found exception."""
        message = f"{resource} with id {resource_id} not found"
        super().__init__(message, status_code=404)


class ConflictException(AppException):
    """Raised when a conflict occurs (e.g., duplicate resource)."""

    def __init__(self, message: str) -> None:
        """Initialize conflict exception."""
        super().__init__(message, status_code=409)


class ServiceException(AppException):
    """Raised when an external service fails."""

    def __init__(self, message: str) -> None:
        """Initialize service exception."""
        super().__init__(message, status_code=503)
