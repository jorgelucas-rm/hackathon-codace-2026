from datetime import date as date_
from datetime import datetime, time, timedelta, timezone
from typing import Optional

from fastapi import Depends

from src.app.model.dto.booking import AvailabilityResponseDTO
from src.app.model.enum import ErrorCode
from src.app.model.enum.booking_status import BookingStatus
from src.app.repository.booking_repository import BookingRepository
from src.app.repository.court_repository import CourtRepository
from src.app.repository.payment_repository import PaymentRepository
from src.app.service.payment_service import PaymentService
from src.infra.exception import NotFoundException

# Ordem de `date.weekday()` (0=segunda) mapeada para os códigos usados em
# `Company.opening_hours` (modelo-de-dominio.md §2): lista de
# `{dia_semana, abertura, fechamento, fechado}`.
_WEEKDAY_CODES = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]

SLOT_DURATION = timedelta(hours=1)


def _find_opening_hours_for_date(
    opening_hours: list[dict], target_date: date_
) -> Optional[dict]:
    weekday_code = _WEEKDAY_CODES[target_date.weekday()]
    for entry in opening_hours or []:
        if entry.get("dia_semana") == weekday_code:
            return entry
    return None


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")[:2]
    return time(int(hour), int(minute))


class AvailabilityService:
    """`GET /api/courts/{id}/availability?date=` (backend-api-e-fluxos.md
    §2.5). `generate_slots` é uma função pura/estática — não toca DB, só
    recebe dados já resolvidos — para ser testável sem HTTP/banco; o resto
    da classe é a orquestração que busca esses dados."""

    def __init__(
        self,
        court_repository: CourtRepository,
        booking_repository: BookingRepository,
        payment_repository: PaymentRepository,
        payment_service: PaymentService,
    ):
        self.court_repository = court_repository
        self.booking_repository = booking_repository
        self.payment_repository = payment_repository
        self.payment_service = payment_service

    def get_availability(self, court_id: int, date: date_) -> AvailabilityResponseDTO:
        court = self.court_repository.get_by_pk(pk=court_id)
        if not court:
            raise NotFoundException(resource="Court", error_code=ErrorCode.NOT_FOUND)

        opening_hours = court.company.opening_hours or []
        active_bookings = self.booking_repository.get_active_by_court_and_date(
            court_id=court_id, date=date
        )

        busy_intervals: list[tuple[time, time]] = []
        for booking in active_bookings:
            if booking.status == BookingStatus.PENDING:
                payment = self.payment_repository.get_by_reference(
                    reference_type="booking", reference_id=booking.id
                )
                if payment and self.payment_service.is_expired(payment):
                    continue
            busy_intervals.append((booking.start_time, booking.end_time))

        slots = self.generate_slots(
            opening_hours=opening_hours,
            busy_intervals=busy_intervals,
            base_price_hour=court.base_price_hour,
            date=date,
        )
        return AvailabilityResponseDTO(court_id=court_id, date=date, slots=slots)

    @staticmethod
    def generate_slots(
        *,
        opening_hours: list[dict],
        busy_intervals: list[tuple[time, time]],
        base_price_hour: int,
        date: date_,
        now: Optional[datetime] = None,
    ) -> list[dict]:
        """Função pura (backend-api-e-fluxos.md §2.5): gera slots de 1h
        dentro do `opening_hours` do dia da semana de `date`; marca `busy`
        quando sobrepõe algum item de `busy_intervals` (já resolvidos como
        "ativos" pelo caller) ou quando o slot já passou; nesta fase nunca
        retorna `open_group` (gancho da Onda 3). `group` é sempre `None`.

        Sem acesso a DB/HTTP — testável isoladamente com dados soltos.
        """
        now = now or datetime.now(timezone.utc)

        day_config = _find_opening_hours_for_date(opening_hours, date)
        if (
            not day_config
            or day_config.get("fechado")
            or not day_config.get("abertura")
            or not day_config.get("fechamento")
        ):
            return []

        opening = _parse_hhmm(day_config["abertura"])
        closing = _parse_hhmm(day_config["fechamento"])

        cursor = datetime.combine(date, opening)
        end_of_day = datetime.combine(date, closing)

        slots: list[dict] = []
        while cursor + SLOT_DURATION <= end_of_day:
            slot_start = cursor.time()
            slot_end = (cursor + SLOT_DURATION).time()

            is_busy = any(
                slot_start < busy_end and slot_end > busy_start
                for busy_start, busy_end in busy_intervals
            )
            is_past = datetime.combine(date, slot_start, tzinfo=timezone.utc) < now
            status = "busy" if (is_busy or is_past) else "free"

            slots.append(
                {
                    "start_time": slot_start,
                    "end_time": slot_end,
                    "status": status,
                    "price": base_price_hour,
                    "group": None,
                }
            )
            cursor += SLOT_DURATION

        return slots

    @staticmethod
    def get_service(
        court_repository: CourtRepository = Depends(CourtRepository.get_instance()),
        booking_repository: BookingRepository = Depends(
            BookingRepository.get_instance()
        ),
        payment_repository: PaymentRepository = Depends(
            PaymentRepository.get_instance()
        ),
        payment_service: PaymentService = Depends(PaymentService.get_service),
    ) -> "AvailabilityService":
        return AvailabilityService(
            court_repository=court_repository,
            booking_repository=booking_repository,
            payment_repository=payment_repository,
            payment_service=payment_service,
        )
