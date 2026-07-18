from datetime import date as date_
from datetime import datetime, time, timedelta, timezone
from typing import Optional

from fastapi import Depends

from src.app.model.dto.booking import (
    REASON_CANCELED_BY_CLIENT,
    REASON_CANCELED_BY_COMPANY,
    BookingCreateDTO,
    BookingReadDTO,
)
from src.app.model.entity.booking import Booking
from src.app.model.entity.court import Court
from src.app.model.entity.payment import Payment
from src.app.model.enum import ErrorCode
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.booking_type import BookingType
from src.app.model.enum.payment_status import PaymentStatus
from src.app.repository.booking_repository import BookingRepository
from src.app.repository.payment_repository import PaymentRepository
from src.app.service.availability_service import (
    _find_opening_hours_for_date,
    _parse_hhmm,
)
from src.app.service.payment_service import PaymentService
from src.environments import REFUND_DEADLINE_HOURS
from src.infra.datetime_utils import local_datetime
from src.infra.exception import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)


class BookingService:
    """`Booking` (T-B1, modelo-de-dominio.md §5). `POST /api/bookings` só
    aceita `type=closed` nesta fase (Onda 2) — `type=group` é gancho para a
    Onda 3 (T-C), levanta `INVALID_STATE`."""

    def __init__(
        self,
        booking_repository: BookingRepository,
        payment_repository: PaymentRepository,
        payment_service: PaymentService,
    ):
        self.booking_repository = booking_repository
        self.payment_repository = payment_repository
        self.payment_service = payment_service

    def to_read_dto(self, booking: Booking) -> BookingReadDTO:
        dto = BookingReadDTO.model_validate(booking)
        court = booking.court
        if court:
            dto.court_name = court.name
            dto.company_name = court.company.name if court.company else None
            dto.sport_names = [s.name for s in court.sports]
        return dto

    def get_by_id(self, booking_id: int) -> Booking:
        booking = self.booking_repository.get_by_pk(pk=booking_id)
        if not booking:
            raise NotFoundException(resource="Booking", error_code=ErrorCode.NOT_FOUND)
        return booking

    def get_detail(
        self,
        booking_id: int,
        user_id: Optional[int] = None,
        company_id: Optional[int] = None,
    ) -> Booking:
        """Autorizado para o criador (`creator_user_id`) ou para a company
        dona da court (via `RequestContext`, resolvido pelo controller)."""
        booking = self.get_by_id(booking_id)

        owned_by_user = user_id is not None and booking.creator_user_id == user_id
        owned_by_company = (
            company_id is not None and booking.court.company_id == company_id
        )
        if not (owned_by_user or owned_by_company):
            raise ForbiddenException(
                message="You do not own this booking",
                error_code=ErrorCode.RESOURCE_NOT_OWNED,
            )
        return booking

    def list_by_user(self, user_id: int, scope: str) -> list[Booking]:
        """`GET /api/users/me/bookings?scope=upcoming|history`. Nesta fase,
        só bookings em que o usuário é o criador (participação em grupo é
        gancho da Onda 3)."""
        bookings = self.booking_repository.get_by_creator(user_id=user_id)
        now = datetime.now(timezone.utc)

        def _is_upcoming(booking: Booking) -> bool:
            if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
                return False
            end_dt = local_datetime(booking.date, booking.end_time)
            return end_dt >= now

        if scope == "history":
            return [b for b in bookings if not _is_upcoming(b)]
        return [b for b in bookings if _is_upcoming(b)]

    def create_closed_booking(
        self, user_id: int, dto: BookingCreateDTO
    ) -> tuple[Booking, Payment]:
        """`POST /api/bookings` (fechada). Transação com lock
        (`SELECT ... FOR UPDATE` na court) + revalidação de sobreposição
        (backend-api-e-fluxos.md §4.1); preço calculado no servidor; cria
        `Booking(PENDING)` + `Payment(PENDING)` numa única transação
        (`add()` + `add()` + um único `commit()` no fim, caminho de
        transação da Onda 0)."""
        if dto.type != "closed":
            raise ConflictException(
                message="Only type=closed bookings are supported in this phase",
                error_code=ErrorCode.INVALID_STATE,
            )

        self._validate_time_range(dto.date, dto.start_time, dto.end_time)

        # Lock da Court antes de checar sobreposição — nenhuma outra
        # transação concorrente consegue criar booking na mesma court até o
        # commit/rollback desta.
        court = self.booking_repository.get_court_for_update(court_id=dto.court_id)
        if not court:
            raise NotFoundException(resource="Court", error_code=ErrorCode.NOT_FOUND)

        self._validate_within_opening_hours(court, dto.date, dto.start_time, dto.end_time)
        self._validate_no_overlap(dto.court_id, dto.date, dto.start_time, dto.end_time)

        duration_hours = self._duration_hours(dto.start_time, dto.end_time)
        total_price = round(court.base_price_hour * duration_hours)

        booking = Booking(
            court_id=dto.court_id,
            creator_user_id=user_id,
            date=dto.date,
            start_time=dto.start_time,
            end_time=dto.end_time,
            type=BookingType.CLOSED,
            status=BookingStatus.PENDING,
            total_price=total_price,
        )
        booking = self.booking_repository.add(entity=booking)

        payment = self.payment_service.create_pending(
            reference_type="booking", reference_id=booking.id, amount=total_price
        )

        self.booking_repository.commit()
        return booking, payment

    def cancel_by_user(self, booking_id: int, user_id: int) -> tuple[Booking, bool]:
        """`POST /api/bookings/{id}/cancel` pelo criador."""
        booking = self.get_by_id(booking_id)
        if booking.creator_user_id != user_id:
            raise ForbiddenException(
                message="You do not own this booking",
                error_code=ErrorCode.RESOURCE_NOT_OWNED,
            )
        return self._cancel(booking, reason=REASON_CANCELED_BY_CLIENT)

    def cancel_by_company(self, booking_id: int, company_id: int) -> tuple[Booking, bool]:
        """Gancho para a Fase D (painel): cancelamento pelo estabelecimento
        (estorno integral sempre, sem checar o prazo — regra distinta da do
        cliente). Não exposto por rota nesta onda."""
        booking = self.get_by_id(booking_id)
        if booking.court.company_id != company_id:
            raise ForbiddenException(
                message="You do not own this booking",
                error_code=ErrorCode.RESOURCE_NOT_OWNED,
            )
        return self._cancel(
            booking,
            reason=REASON_CANCELED_BY_COMPANY,
            force_refund=True,
            allow_completed=True,
        )

    def _cancel(
        self,
        booking: Booking,
        reason: str,
        force_refund: bool = False,
        allow_completed: bool = False,
    ) -> tuple[Booking, bool]:
        """Política de reembolso (backend-api-e-fluxos.md §3.5): até
        `REFUND_DEADLINE_HOURS` antes do jogo -> estorno integral; depois ->
        cancela sem reembolso (não é erro, só informativo -
        `BOOKING_NOT_REFUNDABLE` não bloqueia a ação).

        `allow_completed`: o estabelecimento (dono da quadra) pode cancelar
        também reservas já `COMPLETED` — o job de expiração marca como
        `COMPLETED` toda `CONFIRMED` cujo horário passou, então sem isso o
        painel não conseguiria cancelar/estornar reservas do dia já vencidas.
        O cancelamento pelo cliente segue restrito a `PENDING`/`CONFIRMED`."""
        cancelable = [BookingStatus.PENDING, BookingStatus.CONFIRMED]
        if allow_completed:
            cancelable.append(BookingStatus.COMPLETED)

        if booking.status not in cancelable:
            raise ConflictException(
                message=f"Booking cannot be canceled from status {booking.status.name}",
                error_code=ErrorCode.INVALID_STATE,
            )

        game_start = local_datetime(booking.date, booking.start_time)
        refund_deadline = game_start - timedelta(hours=REFUND_DEADLINE_HOURS)
        now = datetime.now(timezone.utc)

        refunded = False
        payment = self.payment_repository.get_by_reference(
            reference_type="booking", reference_id=booking.id
        )
        if payment and payment.status == PaymentStatus.APPROVED and (
            force_refund or now < refund_deadline
        ):
            self.payment_service.refund(payment_id=payment.id)
            refunded = True

        booking.status = BookingStatus.CANCELED
        booking.reason = reason
        booking = self.booking_repository.add(entity=booking)

        self.booking_repository.commit()
        return booking, refunded

    def _validate_time_range(self, date: date_, start_time: time, end_time: time) -> None:
        if start_time >= end_time:
            raise BadRequestException(
                error_type="Invalid booking time range",
                details="start_time must be before end_time",
                error_code=ErrorCode.INVALID_TIME_RANGE,
            )

        start_dt = local_datetime(date, start_time)
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
        """Sobreposição (backend-api-e-fluxos.md §4.1):
        `start_time < existing.end_time AND end_time > existing.start_time`
        contra bookings ativos (pendente não expirado, confirmada,
        bloqueado) do mesmo court_id + date."""
        active_bookings = self.booking_repository.get_active_by_court_and_date(
            court_id=court_id, date=date
        )
        for existing in active_bookings:
            if existing.status == BookingStatus.PENDING:
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
        booking_repository: BookingRepository = Depends(
            BookingRepository.get_instance()
        ),
        payment_repository: PaymentRepository = Depends(
            PaymentRepository.get_instance()
        ),
        payment_service: PaymentService = Depends(PaymentService.get_service),
    ) -> "BookingService":
        return BookingService(
            booking_repository=booking_repository,
            payment_repository=payment_repository,
            payment_service=payment_service,
        )
