from datetime import date as date_

from fastapi import APIRouter, Depends, Path, Query

from src.app.model.dto import Response
from src.app.model.dto.booking import AvailabilityResponseDTO
from src.app.model.enum import HttpCode
from src.app.service.availability_service import AvailabilityService

# Rota pública aninhada em `/courts/{id}/availability` — mesmo prefixo de
# `court_controller.router`, path distinto, registrado como router separado
# (mesmo padrão de `courts_me_router`/`courts_router` coexistindo).
router = APIRouter(prefix="/courts", tags=["Availability"])


@router.get(
    "/{court_id}/availability",
    response_model=Response[AvailabilityResponseDTO],
    status_code=HttpCode.OK,
)
async def get_court_availability(
    service: AvailabilityService = Depends(AvailabilityService.get_service),
    court_id: int = Path(..., ge=1),
    date: date_ = Query(...),
):
    return Response(
        code=HttpCode.OK,
        message="Availability retrieved successfully",
        data=service.get_availability(court_id=court_id, date=date),
    )
