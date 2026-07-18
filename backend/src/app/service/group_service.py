from datetime import date as date_
from datetime import datetime, time, timedelta, timezone
from typing import Optional

from fastapi import Depends

from src.app.model.dto.booking import BookingCreateDTO
from src.app.model.dto.group import (
    GroupJoinResponseDTO,
    GroupLeaveResponseDTO,
    GroupMemberReadDTO,
    GroupPanelSummaryDTO,
    GroupReadDTO,
)
from src.app.model.entity.booking import Booking
from src.app.model.entity.court import Court
from src.app.model.entity.group_member import GroupMember
from src.app.model.entity.open_group import OpenGroup
from src.app.model.entity.payment import Payment
from src.app.model.enum import ErrorCode
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.booking_type import BookingType
from src.app.model.enum.group_leftover_rule import GroupLeftoverRule
from src.app.model.enum.group_member_status import GroupMemberStatus
from src.app.model.enum.group_status import GroupStatus
from src.app.model.enum.group_visibility import GroupVisibility
from src.app.model.enum.payment_status import PaymentStatus
from src.app.repository.booking_repository import BookingRepository
from src.app.repository.group_member_repository import GroupMemberRepository
from src.app.repository.group_repository import GroupRepository
from src.app.repository.notification_repository import NotificationRepository
from src.app.repository.payment_repository import PaymentRepository
from src.app.service.availability_service import (
    _find_opening_hours_for_date,
    _parse_hhmm,
)
from src.app.service.notification_service import NotificationService
from src.app.service.payment_service import PaymentService
from src.environments import REFUND_DEADLINE_HOURS
from src.infra.datetime_utils import local_datetime
from src.infra.exception import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)

# Contrato Onda 3 (T-C<->T-D) — esqueleto commitado pelo orquestrador.
#
# T-C é dono deste arquivo e implementa os corpos abaixo. `__init__`/
# `get_service` foram reescritos para injetar o que a Fase C precisa
# (GroupMemberRepository, BookingRepository, PaymentRepository,
# PaymentService), sem quebrar as duas assinaturas públicas usadas por T-D:
# `get_panel_summary` e `cancel_group`.

# `reason` usado por `process_deadline` quando o mínimo de vagas não é
# atingido no prazo (backend-api-e-fluxos.md §3.4) — valor livre, mesmo
# padrão dos `REASON_*` de `dto/booking.py`.
REASON_GROUP_NOT_FORMED = "deadline_not_met"


