"""Custom exceptions and error response helpers."""

from dataclasses import dataclass
from typing import Any


@dataclass
class AppError(Exception):
    message: str
    status_code: int = 400
    error_code: str = "bad_request"
    extra: dict[str, Any] | None = None


class NotFoundError(AppError):
    def __init__(self, message: str, extra: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=404, error_code="not_found", extra=extra)


class ConflictError(AppError):
    def __init__(self, message: str, extra: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=409, error_code="conflict", extra=extra)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Missing or invalid demo user.", extra: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=401, error_code="unauthorized", extra=extra)


class AIProviderError(AppError):
    def __init__(self, message: str, extra: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=502, error_code="ai_provider_error", extra=extra)
