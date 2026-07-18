from typing import Type

from src.app.model.entity.notification import Notification
from src.app.repository.base_repository import BaseRepository


class NotificationRepository(BaseRepository[Notification]):

    @property
    def model(self) -> Type[Notification]:
        return Notification

    def get_by_user(
        self, user_id: int, unread_only: bool = False
    ) -> list[Notification]:
        """`GET /api/notifications?apenas_nao_lidas=` — mais recentes
        primeiro."""
        query = self.session.query(Notification).filter(
            Notification.user_id == user_id
        )
        if unread_only:
            query = query.filter(Notification.read.is_(False))
        return query.order_by(Notification.created_at.desc(), Notification.id.desc()).all()

    def mark_read_by_ids(self, user_id: int, ids: list[int]) -> int:
        """Marca como lidas só as notificações informadas que pertençam ao
        usuário — ids de terceiros/inexistentes são ignorados
        silenciosamente (mesmo espírito idempotente do resto do domínio).
        Retorna a quantidade efetivamente marcada."""
        if not ids:
            return 0
        updated = (
            self.session.query(Notification)
            .filter(Notification.user_id == user_id, Notification.id.in_(ids))
            .update({Notification.read: True}, synchronize_session=False)
        )
        self.session.commit()
        return updated

    def mark_all_read(self, user_id: int) -> int:
        updated = (
            self.session.query(Notification)
            .filter(Notification.user_id == user_id, Notification.read.is_(False))
            .update({Notification.read: True}, synchronize_session=False)
        )
        self.session.commit()
        return updated

    def exists_recent(
        self, user_id: int, type: str, reference_type: str, reference_id: int
    ) -> bool:
        """Idempotência simples do job (risco/lembrete): já existe alguma
        notificação desse `type`+`reference_type`+`reference_id` para esse
        usuário? Usado para não notificar duas vezes o mesmo evento — não
        checa janela de tempo (o evento em si — ex. "risco" de um grupo
        específico — só deveria mesmo acontecer uma vez na vida daquele
        grupo/booking)."""
        return (
            self.session.query(Notification.id)
            .filter(
                Notification.user_id == user_id,
                Notification.type == type,
                Notification.reference_type == reference_type,
                Notification.reference_id == reference_id,
            )
            .first()
            is not None
        )

    @property
    def orderable_fields(self) -> dict:
        return {
            "id": Notification.id,
            "created_at": Notification.created_at,
        }

    @property
    def equal_filters(self) -> dict:
        return {
            "user_id": Notification.user_id,
            "type": Notification.type,
            "read": Notification.read,
        }
