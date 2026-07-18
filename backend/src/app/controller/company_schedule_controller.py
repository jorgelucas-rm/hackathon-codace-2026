from datetime import date as date_

from fastapi import APIRouter, Depends, Query

from src.app.controller.dependencies import require_roles
from src.app.model.dto import Response
from src.app.model.dto.booking_admin import CompanyReportDTO
from src.app.model.dto.company_schedule import CompanyScheduleResponseDTO
from src.app.model.enum import HttpCode, Level
from src.app.service.company_schedule_service import CompanyScheduleService
from src.infra.context import RequestContext

# Painel da company (T-D, Fase D): agenda do dia e relatório. Rotas
# aninhadas em /companies/me (dono autenticado).
router = APIRouter(prefix="/companies/me", tags=["Company Panel"])


@router.get(
    "/schedule",
    response_model=Response[CompanyScheduleResponseDTO],
    status_code=HttpCode.OK,
)
async def get_schedule(
    _=Depends(require_roles(Level.COMPANY)),
    service: CompanyScheduleService = Depends(CompanyScheduleService.get_service),
    date: date_ = Query(...),
):
    schedule = service.get_schedule(
        company_id=RequestContext.get_auth_company().company_id, date=date
    )
    return Response(
        code=HttpCode.OK,
        message="Schedule retrieved successfully",
        data=schedule,
    )


@router.get(
    "/report",
    response_model=Response[CompanyReportDTO],
    status_code=HttpCode.OK,
)
async def get_report(
    _=Depends(require_roles(Level.COMPANY)),
    service: CompanyScheduleService = Depends(CompanyScheduleService.get_service),
    from_date: date_ = Query(..., alias="from"),
    to_date: date_ = Query(..., alias="to"),
):
    report = service.get_report(
        company_id=RequestContext.get_auth_company().company_id,
        from_date=from_date,
        to_date=to_date,
    )
    return Response(
        code=HttpCode.OK,
        message="Report retrieved successfully",
        data=report,
    )
