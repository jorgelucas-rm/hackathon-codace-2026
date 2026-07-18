from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Contrato Onda 3 (T-C<->T-D) — esqueleto commitado pelo orquestrador.


class GroupCreateDTO(BaseModel):
    """Payload embutido em `POST /api/bookings` quando `type=group`
    (`backend-api-e-fluxos.md` §2.6). T-C adiciona o campo
    `group: Optional[GroupCreateDTO] = None` em `BookingCreateDTO`
    (`dto/booking.py`) — extensão pontual autorizada nesta onda (arquivo
    de T-B1, Onda 2 já fechada, sem conflito com T-D)."""

    total_spots: int = Field(..., ge=1)
    min_spots: int = Field(..., ge=1)
    visibility: Literal["public", "link"] = "public"
    closing_deadline: datetime
    leftover_rule: Literal["creator_absorbs", "recalculate_quota"] = "creator_absorbs"


class GroupPanelSummaryDTO(BaseModel):
    """Retornada por `GroupService.get_panel_summary(booking_id)`. Usada por
    T-C (slot `open_group` da disponibilidade, mapeada para
    `AvailabilityGroupDTO` em `dto/booking.py`) e por T-D (grade do painel,
    `GET /api/companies/me/schedule`) — é o contrato que evita T-D precisar
    conhecer `OpenGroup`/`GroupMember` diretamente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    total_spots: int
    min_spots: int
    filled_spots: int
    spot_price: int
    visibility: str
    closing_deadline: datetime
