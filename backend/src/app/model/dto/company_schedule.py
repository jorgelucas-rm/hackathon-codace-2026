from datetime import date as date_, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.app.model.dto.group import GroupPanelSummaryDTO
from src.app.model.dto.validators import serializable_enum
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.booking_type import BookingType

# T-D (Fase D, Onda 3) — DTOs próprios do painel da company. Não confundir
# com `dto/booking.py` (T-B1/T-C), que não é editado por esta task.


class ScheduleCustomerDTO(BaseModel):
    """Cliente embutido num booking da agenda: dados de `User` quando
    `creator_user_id` está setado (reserva feita pelo app); senão
    `customer_name`/`customer_phone` (reserva manual ou bloqueio sem
    cliente identificado)."""

    name: Optional[str] = None
    phone: Optional[str] = None


class ScheduleBookingDTO(BaseModel):
    """Um booking ativo na grade do dia. Se `type == GROUP`, `group` é
    preenchido via `GroupService.get_panel_summary(booking.id)` (contrato
    T-C<->T-D)."""

    id: int
    court_id: int
    date: date_
    start_time: time
    end_time: time
    type: serializable_enum(BookingType)
    status: serializable_enum(BookingStatus)
    reason: Optional[str] = None
    total_price: int
    customer: Optional[ScheduleCustomerDTO] = None
    group: Optional[GroupPanelSummaryDTO] = None


class CourtScheduleDTO(BaseModel):
    court_id: int
    court_name: str
    bookings: list[ScheduleBookingDTO] = Field(default_factory=list)


class CompanyScheduleResponseDTO(BaseModel):
    """`GET /api/companies/me/schedule?date=` — grade do dia de todas as
    courts da company autenticada."""

    model_config = ConfigDict(from_attributes=True)

    date: date_
    courts: list[CourtScheduleDTO] = Field(default_factory=list)
