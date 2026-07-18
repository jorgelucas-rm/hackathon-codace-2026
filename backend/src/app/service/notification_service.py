from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from src.app.model.dto.notification import NotificationReadDTO
from src.app.model.entity.notification import Notification
from src.app.repository.notification_repository import NotificationRepository


class NotificationService:
    """`Notification` (T-E, Onda 4, modelo-de-dominio.md §10).

    `create(...)` é pensado para ser chamado de DENTRO de outros services
    (booking/group/payment-effects/job), na mesma transação/sessão deles —
    por isso aceita um `session` opcional: se vier, usa um
    `NotificationRepository` construído sobre essa sessão (a do caller,
    dentro de uma transação multi-entidade já aberta); se não vier, usa o
    `notification_repository` já injetado neste service (caso de uso direto,
    ex. testes). Em ambos os casos só faz `add()` (sem commit) — quem chama
    finaliza a transação com o `commit()` da própria operação, mesmo padrão
    do caminho de transação da Onda 0 (`BaseRepository.add`/`commit`)."""

    def __init__(self, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository

    def to_read_dto(self, notification: Notification) -> NotificationReadDTO:
        return NotificationReadDTO.model_validate(notification)

    def create(
        self,
        user_id: int,
        type: str,
        title: str,
        body: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> Notification:
        repository = (
            NotificationRepository(session=session)
            if session is not None
            else self.notification_repository
        )
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        return repository.add(entity=notification)

    def list_by_user(
        self, user_id: int, unread_only: bool = False
    ) -> list[Notification]:
        return self.notification_repository.get_by_user(
            user_id=user_id, unread_only=unread_only
        )

    def mark_read(
        self,
        user_id: int,
        ids: Optional[list[int]] = None,
        all: bool = False,
    ) -> int:
        """`POST /api/notifications/read`. `all=True` tem precedência sobre
        `ids` (mesma regra do DTO). Idempotente: marcar de novo o que já
        estava lido não é erro, só não muda nada a mais."""
        if all:
            return self.notification_repository.mark_all_read(user_id=user_id)
        return self.notification_repository.mark_read_by_ids(
            user_id=user_id, ids=ids or []
        )

    @staticmethod
    def get_service(
        notification_repository: NotificationRepository = Depends(
            NotificationRepository.get_instance()
        ),
    ) -> "NotificationService":
        return NotificationService(notification_repository=notification_repository)
