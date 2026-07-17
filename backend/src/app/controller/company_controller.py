from fastapi import APIRouter, Body, Depends, Path, Query

from src.app.controller.dependencies import get_filters, require_roles
from src.app.model.dto import (
    CompanyCreateDTO,
    CompanyReadDTO,
    CompanyUpdateDTO,
    Pagination,
    Response,
)
from src.app.model.enum import HttpCode, Level
from src.app.service import CompanyService

router = APIRouter(prefix="/companies", tags=["Companies"])
admin_router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post(
    "",
    response_model=Response[CompanyReadDTO],
    status_code=HttpCode.CREATED,
)
async def register_company(
    service: CompanyService = Depends(CompanyService.get_service),
    dto: CompanyCreateDTO = Body(...),
):
    company = service.register(dto=dto)
    return Response(
        code=HttpCode.CREATED,
        message="Company registered successfully",
        data=CompanyReadDTO.model_validate(company),
    )


@admin_router.get(
    "",
    response_model=Response[Pagination[CompanyReadDTO]],
    status_code=HttpCode.OK,
)
async def list_companies(
    _=Depends(require_roles(Level.ADMIN)),
    service: CompanyService = Depends(CompanyService.get_service),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=1000),
    order_by: str | None = Query(None),
    order_direction: str | None = Query(None),
    filters: dict = Depends(get_filters),
):
    return Response(
        code=HttpCode.OK,
        message="Companies retrieved successfully",
        data=service.get_all_paginated(
            page=page,
            page_size=size,
            order_by=order_by,
            order_direction=order_direction,
            filters=filters,
        ),
    )


@admin_router.get(
    "/{company_id}",
    response_model=Response[CompanyReadDTO],
    status_code=HttpCode.OK,
)
async def get_company(
    _=Depends(require_roles(Level.ADMIN)),
    service: CompanyService = Depends(CompanyService.get_service),
    company_id: int = Path(..., ge=1),
):
    company = service.get_by_id(company_id=company_id)
    return Response(
        code=HttpCode.OK,
        message="Company retrieved successfully",
        data=CompanyReadDTO.model_validate(company),
    )


@admin_router.put(
    "/{company_id}",
    response_model=Response[CompanyReadDTO],
    status_code=HttpCode.OK,
)
async def update_company(
    _=Depends(require_roles(Level.ADMIN)),
    service: CompanyService = Depends(CompanyService.get_service),
    company_id: int = Path(..., ge=1),
    dto: CompanyUpdateDTO = Body(...),
):
    company = service.update(company_id=company_id, dto=dto)
    return Response(
        code=HttpCode.OK,
        message="Company updated successfully",
        data=CompanyReadDTO.model_validate(company),
    )
