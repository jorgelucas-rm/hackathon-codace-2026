from datetime import date as date_, time
from typing import Optional

from pydantic import BaseModel, Field

from src.app.model.dto.booking import BookingReadDTO

# T-D (Fase D, Onda 3) — DTOs próprios de bloqueio/reserva manual/
# cancelamento pelo estabelecimento/relatório. Não editar `dto/booking.py`
# (T-B1/T-C) — só o reaproveita para embutir `BookingReadDTO` nas respostas.


class BlockCreateDTO(BaseModel):
    """`POST /api/courts/{id}/blocks`."""

    date: date_
    start_time: time
    end_time: time
    reason: Optional[str] = Field(default=None, max_length=255)


class ManualBookingCreateDTO(BaseModel):
    """`POST /api/companies/me/manual-bookings` — reserva de balcão, nasce
    `CONFIRMED` direto (sem payment), preço calculado no servidor igual ao
    fluxo normal."""

    court_id: int = Field(..., ge=1)
    date: date_
    start_time: time
    end_time: time
    customer_name: str = Field(..., min_length=1, max_length=150)
    customer_phone: str = Field(..., min_length=1, max_length=20)


class BookingAdminResponseDTO(BaseModel):
    """Resposta comum de bloqueio/desbloqueio/reserva manual."""

    booking: BookingReadDTO


class BookingCancelByCompanyResponseDTO(BaseModel):
    """Resposta de `POST /api/bookings/{id}/cancel-by-company`.
    `group_canceled` indica se a cascata `GroupService.cancel_group` foi
    disparada (booking `type == GROUP`)."""

    booking: BookingReadDTO
    refunded: bool
    group_canceled: bool


class CompanyReportDTO(BaseModel):
    """`GET /api/companies/me/report?from=&to=` — relatório simples
    (ocupação aproximada, receita confirmada, picos de dia/horário). Forma
    exata é decisão de T-D, documentada no service."""

    from_date: date_
    to_date: date_
    total_bookings: int
    confirmed_revenue: int
    occupied_slots: int
    available_slots: int
    occupancy_rate: float
    peak_day: Optional[date_] = None
    peak_hour: Optional[time] = None
