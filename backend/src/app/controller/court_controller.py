from fastapi import APIRouter, Body, Depends, File, Path, UploadFile

from src.app.controller.dependencies import require_roles
from src.app.model.dto import Response
from src.app.model.dto.court import (
    CourtCreateDTO,
    CourtDetailDTO,
    CourtReadDTO,
    CourtUpdateDTO,
)
from src.app.model.enum import HttpCode, Level
from src.app.service.court_service import CourtService
from src.infra.context import RequestContext

# Rotas aninhadas em /companies/me/courts (dono autenticado).
me_router = APIRouter(prefix="/companies/me/courts", tags=["Courts"])
# Rotas públicas/próprias de quadra.
router = APIRouter(prefix="/courts", tags=["Courts"])


@me_router.post(
    "",
    response_model=Response[CourtReadDTO],
    status_code=HttpCode.CREATED,
)
async def create_my_court(
    _=Depends(require_roles(Level.COMPANY)),
    service: CourtService = Depends(CourtService.get_service),
    dto: CourtCreateDTO = Body(...),
):
    court = service.create(
        company_id=RequestContext.get_auth_company().company_id, dto=dto
    )
    return Response(
        code=HttpCode.CREATED,
        message="Court created successfully",
        data=service.to_read_dto(court),
    )


@me_router.get(
    "",
    response_model=Response[list[CourtReadDTO]],
    status_code=HttpCode.OK,
)
async def list_my_courts(
    _=Depends(require_roles(Level.COMPANY)),
    service: CourtService = Depends(CourtService.get_service),
):
    return Response(
        code=HttpCode.OK,
        message="Courts retrieved successfully",
        data=service.list_by_company(
            company_id=RequestContext.get_auth_company().company_id
        ),
    )


@me_router.post(
    "/{court_id}/photos",
    response_model=Response[CourtReadDTO],
    status_code=HttpCode.OK,
)
async def upload_my_court_photo(
    _=Depends(require_roles(Level.COMPANY)),
    service: CourtService = Depends(CourtService.get_service),
    court_id: int = Path(..., ge=1),
    file: UploadFile = File(...),
):
    court = service.add_photo(
        court_id=court_id,
        company_id=RequestContext.get_auth_company().company_id,
        file=file,
    )
    return Response(
        code=HttpCode.OK,
        message="Photo uploaded successfully",
        data=service.to_read_dto(court),
    )


@me_router.delete(
    "/{court_id}/photos/{index}",
    response_model=Response[CourtReadDTO],
    status_code=HttpCode.OK,
)
async def delete_my_court_photo(
    _=Depends(require_roles(Level.COMPANY)),
    service: CourtService = Depends(CourtService.get_service),
    court_id: int = Path(..., ge=1),
    index: int = Path(..., ge=0),
):
    court = service.remove_photo(
        court_id=court_id,
        company_id=RequestContext.get_auth_company().company_id,
        index=index,
    )
    return Response(
        code=HttpCode.OK,
        message="Photo removed successfully",
        data=service.to_read_dto(court),
    )


@router.get(
    "/{court_id}",
    response_model=Response[CourtDetailDTO],
    status_code=HttpCode.OK,
)
async def get_court(
    service: CourtService = Depends(CourtService.get_service),
    court_id: int = Path(..., ge=1),
):
    return Response(
        code=HttpCode.OK,
        message="Court retrieved successfully",
        data=service.get_detail(court_id=court_id),
    )


@router.patch(
    "/{court_id}",
    response_model=Response[CourtReadDTO],
    status_code=HttpCode.OK,
)
async def update_court(
    _=Depends(require_roles(Level.COMPANY)),
    service: CourtService = Depends(CourtService.get_service),
    court_id: int = Path(..., ge=1),
    dto: CourtUpdateDTO = Body(...),
):
    court = service.update(
        court_id=court_id,
        company_id=RequestContext.get_auth_company().company_id,
        dto=dto,
    )
    return Response(
        code=HttpCode.OK,
        message="Court updated successfully",
        data=service.to_read_dto(court),
    )
