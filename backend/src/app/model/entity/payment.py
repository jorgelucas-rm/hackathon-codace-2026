from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func, text

from src.app.model.entity.base_model import BaseModel
from src.app.model.enum.int_enum_type import IntEnumType
from src.app.model.enum.payment_method import PaymentMethod
from src.app.model.enum.payment_status import PaymentStatus


class Payment(BaseModel):
    """Contrato Onda 2 (B1<->B2) — esqueleto commitado pelo orquestrador.

    `reference_type` é string livre por design ("booking" / "group_member"),
    não IntEnumType: é a chave do registro de efeitos em
    `service/payment_service.py` (`register_effect_handler`), preenchida por
    quem possui o domínio referenciado (T-B1 registra "booking" nesta onda;
    T-C registra "group_member" na Onda 3) — acoplar a um enum fechado aqui
    obrigaria este arquivo compartilhado a mudar a cada onda nova.
    """

    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[Optional[PaymentMethod]] = mapped_column(
        IntEnumType(PaymentMethod), nullable=True
    )
    status: Mapped[PaymentStatus] = mapped_column(
        IntEnumType(PaymentStatus),
        server_default=text(str(PaymentStatus.PENDING.value)),
        nullable=False,
    )
    company_payout: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    platform_fee: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gateway_fee: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
