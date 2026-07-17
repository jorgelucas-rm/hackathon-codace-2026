from fastapi import APIRouter, Body, Depends, Path, Query

from src.app.controller.dependencies import get_filters, require_roles
from src.app.model.dto import Pagination, Response, UserCreateDTO, UserReadDTO, UserUpdateDTO
from src.app.model.enum import HttpCode, Level
from src.app.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])
admin_router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=Response[UserReadDTO],
    status_code=HttpCode.CREATED,
)
async def register_user(
    service: UserService = Depends(UserService.get_service),
    dto: UserCreateDTO = Body(...),
):
    user = service.register(dto=dto)
    return Response(
        code=HttpCode.CREATED,
        message="User registered successfully",
        data=UserReadDTO.model_validate(user),
    )


@admin_router.get(
    "",
    response_model=Response[Pagination[UserReadDTO]],
    status_code=HttpCode.OK,
)
async def list_users(
    _=Depends(require_roles(Level.ADMIN)),
    service: UserService = Depends(UserService.get_service),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=1000),
    order_by: str | None = Query(None),
    order_direction: str | None = Query(None),
    filters: dict = Depends(get_filters),
):
    return Response(
        code=HttpCode.OK,
        message="Users retrieved successfully",
        data=service.get_all_paginated(
            page=page,
            page_size=size,
            order_by=order_by,
            order_direction=order_direction,
            filters=filters,
        ),
    )


@admin_router.get(
    "/{user_id}",
    response_model=Response[UserReadDTO],
    status_code=HttpCode.OK,
)
async def get_user(
    _=Depends(require_roles(Level.ADMIN)),
    service: UserService = Depends(UserService.get_service),
    user_id: int = Path(..., ge=1),
):
    user = service.get_by_id(user_id=user_id)
    return Response(
        code=HttpCode.OK,
        message="User retrieved successfully",
        data=UserReadDTO.model_validate(user),
    )


@admin_router.put(
    "/{user_id}",
    response_model=Response[UserReadDTO],
    status_code=HttpCode.OK,
)
async def update_user(
    _=Depends(require_roles(Level.ADMIN)),
    service: UserService = Depends(UserService.get_service),
    user_id: int = Path(..., ge=1),
    dto: UserUpdateDTO = Body(...),
):
    user = service.update(user_id=user_id, dto=dto)
    return Response(
        code=HttpCode.OK,
        message="User updated successfully",
        data=UserReadDTO.model_validate(user),
    )
