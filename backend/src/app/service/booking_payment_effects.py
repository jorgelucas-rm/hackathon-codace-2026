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
from src.app.service.payment_service import register_effect_handler


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


register_effect_handler("booking", on_booking_approved, on_booking_denied)
