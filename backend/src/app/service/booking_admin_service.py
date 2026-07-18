from datetime import date as date_, datetime, time
from typing import Optional

from fastapi import Depends

from src.app.model.dto.booking import BookingReadDTO
from src.app.model.dto.booking_admin import BlockCreateDTO, ManualBookingCreateDTO
from src.app.model.entity.booking import Booking
from src.app.model.entity.court import Court
from src.app.model.enum import ErrorCode
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.booking_type import BookingType
from src.app.repository.booking_repository import BookingRepository
from src.app.repository.notification_repository import NotificationRepository
from src.app.repository.payment_repository import PaymentRepository
from src.app.service.availability_service import (
    _find_opening_hours_for_date,
    _parse_hhmm,
)
from src.app.service.booking_service import BookingService
from src.app.service.group_service import GroupService
from src.app.service.notification_service import NotificationService
from src.app.service.payment_service import PaymentService
from src.infra.exception import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)

# T-D (Fase D, Onda 3) — bloqueios, reserva manual e cancelamento pelo
# estabelecimento. Arquivo próprio, não é `booking_service.py` (T-B1, não
# editado por esta task): a validação de exclusividade (lock + overlap) é
# reimplementada aqui via os métodos públicos de `BookingRepository`
# (`get_court_for_update`, `get_active_by_court_and_date`), no mesmo espírito
# de `BookingService.create_closed_booking`/`_validate_no_overlap`.
#
# Reason livre usado por este módulo para desbloqueio (não um ErrorCode, é
# `Booking.reason`, mesmo padrão de `dto/booking.py` REASON_*).
REASON_BLOCK_REMOVED = "block_removed"


