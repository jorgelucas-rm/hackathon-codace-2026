from src.app.model.enum import ErrorCode, HttpCode
from src.infra.exception.domain_exception import DomainException


class UnauthorizedException(DomainException):
    def __init__(
        self,
        message: str = "Unauthorized access",
        error_code: ErrorCode = ErrorCode.UNAUTHORIZED,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            http_code=HttpCode.UNAUTHORIZED,
        )


class ForbiddenException(DomainException):
    def __init__(
        self,
        message: str = "You do not have permission to access this resource",
        error_code: ErrorCode = ErrorCode.FORBIDDEN,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            http_code=HttpCode.FORBIDDEN,
        )


class NotFoundException(DomainException):
    def __init__(
        self,
        resource: str = "Resource",
        error_code: ErrorCode = ErrorCode.NOT_FOUND,
    ):
        super().__init__(
            message=f"{resource} not found",
            error_code=error_code,
            http_code=HttpCode.NOT_FOUND,
        )


class ConflictException(DomainException):
    def __init__(
        self,
        message: str = "Conflict detected",
        error_code: ErrorCode = ErrorCode.CONFLICT,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            http_code=HttpCode.CONFLICT,
        )


class BadRequestException(DomainException):
    def __init__(
        self,
        error_type: str,
        details: str = "",
        error_code: ErrorCode = ErrorCode.UNPROCESSABLE_ENTITY,
    ):
        message = f"Error in requisition: {error_type}"
        if details:
            message = f"{message} - {details}"

        super().__init__(
            message=message,
            error_code=error_code,
            http_code=HttpCode.UNPROCESSABLE_ENTITY,
        )


class EnvironmentException(DomainException):
    def __init__(
        self,
        key: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
    ):
        super().__init__(
            message=f"Required environment variable not defined: {key}",
            error_code=error_code,
            http_code=HttpCode.INTERNAL_SERVER_ERROR,
        )


class PasswordException(DomainException):
    def __init__(self, error_code: ErrorCode, message: str):
        super().__init__(
            message=message,
            error_code=error_code,
            http_code=HttpCode.BAD_REQUEST,
        )


class InvalidVerificationCodeException(DomainException):
    def __init__(
        self,
        message: str = "Invalid verification code",
        error_code: ErrorCode = ErrorCode.INVALID_CODE,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            http_code=HttpCode.BAD_REQUEST,
        )


class StorageException(DomainException):
    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        message: str = "Storage operation failed",
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            http_code=HttpCode.INTERNAL_SERVER_ERROR,
        )
