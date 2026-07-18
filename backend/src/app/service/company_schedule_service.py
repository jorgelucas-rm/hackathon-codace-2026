from collections import Counter
from datetime import date as date_
from typing import Optional

from fastapi import Depends

from src.app.model.dto.booking_admin import CompanyReportDTO
from src.app.model.dto.company_schedule import (
    CompanyScheduleResponseDTO,
    CourtScheduleDTO,
    ScheduleBookingDTO,
    ScheduleCustomerDTO,
)
from src.app.model.entity.booking import Booking
from src.app.model.enum import ErrorCode
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.booking_type import BookingType
from src.app.repository.booking_repository import BookingRepository
from src.app.repository.court_repository import CourtRepository
from src.app.repository.user_repository import UserRepository
from src.app.service.group_service import GroupService
from src.infra.exception import BadRequestException

# T-D (Fase D, Onda 3) — leitura do painel: agenda do dia e relatório.
# Escrita (bloqueios/reserva manual/cancelamento pelo estabelecimento) fica
# em `booking_admin_service.py`.

# Aproximação de capacidade teórica para o relatório de ocupação quando não
# vale a pena reconstruir `AvailabilityService.generate_slots` por court/dia
# no período: horas de operação médias assumidas por dia (decisão local de
# T-D, documentada no método `get_report`).
REPORT_HOURS_PER_DAY_APPROX = 12

REVENUE_STATUSES = (BookingStatus.CONFIRMED, BookingStatus.COMPLETED)
OCCUPIED_STATUSES = (
    BookingStatus.CONFIRMED,
    BookingStatus.COMPLETED,
    BookingStatus.BLOCKED,
)
PEAK_STATUSES = (
    BookingStatus.PENDING,
    BookingStatus.CONFIRMED,
    BookingStatus.COMPLETED,
    BookingStatus.BLOCKED,
)