class BookingAdminService:
    """Bloqueios (`POST/DELETE .../blocks`), reserva manual (`POST
    /api/companies/me/manual-bookings`) e cancelamento pelo estabelecimento
    (`POST /api/bookings/{id}/cancel-by-company`, cascateando para o grupo
    quando `booking.type == GROUP`)."""

    def __init__(
        self,
        booking_repository: BookingRepository,
        payment_repository: PaymentRepository,
        payment_service: PaymentService,
        booking_service: BookingService,
        group_service: GroupService,
    ):
        self.booking_repository = booking_repository
        self.payment_repository = payment_repository
        self.payment_service = payment_service
        self.booking_service = booking_service
        self.group_service = group_service

    def to_read_dto(self, booking: Booking) -> BookingReadDTO:
        return BookingReadDTO.model_validate(booking)

    def create_block(
        self, company_id: int, court_id: int, dto: BlockCreateDTO
    ) -> Booking:
        """`POST /api/courts/{id}/blocks`. Bloqueio da própria company —
        `creator_company_id=company_id`, sem `creator_user_id`. Mesma
        exclusividade (lock na court + overlap) do fluxo normal de booking."""
        self._validate_time_range(dto.start_time, dto.end_time)

        court = self.booking_repository.get_court_for_update(court_id=court_id)
        if not court:
            raise NotFoundException(resource="Court", error_code=ErrorCode.NOT_FOUND)
        if court.company_id != company_id:
            raise ForbiddenException(
                message="You do not own this court",
                error_code=ErrorCode.RESOURCE_NOT_OWNED,
            )

        self._validate_no_overlap(court_id, dto.date, dto.start_time, dto.end_time)

        booking = Booking(
            court_id=court_id,
            creator_company_id=company_id,
            date=dto.date,
            start_time=dto.start_time,
            end_time=dto.end_time,
            type=BookingType.CLOSED,
            status=BookingStatus.BLOCKED,
            reason=dto.reason,
            total_price=0,
        )
        booking = self.booking_repository.add(entity=booking)
        self.booking_repository.commit()
        return booking

    def remove_block(self, company_id: int, booking_id: int) -> Booking:
        """`DELETE /api/bookings/{id}/block`. Não apaga a linha (mantém
        histórico, mesmo padrão de cancelamento do resto do domínio) —
        marca `CANCELED` e libera o horário (deixa de contar como ativo em
        `get_active_by_court_and_date`)."""
        booking = self.booking_repository.get_by_pk(pk=booking_id)
        if not booking:
            raise NotFoundException(resource="Booking", error_code=ErrorCode.NOT_FOUND)
        if booking.court.company_id != company_id:
            raise ForbiddenException(
                message="You do not own this booking",
                error_code=ErrorCode.RESOURCE_NOT_OWNED,
            )
        if booking.status != BookingStatus.BLOCKED:
            raise ConflictException(
                message=f"Booking is not a block (status={booking.status.name})",
                error_code=ErrorCode.INVALID_STATE,
            )

        booking.status = BookingStatus.CANCELED
        booking.reason = REASON_BLOCK_REMOVED
        booking = self.booking_repository.add(entity=booking)
        self.booking_repository.commit()
        return booking

    def create_manual_booking(
        self, company_id: int, dto: ManualBookingCreateDTO
    ) -> Booking:
        """`POST /api/companies/me/manual-bookings` — reserva de balcão:
        nasce `CONFIRMED` direto (sem `Payment`, fora do simulador de
        gateway por decisão do doc), preço no servidor
        (`court.base_price_hour * duration_hours`), mesma exclusividade do
        fluxo normal."""
        self._validate_time_range(dto.start_time, dto.end_time)

        court = self.booking_repository.get_court_for_update(court_id=dto.court_id)
        if not court:
            raise NotFoundException(resource="Court", error_code=ErrorCode.NOT_FOUND)
        if court.company_id != company_id:
            raise ForbiddenException(
                message="You do not own this court",
                error_code=ErrorCode.RESOURCE_NOT_OWNED,
            )

        self._validate_within_opening_hours(
            court, dto.date, dto.start_time, dto.end_time
        )
        self._validate_no_overlap(
            dto.court_id, dto.date, dto.start_time, dto.end_time
        )

        duration_hours = self._duration_hours(dto.start_time, dto.end_time)
        total_price = round(court.base_price_hour * duration_hours)

        booking = Booking(
            court_id=dto.court_id,
            creator_company_id=company_id,
            date=dto.date,
            start_time=dto.start_time,
            end_time=dto.end_time,
            type=BookingType.CLOSED,
            status=BookingStatus.CONFIRMED,
            total_price=total_price,
            customer_name=dto.customer_name,
            customer_phone=dto.customer_phone,
        )
        booking = self.booking_repository.add(entity=booking)
        self.booking_repository.commit()
        return booking

    def cancel_by_company(
        self, booking_id: int, company_id: int
    ) -> tuple[Booking, bool, bool]:
        """Cancelamento pelo estabelecimento (`POST
        /api/bookings/{id}/cancel-by-company`). Reaproveita
        `BookingService.cancel_by_company` (Onda 2, já existe — só chama,
        não edita) e cascateia para o grupo quando `booking.type == GROUP`:
        resolve `group_id` via `group_service.get_panel_summary(booking.id)`
        **antes** de cancelar o booking (o summary é resolvido a partir do
        booking, então ler antes evita qualquer ordem de dependência com o
        estado pós-cancelamento), depois chama
        `group_service.cancel_group(group_id, reason="canceled_by_company")`
        como operação independente (`commit=True`, default do contrato).

        Retorna `(booking, refunded, group_canceled)` — `refunded` é do
        próprio booking (o estorno do booking "container" do grupo, se
        houver `Payment` associado a ele diretamente); `group_canceled`
        indica se a cascata do grupo rodou."""
        booking = self.booking_service.get_by_id(booking_id)

        group_id: Optional[int] = None
        if booking.type == BookingType.GROUP:
            summary = self.group_service.get_panel_summary(booking_id=booking.id)
            if summary:
                group_id = summary.id

        booking, refunded = self.booking_service.cancel_by_company(
            booking_id=booking_id, company_id=company_id
        )

        group_canceled = False
        if group_id is not None:
            # Cascata: `GroupService.cancel_group` já notifica todos os
            # membros afetados (`group_canceled`, `service/group_service.py`)
            # — não duplica aqui com uma notificação de booking.
            self.group_service.cancel_group(
                group_id=group_id, reason="canceled_by_company", commit=True
            )
            group_canceled = True
        elif booking.creator_user_id is not None:
            # T-E (Onda 4): sem grupo envolvido — notifica o criador
            # diretamente aqui (booking "solo" cancelado pelo
            # estabelecimento, backend-api-e-fluxos.md §3.5).
            notification_service = NotificationService(
                notification_repository=NotificationRepository(
                    session=self.booking_repository.session
                )
            )
            notification_service.create(
                user_id=booking.creator_user_id,
                type="booking_canceled",
                title="Reserva cancelada pelo estabelecimento",
                body="O estabelecimento cancelou sua reserva e o valor foi estornado.",
                reference_type="booking",
                reference_id=booking.id,
                session=self.booking_repository.session,
            )
            self.booking_repository.session.commit()

        return booking, refunded, group_canceled

    def _validate_time_range(self, start_time: time, end_time: time) -> None:
        if start_time >= end_time:
            raise BadRequestException(
                error_type="Invalid time range",
                details="start_time must be before end_time",
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
                details=(
                    f"Company opens {day_config['abertura']}-"
                    f"{day_config['fechamento']} on this day"
                ),
                error_code=ErrorCode.OUTSIDE_OPENING_HOURS,
            )

    def _validate_no_overlap(
        self, court_id: int, date: date_, start_time: time, end_time: time
    ) -> None:
        """Sobreposição (backend-api-e-fluxos.md §4.1), mesma regra de
        `BookingService._validate_no_overlap`: `start_time <
        existing.end_time AND end_time > existing.start_time` contra
        bookings ativos (pendente não expirado, confirmada, bloqueado)."""
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
        booking_service: BookingService = Depends(BookingService.get_service),
        group_service: GroupService = Depends(GroupService.get_service),
    ) -> "BookingAdminService":
        return BookingAdminService(
            booking_repository=booking_repository,
            payment_repository=payment_repository,
            payment_service=payment_service,
            booking_service=booking_service,
            group_service=group_service,
        )
