"""Efeitos de pagamento para `reference_type="group_member"` (Onda 3, T-C).

Mesmo padrão de `service/booking_payment_effects.py` (T-B1, Onda 2):
`PaymentService.confirm(...)` despacha `on_approved`/`on_denied` na mesma
transação/sessão do pagamento e faz um único commit no fim cobrindo Payment +
o efeito — por isso os handlers aqui usam `add()` (sem commit) nos
repositórios envolvidos.

O registro (`register_effect_handler`) roda no import deste módulo (nível de
módulo, no final do arquivo). Para rodar no boot da aplicação, o
orquestrador precisa importar este módulo em algum ponto carregado no
startup — REGISTRAR: `from src.app.service import group_payment_effects  #
noqa: F401` em `service/__init__.py` (arquivo compartilhado, fora do escopo
desta task), ao lado do import já existente de `booking_payment_effects`.
"""

from sqlalchemy.orm import Session

from src.app.model.dto.booking import REASON_PAYMENT_DENIED
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.group_member_status import GroupMemberStatus
from src.app.model.enum.group_status import GroupStatus
from src.app.repository.booking_repository import BookingRepository
from src.app.repository.group_member_repository import GroupMemberRepository
from src.app.repository.group_repository import GroupRepository
from src.app.service.payment_service import register_effect_handler


def on_group_member_approved(reference_id: int, session: Session) -> None:
    """Pagamento da cota aprovado -> `GroupMember.status = CONFIRMED`. Se
    isso lotou o grupo (`CONFIRMED` count == `total_spots`) -> `OpenGroup.
    status = FULL` + `Booking.status = CONFIRMED`
    (backend-api-e-fluxos.md §3.3)."""
    member_repository = GroupMemberRepository(session=session)
    member = member_repository.get_by_pk(pk=reference_id)
    if not member:
        return
    if member.status != GroupMemberStatus.PENDING:
        # Idempotência: já processado (ou membro em outro estado) — nada a
        # fazer, mesma defesa extra de `on_booking_approved`.
        return

    member.status = GroupMemberStatus.CONFIRMED
    member_repository.add(entity=member)

    group_repository = GroupRepository(session=session)
    group = group_repository.get_by_pk(pk=member.group_id)
    if not group:
        return

    if group.status != GroupStatus.OPEN:
        return

    confirmed_count = member_repository.count_confirmed(group.id)
    if confirmed_count >= group.total_spots:
        group.status = GroupStatus.FULL
        group_repository.add(entity=group)

        booking_repository = BookingRepository(session=session)
        booking = booking_repository.get_by_pk(pk=group.booking_id)
        if booking and booking.status == BookingStatus.PENDING:
            booking.status = BookingStatus.CONFIRMED
            booking_repository.add(entity=booking)


def on_group_member_denied(reference_id: int, session: Session) -> None:
    """Pagamento da cota recusado -> `GroupMember.status = LEFT` (cota
    liberada).

    Decisão local (consistente com `backend-api-e-fluxos.md` §3.3: "o
    pagamento pendente é a cota do criador — o grupo só vale se o criador
    pagar, senão tudo expira junto"): se o membro recusado é o **criador**
    do agendamento e o grupo ainda está `OPEN`, cascateia o cancelamento do
    grupo + booking (mesmo efeito de `on_booking_denied` para reserva
    fechada) em vez de deixar um grupo órfão sem criador."""
    member_repository = GroupMemberRepository(session=session)
    member = member_repository.get_by_pk(pk=reference_id)
    if not member:
        return
    if member.status != GroupMemberStatus.PENDING:
        return

    member.status = GroupMemberStatus.LEFT
    member_repository.add(entity=member)

    group_repository = GroupRepository(session=session)
    group = group_repository.get_by_pk(pk=member.group_id)
    if not group:
        return

    booking_repository = BookingRepository(session=session)
    booking = booking_repository.get_by_pk(pk=group.booking_id)

    if (
        booking
        and booking.creator_user_id == member.user_id
        and group.status == GroupStatus.OPEN
    ):
        if booking.status == BookingStatus.PENDING:
            booking.status = BookingStatus.CANCELED
            booking.reason = REASON_PAYMENT_DENIED
            booking_repository.add(entity=booking)

        group.status = GroupStatus.CANCELED
        group_repository.add(entity=group)


register_effect_handler("group_member", on_group_member_approved, on_group_member_denied)
