from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text

from src.app.model.entity.base_model import BaseModel
from src.app.model.entity.user import User


class Notification(BaseModel):
    """Notificação (modelo-de-dominio.md §10) — T-E, Onda 4.

    `type`/`reference_type` são strings livres por design (mesmo padrão de
    `Payment.reference_type` e `Booking.reason`), evitando acoplar este
    arquivo a um enum fechado que mudaria a cada nova onda/evento.

    Lista de `type`s usados nesta task (documentada aqui, é a fonte de
    verdade — ver REGISTRAR no relatório final de T-E):

    - `booking_confirmed`: reserva fechada confirmada (pagamento aprovado).
    - `booking_canceled`: reserva cancelada (pagamento recusado/expirado,
      cancelamento pelo estabelecimento).
    - `group_joined`: alguém entrou no grupo (avisa o criador).
    - `group_left`: alguém saiu do grupo (avisa o criador).
    - `group_full`: grupo completou todas as vagas, jogo confirmado (avisa
      todos os membros confirmados).
    - `game_confirmed`: grupo confirmado pelo job no prazo com o mínimo de
      vagas atingido, sem estar necessariamente cheio (avisa todos os
      membros confirmados) — distinto de `group_full` (que já implica jogo
      confirmado por lotação total).
    - `group_risk`: grupo `OPEN` abaixo do mínimo a menos de
      `GROUP_RISK_HOURS` do prazo de fechamento (job).
    - `group_canceled`: grupo cancelado (prazo vencido sem mínimo,
      cancelamento pelo estabelecimento, ou cota do criador recusada).
    - `reminder`: lembrete de jogo (`Booking` `CONFIRMED` a menos de
      `REMINDER_HOURS` do início) — job.

    `reference_type` acompanha o evento: `"booking"` ou `"group"`.
    """

    __tablename__ = "notification"
    __table_args__ = (
        Index("ix_notification_user_id_read", "user_id", "read"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    read: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User")
