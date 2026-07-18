from fastapi import APIRouter, Body, Depends, Path

from src.app.controller.dependencies import require_roles
from src.app.model.dto import Response
from src.app.model.dto.booking_admin import (
    BlockCreateDTO,
    BookingAdminResponseDTO,
    BookingCancelByCompanyResponseDTO,
    ManualBookingCreateDTO,
)
from src.app.model.enum import HttpCode, Level
from src.app.service.booking_admin_service import BookingAdminService
from src.infra.context import RequestContext

# Bloqueios (aninhados em /courts/{id}/blocks), reserva manual
# (/companies/me/manual-bookings) e cancelamento pelo estabelecimento
# (/bookings/{id}/...) — T-D, Fase D. Separado de `company_schedule_controller.py`
# (que fica só com as rotas de leitura, agenda + relatório) por coesão:
# aqui é tudo escrita/mutação de estado do painel.
blocks_router = APIRouter(prefix="/courts", tags=["Company Panel"])
manual_bookings_router = APIRouter(
    prefix="/companies/me/manual-bookings", tags=["Company Panel"]
)
bookings_admin_router = APIRouter(prefix="/bookings", tags=["Company Panel"])


@blocks_router.post(
    "/{court_id}/blocks",
    response_model=Response[BookingAdminResponseDTO],
    status_code=HttpCode.CREATED,
)
async def create_block(
    _=Depends(require_roles(Level.COMPANY)),
    service: BookingAdminService = Depends(BookingAdminService.get_service),
    court_id: int = Path(..., ge=1),
    dto: BlockCreateDTO = Body(...),
):
    booking = service.create_block(
        company_id=RequestContext.get_auth_company().company_id,
        court_id=court_id,
        dto=dto,
    )
    return Response(
        code=HttpCode.CREATED,
        message="Block created successfully",
        data=BookingAdminResponseDTO(booking=service.to_read_dto(booking)),
    )


@bookings_admin_router.delete(
    "/{booking_id}/block",
    response_model=Response[BookingAdminResponseDTO],
    status_code=HttpCode.OK,
)
async def remove_block(
    _=Depends(require_roles(Level.COMPANY)),
    service: BookingAdminService = Depends(BookingAdminService.get_service),
    booking_id: int = Path(..., ge=1),
):
    booking = service.remove_block(
        company_id=RequestContext.get_auth_company().company_id,
        booking_id=booking_id,
    )
    return Response(
        code=HttpCode.OK,
        message="Block removed successfully",
        data=BookingAdminResponseDTO(booking=service.to_read_dto(booking)),
    )


@manual_bookings_router.post(
    "",
    response_model=Response[BookingAdminResponseDTO],
    status_code=HttpCode.CREATED,
)
async def create_manual_booking(
    _=Depends(require_roles(Level.COMPANY)),
    service: BookingAdminService = Depends(BookingAdminService.get_service),
    dto: ManualBookingCreateDTO = Body(...),
):
    booking = service.create_manual_booking(
        company_id=RequestContext.get_auth_company().company_id, dto=dto
    )
    return Response(
        code=HttpCode.CREATED,
        message="Manual booking created successfully",
        data=BookingAdminResponseDTO(booking=service.to_read_dto(booking)),
    )


@bookings_admin_router.post(
    "/{booking_id}/cancel-by-company",
    response_model=Response[BookingCancelByCompanyResponseDTO],
    status_code=HttpCode.OK,
)
async def cancel_by_company(
    _=Depends(require_roles(Level.COMPANY)),
    service: BookingAdminService = Depends(BookingAdminService.get_service),
    booking_id: int = Path(..., ge=1),
):
    booking, refunded, group_canceled = service.cancel_by_company(
        booking_id=booking_id,
        company_id=RequestContext.get_auth_company().company_id,
    )
    return Response(
        code=HttpCode.OK,
        message="Booking canceled successfully",
        data=BookingCancelByCompanyResponseDTO(
            booking=service.to_read_dto(booking),
            refunded=refunded,
            group_canceled=group_canceled,
        ),
    )
