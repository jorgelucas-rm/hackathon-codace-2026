from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text

from src.app.model.entity.base_model import BaseModel
from src.app.model.entity.booking import Booking
from src.app.model.entity.company import Company
from src.app.model.entity.user import User


class Review(BaseModel):
    """Avaliação (modelo-de-dominio.md §9) — Fase F.

    `booking_id`/`user_id` têm `UniqueConstraint` a nível de banco: decisão
    local (T-F) de reforçar a trava "uma avaliação por usuário por
    agendamento" também no schema, além da checagem em
    `ReviewRepository.get_by_booking_and_user` usada pelo service — dupla
    proteção contra corrida (dois requests concorrentes do mesmo usuário
    para o mesmo booking).
    """

    __tablename__ = "review"
    __table_args__ = (
        UniqueConstraint("booking_id", "user_id", name="uq_review_booking_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("company.id"), nullable=False
    )
    booking_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("booking.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    helpful_count: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    company: Mapped[Company] = relationship("Company", backref="reviews")
    booking: Mapped[Booking] = relationship("Booking", backref="reviews")
    user: Mapped[User] = relationship("User")
