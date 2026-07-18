"""Job de manutenção assíncrono (T-E, Onda 4, `backend-api-e-fluxos.md`
§3.4/4.4).

Um único pacote `jobs/` (novo, propriedade de T-E) com uma função principal
`process_pending(session_maker)` que roda, numa única passada, os cinco
passos descritos no doc de API — cada um idempotente (rodar duas vezes
seguidas não duplica efeito nem quebra):

1. Expira `Booking` `PENDING` com `Payment` `PENDING` vencido (TTL) —
   cancela o booking e o pagamento.
2. Expira cotas de grupo (`GroupMember` `PENDING` com `Payment` vencido) de
   forma equivalente.
3. Fecha grupos por prazo (`GroupService.process_deadline`).
4. Marca `Booking` `CONFIRMED` cujo horário já passou como `COMPLETED`.
5. Notifica risco de cancelamento e lembrete de jogo.

Decisão de design da assinatura: `process_pending(session_maker)` recebe a
`sessionmaker` (não uma `Session` já aberta) porque abre e fecha a própria
sessão a cada passada — o job roda fora do ciclo de vida de uma requisição
HTTP (sem `Depends(get_session)`), então ele é quem monta e desmonta a
transação. Cada um dos 5 passos comita a própria unidade de trabalho antes
de passar para o próximo (nenhuma falha num passo deveria impedir os
seguintes) — por isso cada `_step_*` abre/fecha sua fatia de trabalho via
`add()`+`commit()`, no mesmo padrão de transação do resto do domínio.

**Status de pagamento expirado**: `enum/payment_status.py` (arquivo
compartilhado, fora do escopo desta task) só tem `PENDING/APPROVED/DENIED/
REFUNDED` — sem `EXPIRED`. Em vez de propor um valor novo num arquivo
proibido, a expiração por TTL é tratada como uma recusa
(`PaymentService.confirm(payment_id, result="denied")`): reaproveita a
máquina de estados e os efeitos em cadeia já existentes e testados
(`booking_payment_effects.on_booking_denied` /
`group_payment_effects.on_group_member_denied`), inclusive as notificações
que eles já disparam (`booking_canceled`/`group_canceled`) — nenhuma
notificação extra é necessária nos passos 1/2 deste job por causa disso.

**Idempotência de risco/lembrete** (passo 5): antes de criar a notificação,
checa `NotificationRepository.exists_recent(user_id, type, reference_type,
reference_id)` — já existe alguma notificação desse tipo para essa
referência? Se sim, não notifica de novo. Isso é suficiente porque o evento
("grupo X está em risco", "jogo Y está próximo") só deveria mesmo disparar
uma vez na vida daquele grupo/booking (não há janela de tempo recorrente no
MVP) — trade-off documentado: se por algum motivo o job precisasse avisar
de novo (ex. o usuário quisesse lembrete repetido), essa checagem
impediria; aceito como limitação do MVP.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session, sessionmaker

from src.app.model.entity.booking import Booking
from src.app.model.entity.group_member import GroupMember
from src.app.model.entity.open_group import OpenGroup
from src.app.model.entity.payment import Payment
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.booking_type import BookingType
from src.app.model.enum.group_member_status import GroupMemberStatus
from src.app.model.enum.group_status import GroupStatus
from src.app.model.enum.payment_status import PaymentStatus
from src.app.adapter import MinioAdapter
from src.app.repository.booking_repository import BookingRepository
from src.app.repository.group_member_repository import GroupMemberRepository
from src.app.repository.group_repository import GroupRepository
from src.app.repository.notification_repository import NotificationRepository
from src.app.repository.payment_repository import PaymentRepository
from src.app.service.group_service import GroupService
from src.app.service.notification_service import NotificationService
from src.app.service.payment_service import PaymentService
from src.environments import GROUP_RISK_HOURS, REMINDER_HOURS
from src.infra.storage import get_minio_client, get_minio_presign_client

logger = logging.getLogger("app.jobs.notification_job")


def _build(session: Session):
    """Monta os repositórios/services usados pelo job sobre uma única
    `Session`, no mesmo padrão de injeção manual usado pelos handlers de
    efeito de pagamento (`booking_payment_effects.py`/
    `group_payment_effects.py`)."""
    booking_repository = BookingRepository(session=session)
    payment_repository = PaymentRepository(session=session)
    group_repository = GroupRepository(session=session)
    group_member_repository = GroupMemberRepository(session=session)
    notification_repository = NotificationRepository(session=session)
    payment_service = PaymentService(payment_repository=payment_repository)
    minio_adapter = MinioAdapter(
        minio_client=get_minio_client(), minio_presign_client=get_minio_presign_client()
    )
    group_service = GroupService(
        group_repository=group_repository,
        group_member_repository=group_member_repository,
        booking_repository=booking_repository,
        payment_repository=payment_repository,
        payment_service=payment_service,
        minio_adapter=minio_adapter,
    )
    notification_service = NotificationService(
        notification_repository=notification_repository
    )
    return {
        "booking_repository": booking_repository,
        "payment_repository": payment_repository,
        "group_repository": group_repository,
        "group_member_repository": group_member_repository,
        "notification_repository": notification_repository,
        "payment_service": payment_service,
        "group_service": group_service,
        "notification_service": notification_service,
    }


def _step_expire_pending_bookings(deps: dict) -> None:
    """1. `Booking` `PENDING` com `Payment(reference_type="booking")`
    `PENDING` vencido (TTL) -> `payment_service.confirm(..., "denied")`
    (cancela o booking em cadeia via `on_booking_denied`, idempotente:
    `confirm` só age sobre `PENDING`)."""
    payment_service = deps["payment_service"]
    payment_repository = deps["payment_repository"]
    pending_payments = (
        payment_repository.session.query(Payment)
        .filter(
            Payment.reference_type == "booking",
            Payment.status == PaymentStatus.PENDING,
        )
        .all()
    )
    for payment in pending_payments:
        if payment_service.is_expired(payment):
            payment_service.confirm(payment_id=payment.id, result="denied")


def _step_expire_pending_group_members(deps: dict) -> None:
    """2. Equivalente ao passo 1 para cotas de grupo
    (`reference_type="group_member"`)."""
    payment_service = deps["payment_service"]
    payment_repository = deps["payment_repository"]
    pending_payments = (
        payment_repository.session.query(Payment)
        .filter(
            Payment.reference_type == "group_member",
            Payment.status == PaymentStatus.PENDING,
        )
        .all()
    )
    for payment in pending_payments:
        if payment_service.is_expired(payment):
            payment_service.confirm(payment_id=payment.id, result="denied")


def _step_process_group_deadlines(deps: dict) -> None:
    """3. `OpenGroup` `OPEN`/`FULL` com `closing_deadline` vencido ->
    `GroupService.process_deadline(group)` (já idempotente por si só —
    reconfere `group.status` antes de agir)."""
    group_repository = deps["group_repository"]
    group_service = deps["group_service"]
    now = datetime.now(timezone.utc)
    groups = (
        group_repository.session.query(OpenGroup)
        .filter(
            OpenGroup.status.in_([GroupStatus.OPEN, GroupStatus.FULL]),
            OpenGroup.closing_deadline <= now,
        )
        .all()
    )
    for group in groups:
        group_service.process_deadline(group)


def _step_complete_past_bookings(deps: dict) -> None:
    """4. `Booking` `CONFIRMED` cujo horário (`date`+`end_time`) já passou
    -> `COMPLETED`. Idempotente: só atua sobre `CONFIRMED`, roda de novo
    sem efeito sobre quem já virou `COMPLETED`."""
    booking_repository = deps["booking_repository"]
    now = datetime.now(timezone.utc)
    confirmed_bookings = (
        booking_repository.session.query(Booking)
        .filter(Booking.status == BookingStatus.CONFIRMED)
        .all()
    )
    changed = False
    for booking in confirmed_bookings:
        end_dt = datetime.combine(booking.date, booking.end_time, tzinfo=timezone.utc)
        if end_dt <= now:
            booking.status = BookingStatus.COMPLETED
            booking_repository.add(entity=booking)
            changed = True
    if changed:
        booking_repository.commit()


def _step_notify_risk_and_reminders(deps: dict) -> None:
    """5. Risco de cancelamento (grupo `OPEN` abaixo do `min_spots` a menos
    de `GROUP_RISK_HOURS` do `closing_deadline`, ainda não vencido — isso já
    foi tratado no passo 3) e lembrete de jogo (`Booking` `CONFIRMED` a
    menos de `REMINDER_HOURS` do início). Idempotência via
    `NotificationRepository.exists_recent` (ver docstring do módulo)."""
    group_repository = deps["group_repository"]
    group_member_repository = deps["group_member_repository"]
    booking_repository = deps["booking_repository"]
    notification_repository = deps["notification_repository"]
    notification_service = deps["notification_service"]
    session = group_repository.session
    now = datetime.now(timezone.utc)

    # --- risco de cancelamento ---
    risk_deadline = now + timedelta(hours=GROUP_RISK_HOURS)
    at_risk_groups = (
        session.query(OpenGroup)
        .filter(
            OpenGroup.status == GroupStatus.OPEN,
            OpenGroup.closing_deadline > now,
            OpenGroup.closing_deadline <= risk_deadline,
        )
        .all()
    )
    for group in at_risk_groups:
        confirmed_count = group_member_repository.count_confirmed(group.id)
        if confirmed_count >= group.min_spots:
            continue
        for member in group_member_repository.get_confirmed_by_group(group.id):
            if notification_repository.exists_recent(
                user_id=member.user_id,
                type="group_risk",
                reference_type="group",
                reference_id=group.id,
            ):
                continue
            notification_service.create(
                user_id=member.user_id,
                type="group_risk",
                title="Grupo em risco de cancelamento",
                body=(
                    f"Faltam menos de {GROUP_RISK_HOURS}h para o prazo e o "
                    "grupo ainda não atingiu o mínimo de vagas."
                ),
                reference_type="group",
                reference_id=group.id,
                session=session,
            )
    session.commit()

    # --- lembrete de jogo ---
    reminder_deadline = now + timedelta(hours=REMINDER_HOURS)
    confirmed_bookings = (
        session.query(Booking).filter(Booking.status == BookingStatus.CONFIRMED).all()
    )
    for booking in confirmed_bookings:
        start_dt = datetime.combine(booking.date, booking.start_time, tzinfo=timezone.utc)
        if not (now < start_dt <= reminder_deadline):
            continue

        recipients: set[int] = set()
        if booking.creator_user_id is not None:
            recipients.add(booking.creator_user_id)
        if booking.type == BookingType.GROUP:
            group = group_repository.get_by_booking(booking.id)
            if group:
                for member in group_member_repository.get_confirmed_by_group(group.id):
                    recipients.add(member.user_id)

        for user_id in recipients:
            if notification_repository.exists_recent(
                user_id=user_id,
                type="reminder",
                reference_type="booking",
                reference_id=booking.id,
            ):
                continue
            notification_service.create(
                user_id=user_id,
                type="reminder",
                title="Seu jogo está chegando",
                body="Seu jogo confirmado começa em breve.",
                reference_type="booking",
                reference_id=booking.id,
                session=session,
            )
    session.commit()


async def process_pending(session_maker: sessionmaker) -> None:
    """Uma passada completa dos 5 passos (backend-api-e-fluxos.md §4.4),
    cada um numa sub-transação própria — uma falha num passo não impede os
    seguintes de rodar na próxima chamada (o loop chama isto a cada 60s)."""
    session = session_maker()
    try:
        deps = _build(session)
        steps = (
            ("expire_pending_bookings", _step_expire_pending_bookings),
            ("expire_pending_group_members", _step_expire_pending_group_members),
            ("process_group_deadlines", _step_process_group_deadlines),
            ("complete_past_bookings", _step_complete_past_bookings),
            ("notify_risk_and_reminders", _step_notify_risk_and_reminders),
        )
        for name, step in steps:
            try:
                step(deps)
            except Exception:
                session.rollback()
                logger.exception("notification_job: step %s failed", name)
    finally:
        session.close()


async def run_loop(session_maker: sessionmaker, interval_seconds: int = 60) -> None:
    """Loop assíncrono único (backend-api-e-fluxos.md §4.4): chama
    `process_pending` a cada `interval_seconds` (default 60s). Uma exceção
    não tratada dentro de `process_pending` (ex. erro de conexão com o
    banco) não derruba o loop — logada e a próxima iteração roda normal."""
    while True:
        try:
            await process_pending(session_maker)
        except Exception:
            logger.exception("notification_job: process_pending failed")
        await asyncio.sleep(interval_seconds)
