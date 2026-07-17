from src.app.model.enum import ErrorCode, HttpCode


class DomainException(Exception):
    """Base para todas as exceções de domínio."""

    error_code: ErrorCode | None
    http_code: HttpCode

    def __init__(self, message: str, error_code: ErrorCode | None, http_code: HttpCode):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.http_code = http_code
