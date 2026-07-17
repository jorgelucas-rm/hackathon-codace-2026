from typing import Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.app.controller.dependencies.ip_address import get_client_ip
from src.app.model.dto.auth import AuthCompany, AuthUser
from src.app.model.enum import AuthType, ErrorCode, Level
from src.infra.context import RequestContext
from src.infra.exception.exceptions import ForbiddenException
from src.infra.security.jwt_service import JWTService

oauth2_scheme = HTTPBearer()


async def require_auth(
    request: Request,
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> None:
    payload = JWTService.decode_token(token.credentials)

    sub = payload.get("sub")

    if not sub:
        raise ForbiddenException(
            message="Invalid token",
            error_code=ErrorCode.INVALID_TOKEN,
        )

    role_value = payload.get("role")
    role = Level(role_value)

    auth_type_value = payload.get("auth_type")
    auth_type = AuthType(auth_type_value)

    uid = int(sub)
    if auth_type == AuthType.USER:
        RequestContext.set_auth_user(
            AuthUser(
                ip=get_client_ip(request=request),
                user_id=uid,
                role=role,
            ),
        )

    elif auth_type == AuthType.COMPANY:
        RequestContext.set_auth_company(
            AuthCompany(
                ip=get_client_ip(request=request),
                company_id=uid,
                role=role,
            ),
        )

    else:
        raise ForbiddenException(
            message="Invalid token",
            error_code=ErrorCode.INVALID_TOKEN,
        )


def require_roles(*allowed_roles: Level) -> Callable[..., None]:
    def dependency(_=Depends(require_auth)) -> None:
        role = RequestContext.get_current_role()
        if role not in allowed_roles:
            raise ForbiddenException(
                message="Not authorized",
                error_code=ErrorCode.FORBIDDEN,
            )

    return dependency
