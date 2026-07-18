"""Efeitos de pagamento para `reference_type="booking"` (contrato Onda 2).

`PaymentService.confirm(...)` despacha `on_approved`/`on_denied` na mesma
transação/sessão do pagamento e faz um único commit no fim cobrindo
Payment + o efeito — por isso os handlers aqui usam `BookingRepository.add()`
(sem commit).

O registro (`register_effect_handler`) roda no import deste módulo (nível de
módulo, no final do arquivo). Para rodar no boot da aplicação, o
orquestrador precisa importar este módulo em algum ponto carregado no
startup — REGISTRAR: `from src.app.service import booking_payment_effects  #
noqa: F401` em `service/__init__.py` (arquivo compartilhado, fora do escopo
desta task).
"""

from sqlalchemy.orm import Session

from src.app.model.dto.booking import REASON_PAYMENT_DENIED
from src.app.model.enum.booking_status import BookingStatus
from src.app.repository.booking_repository import BookingRepository
from src.app.repository.notification_repository import NotificationRepository
from src.app.service.notification_service import NotificationService
from src.app.service.payment_service import register_effect_handler

# T-E (Onda 4): instrumentação pontual aditiva — só chamadas a
# `notification_service.create(...)`, sem mudar a lógica de transição
# existente. `type="booking_confirmed"`/`"booking_canceled"`,
# `reference_type="booking"`. Ponto escolhido: aqui (não em
# `booking_service.py`, fora do escopo desta task) é o único lugar que
# cobre tanto a aprovação de pagamento quanto a recusa/expiração via TTL
# (o job da Onda 4 também reaproveita `PaymentService.confirm`, que
# despacha para estes mesmos handlers — cobre o caso de TTL vencido sem
# precisar de instrumentação duplicada no job).


def on_booking_approved(reference_id: int, session: Session) -> None:
    """Pagamento aprovado -> `Booking.status = CONFIRMED`."""
    repository = BookingRepository(session=session)
    booking = repository.get_by_pk(pk=reference_id)
    if not booking:
        return
    if booking.status != BookingStatus.PENDING:
        # Idempotência: já processado (ou booking em outro estado) — nada a
        # fazer. `PaymentService.confirm` já é idempotente por si só, isto é
        # defesa extra caso o efeito seja invocado fora desse caminho.
        return

    booking.status = BookingStatus.CONFIRMED
    repository.add(entity=booking)

    if booking.creator_user_id is not None:
        notification_service = NotificationService(
            notification_repository=NotificationRepository(session=session)
        )
        notification_service.create(
            user_id=booking.creator_user_id,
            type="booking_confirmed",
            title="Reserva confirmada",
            body="Seu pagamento foi aprovado e a reserva está confirmada.",
            reference_type="booking",
            reference_id=booking.id,
            session=session,
        )


def on_booking_denied(reference_id: int, session: Session) -> None:
    """Pagamento recusado -> `Booking.status = CANCELED`,
    `reason=payment_denied`."""
    repository = BookingRepository(session=session)
    booking = repository.get_by_pk(pk=reference_id)
    if not booking:
        return
    if booking.status != BookingStatus.PENDING:
        return

    booking.status = BookingStatus.CANCELED
    booking.reason = REASON_PAYMENT_DENIED
    repository.add(entity=booking)

    if booking.creator_user_id is not None:
        notification_service = NotificationService(
            notification_repository=NotificationRepository(session=session)
        )
        notification_service.create(
            user_id=booking.creator_user_id,
            type="booking_canceled",
            title="Reserva cancelada",
            body="Seu pagamento foi recusado (ou expirou) e a reserva foi cancelada.",
            reference_type="booking",
            reference_id=booking.id,
            session=session,
        )


register_effect_handler("booking", on_booking_approved, on_booking_denied)
