from datetime import date as date_, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.app.model.dto.group import GroupCreateDTO, GroupPanelSummaryDTO
from src.app.model.dto.payment import PaymentSummaryDTO
from src.app.model.dto.validators import serializable_enum
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.booking_type import BookingType

# Valores de `reason` usados por este módulo (modelo-de-dominio.md §5) —
# valores livres por ora, não um enum fechado.
REASON_CANCELED_BY_CLIENT = "canceled_by_client"
REASON_CANCELED_BY_COMPANY = "canceled_by_company"
REASON_PAYMENT_DENIED = "payment_denied"


class BookingCreateDTO(BaseModel):
    """`POST /api/bookings` — nesta fase só `type=closed`.

    `type` aceita string livre (não `serializable_enum`, que rejeitaria via
    422 antes do service poder converter em `INVALID_STATE` — o gancho da
    Onda 3 pede especificamente esse código de erro para `type=group`).
    """

    court_id: int = Field(..., ge=1)
    date: date_
    start_time: time
    end_time: time
    type: Optional[str] = Field(default="closed")
    # T-C (Onda 3, extensão pontual aditiva): payload do grupo quando
    # `type=group` (`backend-api-e-fluxos.md` §2.6). `None` no caminho
    # `type=closed`, que continua funcionando sem alteração.
    group: Optional[GroupCreateDTO] = None

    @field_validator("type")
    @classmethod
    def _normalize_type(cls, v: Optional[str]) -> str:
        return (v or "closed").strip().lower()


class BookingReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    court_id: int
    creator_user_id: Optional[int] = None
    creator_company_id: Optional[int] = None
    date: date_
    start_time: time
    end_time: time
    type: serializable_enum(BookingType)
    status: serializable_enum(BookingStatus)
    reason: Optional[str] = None
    total_price: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    created_at: datetime


class BookingCreateResponseDTO(BaseModel):
    """Resposta de `POST /api/bookings`: booking + pagamento pendente a
    confirmar (contrato Onda 2, `PaymentSummaryDTO` de T-B2).

    `group` (T-C, Onda 3, extensão aditiva): resumo do grupo recém-criado
    quando `type=group` — o pagamento embutido continua sendo o mesmo
    conceito (a cota do criador, `reference_type="group_member"`, em vez do
    valor total). `None` no caminho `type=closed`, que não muda."""

    booking: BookingReadDTO
    payment: PaymentSummaryDTO
    group: Optional[GroupPanelSummaryDTO] = None


class BookingCancelResponseDTO(BaseModel):
    booking: BookingReadDTO
    refunded: bool


class AvailabilityGroupDTO(BaseModel):
    """Dados do grupo embutidos no slot `open_group`. Onda 3 (T-C) preenche;
    nesta fase o slot nunca sai como `open_group`, então `group` é sempre
    `None` na resposta real — o schema já existe para não quebrar o
    contrato do front quando T-C plugar."""

    id: int
    total_spots: int
    filled_spots: int
    spot_price: int
    closing_deadline: datetime


class AvailabilitySlotDTO(BaseModel):
    start_time: time
    end_time: time
    status: str  # "free" | "busy" | "open_group"
    price: int
    group: Optional[AvailabilityGroupDTO] = None


class AvailabilityResponseDTO(BaseModel):
    court_id: int
    date: date_
    slots: list[AvailabilitySlotDTO] = Field(default_factory=list)