class GroupService:

    def __init__(
        self,
        group_repository: GroupRepository,
        group_member_repository: GroupMemberRepository,
        booking_repository: BookingRepository,
        payment_repository: PaymentRepository,
        payment_service: PaymentService,
    ):
        self.group_repository = group_repository
        self.group_member_repository = group_member_repository
        self.booking_repository = booking_repository
        self.payment_repository = payment_repository
        self.payment_service = payment_service

    # ------------------------------------------------------------------
    # Leitura / DTOs
    # ------------------------------------------------------------------

    def get_panel_summary(self, booking_id: int) -> Optional[GroupPanelSummaryDTO]:
        """Usado por T-D (`GET /api/companies/me/schedule`) para embutir os
        dados do grupo num booking `type=GROUP`, e por T-C no slot
        `open_group` da disponibilidade. Retorna `None` se o booking não tem
        grupo associado.

        `filled_spots` = contagem de `GroupMember` com status `CONFIRMED` +
        `PENDING` não expirado (via `payment_service.is_expired` no payment
        do membro) — mesmo critério de "vaga ocupada" de
        `backend-api-e-fluxos.md` §3.3."""
        group = self.group_repository.get_by_booking(booking_id)
        if not group:
            return None

        return GroupPanelSummaryDTO(
            id=group.id,
            status=group.status.name,
            total_spots=group.total_spots,
            min_spots=group.min_spots,
            filled_spots=self._filled_spots(group.id),
            spot_price=group.spot_price,
            visibility=group.visibility.name,
            closing_deadline=group.closing_deadline,
        )

    def get_detail(self, group_id: int) -> GroupReadDTO:
        """`GET /api/groups/{id}` — funciona tanto para `visibility=PUBLIC`
        quanto `visibility=LINK` (acesso direto por id, sem passar pela
        busca pública, que é quem filtra por visibilidade)."""
        group = self.group_repository.get_by_pk(pk=group_id)
        if not group:
            raise NotFoundException(resource="Group", error_code=ErrorCode.NOT_FOUND)
        return self._to_read_dto(group)

    def search_public(
        self,
        sport_id: Optional[int] = None,
        court_id: Optional[int] = None,
        date: Optional[date_] = None,
    ) -> list[GroupReadDTO]:
        """`GET /api/groups` — busca pública (backend-api-e-fluxos.md §2.7):
        só grupos `status=OPEN` + `visibility=PUBLIC` com `closing_deadline`
        futuro. Filtros básicos por `sport_id`/`court_id`/`date` (o doc
        também cita `lat/lng/raio_km` — fora de escopo aqui, mesmo padrão
        de geolocalização de T-A1 em `company`; não implementado nesta
        task). Ordenação default: data/horário do agendamento (mais
        próximos primeiro)."""
        now = datetime.now(timezone.utc)
        groups = self.group_repository.search_public(
            now=now, sport_id=sport_id, court_id=court_id, date=date
        )
        return [self._to_read_dto(group) for group in groups]

    def list_my_groups(self, user_id: int) -> list[GroupReadDTO]:
        """`GET /groups/mine`: grupos onde o usuário é membro ativo — cobre
        tanto o grupo que ele criou quanto os que entrou via
        `POST /api/groups/{id}/join` (que não aparecem em
        `GET /users/me/bookings`, escopado só por `creator_user_id`)."""
        groups = self.group_repository.get_by_member_user(user_id)
        return [self._to_read_dto(group) for group in groups]

    def _to_read_dto(self, group: OpenGroup) -> GroupReadDTO:
        booking = group.booking
        court = booking.court if booking else None
        confirmed_members = self.group_member_repository.get_confirmed_by_group(
            group.id
        )
        return GroupReadDTO(
            id=group.id,
            booking_id=group.booking_id,
            court_id=booking.court_id if booking else 0,
            court_name=court.name if court else None,
            company_id=court.company_id if court else None,
            company_name=(court.company.name if court and court.company else None),
            date=booking.date if booking else date_.min,
            start_time=booking.start_time if booking else time.min,
            end_time=booking.end_time if booking else time.min,
            status=group.status.name,
            total_spots=group.total_spots,
            min_spots=group.min_spots,
            filled_spots=self._filled_spots(group.id),
            spot_price=group.spot_price,
            visibility=group.visibility.name,
            closing_deadline=group.closing_deadline,
            leftover_rule=group.leftover_rule.name,
            members=[self._member_read_dto(m) for m in confirmed_members],
        )

    @staticmethod
    def _member_read_dto(member: GroupMember) -> GroupMemberReadDTO:
        return GroupMemberReadDTO(
            id=member.id,
            user_id=member.user_id,
            user_name=member.user.name if member.user else None,
            user_avatar=member.user.avatar if member.user else None,
            status=member.status.name,
            joined_at=member.joined_at,
        )

    # ------------------------------------------------------------------
    # Notificações (T-E, Onda 4) — instrumentação pontual aditiva, só
    # `notification_service.create(...)`, sem alterar a lógica de estado
    # acima/abaixo. Reaproveita a sessão dos repositórios já injetados
    # (mesma transação — `add()` sem commit extra, mesmo padrão do resto do
    # arquivo).
    # ------------------------------------------------------------------

    def _notify(
        self,
        user_id: int,
        type: str,
        title: str,
        body: str,
        group_id: int,
    ) -> None:
        notification_service = NotificationService(
            notification_repository=NotificationRepository(
                session=self.group_repository.session
            )
        )
        notification_service.create(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            reference_type="group",
            reference_id=group_id,
            session=self.group_repository.session,
        )

    def _filled_spots(self, group_id: int) -> int:
        """`CONFIRMED` + `PENDING` não expirado (TTL do pagamento da cota) —
        mesmo critério usado em `GROUP_FULL`/`get_panel_summary`."""
        active_members = self.group_member_repository.get_active_by_group(group_id)
        count = 0
        for member in active_members:
            if member.status == GroupMemberStatus.CONFIRMED:
                count += 1
                continue
            # PENDING: só conta se o pagamento da cota não expirou (expiração
            # preguiçosa, mesmo padrão de `BookingRepository`/
            # `payment_service.is_expired`).
            payment = member.payment
            if payment is None and member.payment_id:
                payment = self.payment_repository.get_by_pk(pk=member.payment_id)
            if payment is None or not self.payment_service.is_expired(payment):
                count += 1
        return count

    # ------------------------------------------------------------------
    # Criação do grupo (embutida em POST /api/bookings, type=group)
    # ------------------------------------------------------------------

    def create_group_booking(
        self, user_id: int, dto: BookingCreateDTO
    ) -> tuple[Booking, OpenGroup, GroupMember, Payment]:
        """`POST /api/bookings` com `type=group`
        (backend-api-e-fluxos.md §2.6/3.3): cria `Booking(GROUP, PENDING)` +
        `OpenGroup` + `GroupMember` do criador (`PENDING`) + `Payment` da
        cota do criador (`reference_type="group_member"`), tudo numa única
        transação (`add()` em cada repositório, um único `commit()` no
        fim)."""
        if dto.type != "group":
            raise ConflictException(
                message="Only type=group bookings are supported here",
                error_code=ErrorCode.INVALID_STATE,
            )
        if dto.group is None:
            raise BadRequestException(
                error_type="Missing group configuration",
                details="group is required for type=group",
                error_code=ErrorCode.INVALID_GROUP_CONFIG,
            )

        group_dto = dto.group
        self._validate_time_range(dto.date, dto.start_time, dto.end_time)

        # Lock da Court antes de checar sobreposição — mesmo padrão de
        # `BookingService.create_closed_booking`.
        court = self.booking_repository.get_court_for_update(court_id=dto.court_id)
        if not court:
            raise NotFoundException(resource="Court", error_code=ErrorCode.NOT_FOUND)

        if group_dto.total_spots > court.capacity:
            raise BadRequestException(
                error_type="Invalid group configuration",
                details="total_spots must be <= court capacity",
                error_code=ErrorCode.INVALID_GROUP_CONFIG,
            )
        if group_dto.min_spots > group_dto.total_spots:
            raise BadRequestException(
                error_type="Invalid group configuration",
                details="min_spots must be <= total_spots",
                error_code=ErrorCode.INVALID_GROUP_CONFIG,
            )

        game_start = datetime.combine(
            dto.date, dto.start_time, tzinfo=timezone.utc
        )
        closing_deadline = group_dto.closing_deadline
        if closing_deadline.tzinfo is None:
            closing_deadline = closing_deadline.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if closing_deadline <= now or closing_deadline > game_start:
            # Decisão local: prazo de fechamento precisa estar no futuro e
            # não pode ser depois do início do jogo (não faz sentido fechar
            # o grupo depois de o jogo já ter começado).
            raise BadRequestException(
                error_type="Invalid group configuration",
                details="closing_deadline must be in the future and before the game start time",
                error_code=ErrorCode.INVALID_GROUP_CONFIG,
            )

        self._validate_within_opening_hours(
            court, dto.date, dto.start_time, dto.end_time
        )
        self._validate_no_overlap(dto.court_id, dto.date, dto.start_time, dto.end_time)

        duration_hours = self._duration_hours(dto.start_time, dto.end_time)
        total_price = round(court.base_price_hour * duration_hours)
        # Cota arredondada para cima, em centavos (backend-api-e-fluxos.md
        # §2.6): `ceil(total / vagas_totais)`.
        spot_price = -(-total_price // group_dto.total_spots)

        booking = Booking(
            court_id=dto.court_id,
            creator_user_id=user_id,
            date=dto.date,
            start_time=dto.start_time,
            end_time=dto.end_time,
            type=BookingType.GROUP,
            status=BookingStatus.PENDING,
            total_price=total_price,
        )
        booking = self.booking_repository.add(entity=booking)

        group = OpenGroup(
            booking_id=booking.id,
            total_spots=group_dto.total_spots,
            min_spots=group_dto.min_spots,
            spot_price=spot_price,
            visibility=(
                GroupVisibility.PUBLIC
                if group_dto.visibility == "public"
                else GroupVisibility.LINK
            ),
            closing_deadline=group_dto.closing_deadline,
            leftover_rule=(
                GroupLeftoverRule.CREATOR_ABSORBS
                if group_dto.leftover_rule == "creator_absorbs"
                else GroupLeftoverRule.RECALCULATE_QUOTA
            ),
            status=GroupStatus.OPEN,
        )
        group = self.group_repository.add(entity=group)

        member = GroupMember(
            group_id=group.id, user_id=user_id, status=GroupMemberStatus.PENDING
        )
        member = self.group_member_repository.add(entity=member)

        payment = self.payment_service.create_pending(
            reference_type="group_member", reference_id=member.id, amount=spot_price
        )
        member.payment_id = payment.id
        member = self.group_member_repository.add(entity=member)

        self.group_repository.commit()
        return booking, group, member, payment

    # ------------------------------------------------------------------
    # Entrar / sair
    # ------------------------------------------------------------------

    def join(self, group_id: int, user_id: int) -> GroupJoinResponseDTO:
        """`POST /api/groups/{id}/join`: lock do grupo, cria
        `GroupMember(PENDING)` + `Payment` da cota."""
        group = self.group_repository.get_for_update(group_id)
        if not group:
            raise NotFoundException(resource="Group", error_code=ErrorCode.NOT_FOUND)
        if group.status != GroupStatus.OPEN:
            raise ConflictException(
                message="Group is not open for new members",
                error_code=ErrorCode.INVALID_STATE,
            )

        existing = self.group_member_repository.get_active_member(
            group_id=group.id, user_id=user_id
        )
        if existing:
            raise ConflictException(
                message="User is already a member of this group",
                error_code=ErrorCode.ALREADY_MEMBER,
            )

        filled = self._filled_spots(group.id)
        if filled >= group.total_spots:
            raise ConflictException(
                message="Group has no available spots",
                error_code=ErrorCode.GROUP_FULL,
            )

        member = GroupMember(
            group_id=group.id, user_id=user_id, status=GroupMemberStatus.PENDING
        )
        member = self.group_member_repository.add(entity=member)

        payment = self.payment_service.create_pending(
            reference_type="group_member",
            reference_id=member.id,
            amount=group.spot_price,
        )
        member.payment_id = payment.id
        member = self.group_member_repository.add(entity=member)

        self.group_repository.commit()

        return GroupJoinResponseDTO(
            member=self._member_read_dto(member),
            payment=self.payment_service.to_summary_dto(payment),
            group=self.get_panel_summary(group.booking_id),
        )

    def leave(self, group_id: int, user_id: int) -> GroupLeaveResponseDTO:
        """`POST /api/groups/{id}/leave`: reembolso conforme prazo (mesma
        política `REFUND_DEADLINE_HOURS` do booking — decisão: prazo
        contado a partir do início do jogo, igual ao cancelamento de
        reserva fechada), marca membro `LEFT`, reabre a vaga (grupo `FULL`
        volta a `OPEN`)."""
        group = self.group_repository.get_for_update(group_id)
        if not group:
            raise NotFoundException(resource="Group", error_code=ErrorCode.NOT_FOUND)

        member = self.group_member_repository.get_active_member(
            group_id=group.id, user_id=user_id
        )
        if not member:
            raise ConflictException(
                message="User is not an active member of this group",
                error_code=ErrorCode.NOT_GROUP_MEMBER,
            )

        booking = self.booking_repository.get_by_pk(pk=group.booking_id)
        if booking and booking.creator_user_id == user_id:
            # backend-api-e-fluxos.md §2.7: "Criador não sai — cancela o
            # agendamento." (rota de cancelamento de booking, fora deste
            # método).
            raise ConflictException(
                message="Creator cannot leave the group; cancel the booking instead",
                error_code=ErrorCode.INVALID_STATE,
            )

        refunded = False
        payment = member.payment
        if payment is None and member.payment_id:
            payment = self.payment_repository.get_by_pk(pk=member.payment_id)

        if payment and payment.status == PaymentStatus.APPROVED:
            game_start = (
                local_datetime(booking.date, booking.start_time)
                if booking
                else None
            )
            refund_deadline = (
                game_start - timedelta(hours=REFUND_DEADLINE_HOURS)
                if game_start
                else None
            )
            now = datetime.now(timezone.utc)
            if refund_deadline is None or now < refund_deadline:
                self.payment_service.refund(payment_id=payment.id)
                refunded = True

        member.status = GroupMemberStatus.LEFT
        member = self.group_member_repository.add(entity=member)

        if group.status == GroupStatus.FULL:
            group.status = GroupStatus.OPEN
            group = self.group_repository.add(entity=group)

        if booking and booking.creator_user_id is not None:
            # Avisa o criador que alguém saiu (backend-api-e-fluxos.md
            # §3.3: "os membros são notificados").
            self._notify(
                user_id=booking.creator_user_id,
                type="group_left",
                title="Alguém saiu do seu grupo",
                body="Uma vaga foi reaberta no seu grupo.",
                group_id=group.id,
            )

        self.group_repository.commit()

        return GroupLeaveResponseDTO(
            group=self.get_panel_summary(group.booking_id),
            refunded=refunded,
        )

    # ------------------------------------------------------------------
    # Cancelamento / fechamento por prazo
    # ------------------------------------------------------------------

    def cancel_group(self, group_id: int, reason: str, commit: bool = True) -> None:
        """Estorna todas as cotas com pagamento `APPROVED`
        (`payment_service.refund`, via `add()` sem commit adicional), marca
        `OpenGroup.status = CANCELED` + o `Booking` associado como
        `CANCELED` (mesmo `reason`). Todos os membros ativos ficam `LEFT`.

        `commit=False` permite compor dentro de uma transação maior já
        aberta pelo caller; por padrão (`True`) finaliza sozinho."""
        group = self.group_repository.get_by_pk(pk=group_id)
        if not group:
            raise NotFoundException(resource="Group", error_code=ErrorCode.NOT_FOUND)

        members = self.group_member_repository.get_by_group(group.id)
        for member in members:
            if member.status not in (
                GroupMemberStatus.PENDING,
                GroupMemberStatus.CONFIRMED,
            ):
                continue

            payment = member.payment
            if payment is None and member.payment_id:
                payment = self.payment_repository.get_by_pk(pk=member.payment_id)
            if payment and payment.status == PaymentStatus.APPROVED:
                self.payment_service.refund(payment_id=payment.id)

            member.status = GroupMemberStatus.LEFT
            self.group_member_repository.add(entity=member)

            # Notifica todos os membros que tinham cota aprovada/pendente
            # (backend-api-e-fluxos.md §3.4/3.5: "estorna todas as cotas;
            # notifica todos" / "notifica todos").
            self._notify(
                user_id=member.user_id,
                type="group_canceled",
                title="Grupo cancelado",
                body=f"O grupo foi cancelado ({reason}).",
                group_id=group.id,
            )

        if group.status != GroupStatus.CANCELED:
            group.status = GroupStatus.CANCELED
            self.group_repository.add(entity=group)

        booking = self.booking_repository.get_by_pk(pk=group.booking_id)
        if booking and booking.status in (
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED,
        ):
            booking.status = BookingStatus.CANCELED
            booking.reason = reason
            self.booking_repository.add(entity=booking)

        if commit:
            self.group_repository.commit()

    def process_deadline(self, group: OpenGroup) -> None:
        """Chamada futura por um job (Onda 4), idempotente
        (backend-api-e-fluxos.md §3.4): se `min_spots` atingido (`CONFIRMED`
        >= `min_spots`) -> grupo `CONFIRMED` + booking `CONFIRMED`; senão ->
        `cancel_group(group.id, reason="deadline_not_met")`.

        Idempotência: se o grupo já está `CONFIRMED`/`CANCELED`, não faz
        nada (já processado)."""
        if group.status not in (GroupStatus.OPEN, GroupStatus.FULL):
            return

        confirmed_count = self.group_member_repository.count_confirmed(group.id)
        if confirmed_count >= group.min_spots:
            was_full = group.status == GroupStatus.FULL
            group.status = GroupStatus.CONFIRMED
            self.group_repository.add(entity=group)

            booking = self.booking_repository.get_by_pk(pk=group.booking_id)
            if booking and booking.status == BookingStatus.PENDING:
                booking.status = BookingStatus.CONFIRMED
                self.booking_repository.add(entity=booking)

            if not was_full:
                # `game_confirmed`: confirmado pelo job com o mínimo
                # atingido sem lotar (distinto de `group_full`, que já
                # notifica "jogo confirmado" no instante em que a última
                # vaga é preenchida — `group_payment_effects.py`). Evita
                # notificar duas vezes o mesmo evento quando o grupo já
                # tinha sido lotado antes do prazo.
                for confirmed_member in self.group_member_repository.get_confirmed_by_group(
                    group.id
                ):
                    self._notify(
                        user_id=confirmed_member.user_id,
                        type="game_confirmed",
                        title="Jogo confirmado!",
                        body="O grupo atingiu o mínimo de vagas no prazo — o jogo está confirmado.",
                        group_id=group.id,
                    )

            self.group_repository.commit()
        else:
            self.cancel_group(group.id, reason=REASON_GROUP_NOT_FORMED, commit=True)

    # ------------------------------------------------------------------
    # Validações (própria versão da Fase C — não edita `booking_service.py`,
    # reaproveita os métodos públicos de `BookingRepository`, mesmo padrão
    # autorizado para T-D em `booking_admin_service.py`).
    # ------------------------------------------------------------------

    def _validate_time_range(self, date: date_, start_time: time, end_time: time) -> None:
        if start_time >= end_time:
            raise BadRequestException(
                error_type="Invalid booking time range",
                details="start_time must be before end_time",
                error_code=ErrorCode.INVALID_TIME_RANGE,
            )

        start_dt = datetime.combine(date, start_time, tzinfo=timezone.utc)
        if start_dt <= datetime.now(timezone.utc):
            raise BadRequestException(
                error_type="Invalid booking time range",
                details="booking must be scheduled in the future",
                error_code=ErrorCode.INVALID_TIME_RANGE,
            )

    def _validate_within_opening_hours(
        self, court: Court, date: date_, start_time: time, end_time: time
    ) -> None:
        opening_hours = court.company.opening_hours or []
        day_config = _find_opening_hours_for_date(opening_hours, date)
        if (
            not day_config
            or day_config.get("fechado")
            or not day_config.get("abertura")
            or not day_config.get("fechamento")
        ):
            raise BadRequestException(
                error_type="Booking outside opening hours",
                details="Company is closed on this day",
                error_code=ErrorCode.OUTSIDE_OPENING_HOURS,
            )

        opening = _parse_hhmm(day_config["abertura"])
        closing = _parse_hhmm(day_config["fechamento"])
        if start_time < opening or end_time > closing:
            raise BadRequestException(
                error_type="Booking outside opening hours",
                details=f"Company opens {day_config['abertura']}-{day_config['fechamento']} on this day",
                error_code=ErrorCode.OUTSIDE_OPENING_HOURS,
            )

    def _validate_no_overlap(
        self, court_id: int, date: date_, start_time: time, end_time: time
    ) -> None:
        """Sobreposição (backend-api-e-fluxos.md §4.1) contra bookings
        ativos (pendente não expirado, confirmada, bloqueado) do mesmo
        court_id + date. Para bookings `type=GROUP` pendentes, a
        "expiração" equivalente é o grupo não estar mais `OPEN` (o booking
        de grupo não tem `Payment(reference_type="booking")` — a cota do
        criador é quem segura o horário)."""
        active_bookings = self.booking_repository.get_active_by_court_and_date(
            court_id=court_id, date=date
        )
        for existing in active_bookings:
            if existing.status == BookingStatus.PENDING:
                if existing.type == BookingType.GROUP:
                    existing_group = self.group_repository.get_by_booking(existing.id)
                    if existing_group and existing_group.status not in (
                        GroupStatus.OPEN,
                        GroupStatus.FULL,
                    ):
                        continue
                else:
                    payment = self.payment_repository.get_by_reference(
                        reference_type="booking", reference_id=existing.id
                    )
                    if payment and self.payment_service.is_expired(payment):
                        continue

            if start_time < existing.end_time and end_time > existing.start_time:
                raise ConflictException(
                    message="This time slot is no longer available",
                    error_code=ErrorCode.SLOT_UNAVAILABLE,
                )

    @staticmethod
    def _duration_hours(start_time: time, end_time: time) -> float:
        start_dt = datetime.combine(date_.min, start_time)
        end_dt = datetime.combine(date_.min, end_time)
        return (end_dt - start_dt).total_seconds() / 3600

    @staticmethod
    def get_service(
        group_repository: GroupRepository = Depends(GroupRepository.get_instance()),
        group_member_repository: GroupMemberRepository = Depends(
            GroupMemberRepository.get_instance()
        ),
        booking_repository: BookingRepository = Depends(
            BookingRepository.get_instance()
        ),
        payment_repository: PaymentRepository = Depends(
            PaymentRepository.get_instance()
        ),
        payment_service: PaymentService = Depends(PaymentService.get_service),
    ) -> "GroupService":
        return GroupService(
            group_repository=group_repository,
            group_member_repository=group_member_repository,
            booking_repository=booking_repository,
            payment_repository=payment_repository,
            payment_service=payment_service,
        )
