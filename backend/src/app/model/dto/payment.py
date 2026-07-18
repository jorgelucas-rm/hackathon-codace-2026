from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

from src.app.model.dto.validators import serializable_enum
from src.app.model.enum.payment_method import PaymentMethod
from src.app.model.enum.payment_status import PaymentStatus


class PaymentSummaryDTO(BaseModel):
    """Contrato Onda 2 (B1<->B2) — esqueleto commitado pelo orquestrador.

    Forma mínima usada por quem só precisa *referenciar* um pagamento (ex.:
    T-B1 embute isto na resposta de `POST /api/bookings`). T-B2 é dono deste
    arquivo e pode adicionar `PaymentReadDTO`/`PaymentConfirmDTO` etc. à
    vontade, mas não deve remover ou quebrar este DTO — é consumido fora do
    módulo de payment.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_type: str
    reference_id: int
    amount: int
    method: Optional[serializable_enum(PaymentMethod)] = None
    status: serializable_enum(PaymentStatus)
    created_at: datetime


class PaymentReadDTO(BaseModel):
    """Forma completa de leitura (`GET /api/payments/{id}`), incluindo o
    split e o estorno — além do que `PaymentSummaryDTO` expõe."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_type: str
    reference_id: int
    amount: int
    method: Optional[serializable_enum(PaymentMethod)] = None
    status: serializable_enum(PaymentStatus)
    company_payout: Optional[int] = None
    platform_fee: Optional[int] = None
    gateway_fee: Optional[int] = None
    refunded_at: Optional[datetime] = None
    created_at: datetime


class PaymentConfirmDTO(BaseModel):
    """Body de `POST /api/payments/{id}/confirm` — simulador de gateway."""

    result: Literal["approved", "denied"]
    method: Optional[serializable_enum(PaymentMethod)] = None
