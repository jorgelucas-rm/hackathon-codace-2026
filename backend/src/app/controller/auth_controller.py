from fastapi import APIRouter, Body, Depends, Request

from src.app.controller.dependencies import require_auth
from src.app.model.dto import LoginCompany, LoginUser, Response
from src.app.model.enum import HttpCode
from src.app.service import AuthService
from src.infra.middleware.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get(
    "/me",
    status_code=HttpCode.OK,
)
async def me(
    _=Depends(require_auth),
    service: AuthService = Depends(AuthService.get_service),
):
    return Response(
        code=HttpCode.OK,
        message="Data retrieved successfully",
        data=service.get_me(),
    )


@router.post(
    "/user-login",
    response_model=Response[str],
    status_code=HttpCode.OK,
)
@limiter.limit("5/minute")
async def user_login(
    request: Request,
    service: AuthService = Depends(AuthService.get_service),
    login: LoginUser = Body(...),
):
    token = service.user_login(login=login)
    return Response(code=HttpCode.OK, message="Login successful", data=token)


@router.post(
    "/company-login",
    response_model=Response[str],
    status_code=HttpCode.OK,
)
@limiter.limit("5/minute")
async def company_login(
    request: Request,
    service: AuthService = Depends(AuthService.get_service),
    login: LoginCompany = Body(...),
):
    token = service.company_login(login=login)
    return Response(code=HttpCode.OK, message="Login successful", data=token)
