from datetime import date as date_, datetime, time
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text

from src.app.model.entity.base_model import BaseModel
from src.app.model.entity.court import Court
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.booking_type import BookingType
from src.app.model.enum.int_enum_type import IntEnumType


class Booking(BaseModel):
    """Agendamento (modelo-de-dominio.md §5) — coração transacional da Onda 2.

    `creator_user_id`/`creator_company_id` são mutuamente "opcionais": uma
    reserva feita pelo app tem `creator_user_id`; um bloqueio/reserva manual
    (Fase D, fora do escopo desta onda) tem `creator_company_id`. Nenhuma
    FK apontando para as duas ao mesmo tempo é reforçada aqui — é regra de
    serviço, não de schema.
    """

    __tablename__ = "booking"
    __table_args__ = (
        # Índice composto: toda checagem de sobreposição e a rota de
        # disponibilidade filtram por court_id + date.
        Index("ix_booking_court_id_date", "court_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    court_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("court.id"), nullable=False
    )
    creator_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=True
    )
    creator_company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("company.id"), nullable=True
    )
    date: Mapped[date_] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    type: Mapped[BookingType] = mapped_column(
        IntEnumType(BookingType),
        server_default=text(str(BookingType.CLOSED.value)),
        nullable=False,
    )
    status: Mapped[BookingStatus] = mapped_column(
        IntEnumType(BookingStatus),
        server_default=text(str(BookingStatus.PENDING.value)),
        nullable=False,
    )
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)
    # Reserva manual (Fase D) — fora do escopo desta onda, mas as colunas já
    # entram na migração para não exigir outra revisão Alembic depois.
    customer_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    court: Mapped[Court] = relationship("Court", backref="bookings")
