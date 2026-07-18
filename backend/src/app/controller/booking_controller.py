from fastapi import APIRouter, Body, Depends, Path, Query

from src.app.controller.dependencies import require_roles
from src.app.model.dto import Response
from src.app.model.dto.booking import (
    BookingCancelResponseDTO,
    BookingCreateDTO,
    BookingCreateResponseDTO,
    BookingReadDTO,
)
from src.app.model.enum import AuthType, HttpCode, Level
from src.app.service.booking_service import BookingService
from src.infra.context import RequestContext

# Rotas de agendamento próprias (`/bookings`) e aninhadas em
# `/users/me/bookings` (agenda do usuário logado).
router = APIRouter(prefix="/bookings", tags=["Bookings"])
me_router = APIRouter(prefix="/users/me/bookings", tags=["Bookings"])


@router.post(
    "",
    response_model=Response[BookingCreateResponseDTO],
    status_code=HttpCode.CREATED,
)
async def create_booking(
    _=Depends(require_roles(Level.USER)),
    service: BookingService = Depends(BookingService.get_service),
    dto: BookingCreateDTO = Body(...),
):
    booking, payment = service.create_closed_booking(
        user_id=RequestContext.get_auth_user().user_id, dto=dto
    )
    return Response(
        code=HttpCode.CREATED,
        message="Booking created successfully",
        data=BookingCreateResponseDTO(
            booking=service.to_read_dto(booking),
            payment=service.payment_service.to_summary_dto(payment),
        ),
    )


@router.get(
    "/{booking_id}",
    response_model=Response[BookingReadDTO],
    status_code=HttpCode.OK,
)
async def get_booking(
    _=Depends(require_roles(Level.USER, Level.COMPANY)),
    service: BookingService = Depends(BookingService.get_service),
    booking_id: int = Path(..., ge=1),
):
    auth_type = RequestContext.get_auth_type()
    user_id = (
        RequestContext.get_auth_user().user_id if auth_type == AuthType.USER else None
    )
    company_id = (
        RequestContext.get_auth_company().company_id
        if auth_type == AuthType.COMPANY
        else None
    )
    booking = service.get_detail(
        booking_id=booking_id, user_id=user_id, company_id=company_id
    )
    return Response(
        code=HttpCode.OK,
        message="Booking retrieved successfully",
        data=service.to_read_dto(booking),
    )


@router.post(
    "/{booking_id}/cancel",
    response_model=Response[BookingCancelResponseDTO],
    status_code=HttpCode.OK,
)
async def cancel_booking(
    _=Depends(require_roles(Level.USER)),
    service: BookingService = Depends(BookingService.get_service),
    booking_id: int = Path(..., ge=1),
):
    booking, refunded = service.cancel_by_user(
        booking_id=booking_id, user_id=RequestContext.get_auth_user().user_id
    )
    return Response(
        code=HttpCode.OK,
        message="Booking canceled successfully",
        data=BookingCancelResponseDTO(
            booking=service.to_read_dto(booking), refunded=refunded
        ),
    )


@me_router.get(
    "",
    response_model=Response[list[BookingReadDTO]],
    status_code=HttpCode.OK,
)
async def list_my_bookings(
    _=Depends(require_roles(Level.USER)),
    service: BookingService = Depends(BookingService.get_service),
    scope: str = Query(default="upcoming", pattern="^(upcoming|history)$"),
):
    bookings = service.list_by_user(
        user_id=RequestContext.get_auth_user().user_id, scope=scope
    )
    return Response(
        code=HttpCode.OK,
        message="Bookings retrieved successfully",
        data=[service.to_read_dto(b) for b in bookings],
    )
