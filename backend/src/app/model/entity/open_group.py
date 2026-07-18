from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text

from src.app.model.entity.base_model import BaseModel
from src.app.model.entity.booking import Booking
from src.app.model.enum.group_leftover_rule import GroupLeftoverRule
from src.app.model.enum.group_status import GroupStatus
from src.app.model.enum.group_visibility import GroupVisibility
from src.app.model.enum.int_enum_type import IntEnumType


class OpenGroup(BaseModel):
    """Grupo Aberto (modelo-de-dominio.md §6) — 1:1 com um `Booking`
    (`type=GROUP`). Contrato Onda 3 (T-C<->T-D) — esqueleto commitado pelo
    orquestrador; T-C é dono deste arquivo e pode estender à vontade."""

    __tablename__ = "open_group"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("booking.id"), nullable=False, unique=True
    )
    total_spots: Mapped[int] = mapped_column(Integer, nullable=False)
    min_spots: Mapped[int] = mapped_column(Integer, nullable=False)
    spot_price: Mapped[int] = mapped_column(Integer, nullable=False)
    visibility: Mapped[GroupVisibility] = mapped_column(
        IntEnumType(GroupVisibility),
        server_default=text(str(GroupVisibility.PUBLIC.value)),
        nullable=False,
    )
    closing_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    leftover_rule: Mapped[GroupLeftoverRule] = mapped_column(
        IntEnumType(GroupLeftoverRule),
        server_default=text(str(GroupLeftoverRule.CREATOR_ABSORBS.value)),
        nullable=False,
    )
    status: Mapped[GroupStatus] = mapped_column(
        IntEnumType(GroupStatus),
        server_default=text(str(GroupStatus.OPEN.value)),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    booking: Mapped[Booking] = relationship(
        "Booking", backref="open_group", uselist=False
    )
