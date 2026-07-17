from contextvars import ContextVar
from typing import Optional

from src.app.model.dto import AuthCompany, AuthUser
from src.app.model.enum import AuthType, Level
from src.infra.exception.exceptions import UnauthorizedException


class RequestContext:
    """Estado do request corrente, propagado via ContextVar (seguro para asyncio)."""

    _auth_user: ContextVar[Optional[AuthUser]] = ContextVar(
        "auth_user",
        default=None,
    )
    _auth_company: ContextVar[Optional[AuthCompany]] = ContextVar(
        "auth_company",
        default=None,
    )
    _auth_type: ContextVar[Optional[AuthType]] = ContextVar(
        "auth_type",
        default=None,
    )

    @staticmethod
    def set_auth_user(auth_user: AuthUser) -> None:
        RequestContext._auth_user.set(auth_user)
        RequestContext._auth_type.set(AuthType.USER)

    @staticmethod
    def get_auth_user() -> AuthUser:
        auth_user = RequestContext._auth_user.get()
        if not auth_user:
            raise UnauthorizedException()
        return auth_user

    @staticmethod
    def set_auth_company(auth_company: AuthCompany) -> None:
        RequestContext._auth_company.set(auth_company)
        RequestContext._auth_type.set(AuthType.COMPANY)

    @staticmethod
    def get_auth_company() -> AuthCompany:
        auth_company = RequestContext._auth_company.get()
        if not auth_company:
            raise UnauthorizedException()
        return auth_company

    @staticmethod
    def get_auth_type() -> AuthType:
        auth_type = RequestContext._auth_type.get()
        if not auth_type:
            raise UnauthorizedException()
        return auth_type

    @staticmethod
    def get_current_role() -> Level:
        auth_type = RequestContext._auth_type.get()
        if auth_type == AuthType.USER:
            return RequestContext._auth_user.get().role
        if auth_type == AuthType.COMPANY:
            return RequestContext._auth_company.get().role
        raise UnauthorizedException()

    @staticmethod
    def clear() -> None:
        RequestContext._auth_user.set(None)
        RequestContext._auth_company.set(None)
        RequestContext._auth_type.set(None)
