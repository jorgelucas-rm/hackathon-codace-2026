from fastapi import APIRouter, Body, Depends, Path, Query

from src.app.controller.dependencies import get_filters, require_roles
from src.app.model.dto import (
    CompanyCreateDTO,
    CompanyReadDTO,
    CompanyUpdateDTO,
    Pagination,
    Response,
)
from src.app.model.dto.company import (
    CompanyDetailDTO,
    CompanyMeUpdateDTO,
    CompanySearchCardDTO,
)
from src.app.model.enum import HttpCode, Level
from src.app.service import CompanyService
from src.infra.context import RequestContext

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


@router.get(
    "",
    response_model=Response[Pagination[CompanySearchCardDTO]],
    status_code=HttpCode.OK,
)
async def search_companies(
    service: CompanyService = Depends(CompanyService.get_service),
    lat: float | None = Query(default=None),
    lng: float | None = Query(default=None),
    raio_km: float | None = Query(default=None, gt=0),
    sport_id: int | None = Query(default=None),
    amenities: list[str] | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
):
    """Busca pública da vitrine — só `situation=True`. Card com distância
    (se `lat`/`lng` informados), menor preço/hora entre quadras ativas e
    nota média (placeholder `null` até a Fase F)."""
    return Response(
        code=HttpCode.OK,
        message="Companies retrieved successfully",
        data=service.search_public(
            lat=lat,
            lng=lng,
            raio_km=raio_km,
            sport_id=sport_id,
            amenities=amenities,
            q=q,
            page=page,
            page_size=size,
        ),
    )


@router.patch(
    "/me",
    response_model=Response[CompanyReadDTO],
    status_code=HttpCode.OK,
)
async def update_my_company(
    _=Depends(require_roles(Level.COMPANY)),
    service: CompanyService = Depends(CompanyService.get_service),
    dto: CompanyMeUpdateDTO = Body(...),
):
    company = service.update_me(
        company_id=RequestContext.get_auth_company().company_id, dto=dto
    )
    return Response(
        code=HttpCode.OK,
        message="Company updated successfully",
        data=CompanyReadDTO.model_validate(company),
    )


@router.get(
    "/{company_id}",
    response_model=Response[CompanyDetailDTO],
    status_code=HttpCode.OK,
)
async def get_company_detail(
    service: CompanyService = Depends(CompanyService.get_service),
    company_id: int = Path(..., ge=1),
):
    """Detalhe público completo: fotos, comodidades, horário de
    funcionamento, quadras ativas e nota média (placeholder)."""
    return Response(
        code=HttpCode.OK,
        message="Company retrieved successfully",
        data=service.get_detail(company_id=company_id),
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
