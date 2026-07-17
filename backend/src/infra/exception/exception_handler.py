from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.app.model.dto.response import Response
from src.app.model.enum import ErrorCode, HttpCode
from src.infra.exception.domain_exception import DomainException


async def global_exception_handler(request: Request, exception: Exception):
    if isinstance(exception, RateLimitExceeded):
        return JSONResponse(
            status_code=HttpCode.TOO_MANY_REQUESTS,
            content=Response(
                code=HttpCode.TOO_MANY_REQUESTS,
                error_code=ErrorCode.TOO_MANY_REQUESTS,
                message="Too many requests. Please try again later.",
            ).model_dump(),
        )

    if isinstance(exception, DomainException):
        return _handle_domain_exception(exception)

    elif isinstance(exception, StarletteHTTPException):
        return _handle_starlette_exception(exception)

    elif isinstance(exception, RequestValidationError):
        return _handle_validation_exception(exception)

    return JSONResponse(
        status_code=HttpCode.INTERNAL_SERVER_ERROR,
        content=Response(
            code=HttpCode.INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="Unexpected error.",
        ).model_dump(),
    )


def _handle_domain_exception(exception: DomainException):
    return JSONResponse(
        status_code=exception.http_code,
        content=Response(
            code=exception.http_code,
            error_code=exception.error_code,
            message=exception.message,
        ).model_dump(),
    )


def _handle_starlette_exception(exception: StarletteHTTPException):
    http_code = exception.status_code
    message = "Unexpected error." if http_code == HttpCode.INTERNAL_SERVER_ERROR else str(exception.detail)

    return JSONResponse(
        status_code=http_code,
        content=Response(
            code=http_code,
            error_code=ErrorCode.UNEXPECTED_ERROR,
            message=message,
        ).model_dump(),
    )


def _handle_validation_exception(exception: RequestValidationError):
    http_code = HttpCode.UNPROCESSABLE_ENTITY
    error_code = ErrorCode.UNPROCESSABLE_ENTITY
    messages = []

    for err in exception.errors():
        loc = err.get("loc", [])
        msg = err.get("msg", "")

        if "JSON decode error" in msg:
            message = "Invalid JSON body."
            break

        if len(loc) > 1:
            field = loc[-1]
            messages.append(f"{field}: {msg}")
        else:
            messages.append(msg)

    else:
        message = " | ".join(messages)

    return JSONResponse(
        status_code=http_code,
        content=Response(
            code=http_code,
            error_code=error_code,
            message=message,
        ).model_dump(),
    )
