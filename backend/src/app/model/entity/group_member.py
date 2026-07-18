from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text

from src.app.model.entity.base_model import BaseModel
from src.app.model.entity.open_group import OpenGroup
from src.app.model.entity.user import User
from src.app.model.enum.group_member_status import GroupMemberStatus
from src.app.model.enum.int_enum_type import IntEnumType


class GroupMember(BaseModel):
    """Participante do Grupo (modelo-de-dominio.md §7). Contrato Onda 3 —
    esqueleto commitado pelo orquestrador; T-C é dono deste arquivo e pode
    estender à vontade.

    `payment_id` nullable: a cota (`Payment`, `reference_type=
    "group_member"`) é criada *depois* do membro (precisa do `member.id`
    como `reference_id`) — fica `None` só no instante entre os dois
    `add()`, antes do commit único da transação.
    """

    __tablename__ = "group_member"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("open_group.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    payment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("payment.id"), nullable=True
    )
    status: Mapped[GroupMemberStatus] = mapped_column(
        IntEnumType(GroupMemberStatus),
        server_default=text(str(GroupMemberStatus.PENDING.value)),
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    group: Mapped[OpenGroup] = relationship("OpenGroup", backref="members")
    user: Mapped[User] = relationship("User")