class CompanyScheduleService:
    """`GET /api/companies/me/schedule?date=` e `GET
    /api/companies/me/report?from=&to=` (T-D, Fase D). Uma chamada monta a
    tela do painel: grade do dia de todas as courts da company, com cliente
    e (se `type=GROUP`) dados do grupo embutidos via `GroupService`."""

    def __init__(
        self,
        court_repository: CourtRepository,
        booking_repository: BookingRepository,
        user_repository: UserRepository,
        group_service: GroupService,
    ):
        self.court_repository = court_repository
        self.booking_repository = booking_repository
        self.user_repository = user_repository
        self.group_service = group_service

    def get_schedule(
        self, company_id: int, date: date_
    ) -> CompanyScheduleResponseDTO:
        courts = self.court_repository.get_by_company(company_id=company_id)

        court_schedules: list[CourtScheduleDTO] = []
        for court in courts:
            active_bookings = self.booking_repository.get_active_by_court_and_date(
                court_id=court.id, date=date
            )
            court_schedules.append(
                CourtScheduleDTO(
                    court_id=court.id,
                    court_name=court.name,
                    bookings=[self._to_schedule_dto(b) for b in active_bookings],
                )
            )

        return CompanyScheduleResponseDTO(date=date, courts=court_schedules)

    def _to_schedule_dto(self, booking: Booking) -> ScheduleBookingDTO:
        customer = self._resolve_customer(booking)

        group = None
        if booking.type == BookingType.GROUP:
            group = self.group_service.get_panel_summary(booking_id=booking.id)

        return ScheduleBookingDTO(
            id=booking.id,
            court_id=booking.court_id,
            date=booking.date,
            start_time=booking.start_time,
            end_time=booking.end_time,
            type=booking.type,
            status=booking.status,
            reason=booking.reason,
            total_price=booking.total_price,
            customer=customer,
            group=group,
        )

    def _resolve_customer(self, booking: Booking) -> Optional[ScheduleCustomerDTO]:
        if booking.creator_user_id:
            user = self.user_repository.get_by_pk(pk=booking.creator_user_id)
            if user:
                return ScheduleCustomerDTO(name=user.name, phone=user.phone)
            return None
        if booking.customer_name or booking.customer_phone:
            return ScheduleCustomerDTO(
                name=booking.customer_name, phone=booking.customer_phone
            )
        return None

    def get_report(
        self, company_id: int, from_date: date_, to_date: date_
    ) -> CompanyReportDTO:
        """Relatório simples (decisão local de T-D, `backend-api-e-fluxos.md`
        §3.6):

        - **Receita confirmada**: soma de `total_price` dos bookings
          `CONFIRMED`/`COMPLETED` no período.
        - **Ocupação**: proporção de slots ocupados (`CONFIRMED`/
          `COMPLETED`/`BLOCKED`) sobre uma capacidade teórica aproximada
          (`REPORT_HOURS_PER_DAY_APPROX` horas/dia × dias do período × número
          de courts) — aproximação deliberada em vez de recalcular
          `generate_slots` por court/dia (custo desnecessário para um
          relatório).
        - **Picos**: dia e horário de início (`start_time`) com mais
          bookings ativos (`PENDING`/`CONFIRMED`/`COMPLETED`/`BLOCKED`) no
          período — o mais frequente de cada, não uma série completa.
        """
        if from_date > to_date:
            raise BadRequestException(
                error_type="Invalid report range",
                details="'from' must not be after 'to'",
                error_code=ErrorCode.INVALID_TIME_RANGE,
            )

        courts = self.court_repository.get_by_company(company_id=company_id)
        court_ids = [c.id for c in courts]

        if not court_ids:
            return CompanyReportDTO(
                from_date=from_date,
                to_date=to_date,
                total_bookings=0,
                confirmed_revenue=0,
                occupied_slots=0,
                available_slots=0,
                occupancy_rate=0.0,
                peak_day=None,
                peak_hour=None,
            )

        bookings = (
            self.booking_repository.session.query(Booking)
            .filter(
                Booking.court_id.in_(court_ids),
                Booking.date >= from_date,
                Booking.date <= to_date,
            )
            .all()
        )

        confirmed_revenue = sum(
            b.total_price for b in bookings if b.status in REVENUE_STATUSES
        )
        occupied_slots = sum(1 for b in bookings if b.status in OCCUPIED_STATUSES)

        days = (to_date - from_date).days + 1
        available_slots = len(court_ids) * days * REPORT_HOURS_PER_DAY_APPROX
        occupancy_rate = (
            round(occupied_slots / available_slots, 4) if available_slots else 0.0
        )

        peak_pool = [b for b in bookings if b.status in PEAK_STATUSES]
        day_counter = Counter(b.date for b in peak_pool)
        hour_counter = Counter(b.start_time for b in peak_pool)
        peak_day = day_counter.most_common(1)[0][0] if day_counter else None
        peak_hour = hour_counter.most_common(1)[0][0] if hour_counter else None

        return CompanyReportDTO(
            from_date=from_date,
            to_date=to_date,
            total_bookings=len(bookings),
            confirmed_revenue=confirmed_revenue,
            occupied_slots=occupied_slots,
            available_slots=available_slots,
            occupancy_rate=occupancy_rate,
            peak_day=peak_day,
            peak_hour=peak_hour,
        )

    @staticmethod
    def get_service(
        court_repository: CourtRepository = Depends(CourtRepository.get_instance()),
        booking_repository: BookingRepository = Depends(
            BookingRepository.get_instance()
        ),
        user_repository: UserRepository = Depends(UserRepository.get_instance()),
        group_service: GroupService = Depends(GroupService.get_service),
    ) -> "CompanyScheduleService":
        return CompanyScheduleService(
            court_repository=court_repository,
            booking_repository=booking_repository,
            user_repository=user_repository,
            group_service=group_service,
        )
