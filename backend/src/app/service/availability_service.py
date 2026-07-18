from datetime import date as date_
from datetime import datetime, time, timedelta, timezone
from typing import Optional

from fastapi import Depends

from src.app.model.dto.booking import AvailabilityGroupDTO, AvailabilityResponseDTO
from src.app.model.enum import ErrorCode
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.booking_type import BookingType
from src.app.model.enum.group_status import GroupStatus
from src.app.model.enum.group_visibility import GroupVisibility
from src.app.repository.booking_repository import BookingRepository
from src.app.repository.court_repository import CourtRepository
from src.app.repository.group_member_repository import GroupMemberRepository
from src.app.repository.group_repository import GroupRepository
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
        group_repository: Optional[GroupRepository] = None,
        group_member_repository: Optional[GroupMemberRepository] = None,
    ):
        self.court_repository = court_repository
        self.booking_repository = booking_repository
        self.payment_repository = payment_repository
        self.payment_service = payment_service
        # T-C (Onda 3, extensão pontual aditiva): opcionais para não quebrar
        # quem já instancia `AvailabilityService` diretamente (ex.: testes de
        # T-B1) sem os dois repositórios novos — sem eles, o slot nunca sai
        # como `open_group` (mesmo comportamento de antes da Onda 3).
        self.group_repository = group_repository
        self.group_member_repository = group_member_repository

    def get_availability(self, court_id: int, date: date_) -> AvailabilityResponseDTO:
        court = self.court_repository.get_by_pk(pk=court_id)
        if not court:
            raise NotFoundException(resource="Court", error_code=ErrorCode.NOT_FOUND)

        opening_hours = court.company.opening_hours or []
        active_bookings = self.booking_repository.get_active_by_court_and_date(
            court_id=court_id, date=date
        )

        busy_intervals: list[tuple[time, time]] = []
        group_intervals: list[dict] = []
        for booking in active_bookings:
            if booking.status == BookingStatus.PENDING:
                if booking.type == BookingType.GROUP:
                    group_dto = self._open_group_slot(booking)
                    if group_dto is not None:
                        group_intervals.append(
                            {
                                "start_time": booking.start_time,
                                "end_time": booking.end_time,
                                "group": group_dto,
                            }
                        )
                        continue
                    # Grupo não está mais aberto/público (ou sem grupo
                    # associado, defensivo) -> conta como ocupado, cai no
                    # `busy_intervals.append` abaixo.
                else:
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
            group_intervals=group_intervals,
        )
        return AvailabilityResponseDTO(court_id=court_id, date=date, slots=slots)

    def _open_group_slot(self, booking) -> Optional[AvailabilityGroupDTO]:
        """Slot `open_group` (T-C, Onda 3): só para booking `type=GROUP`
        `PENDING` cujo grupo está `OPEN` + `visibility=PUBLIC` — grupos
        `LINK` não aparecem na grade pública, mesmo critério de
        `GET /api/groups`. `filled_spots` = `CONFIRMED` + `PENDING` não
        expirado (mesmo critério de `GroupService._filled_spots` —
        duplicado aqui para não importar `group_service`, que já importa
        este módulo, e evitar ciclo)."""
        if self.group_repository is None or self.group_member_repository is None:
            return None

        group = self.group_repository.get_by_booking(booking.id)
        if (
            not group
            or group.status != GroupStatus.OPEN
            or group.visibility != GroupVisibility.PUBLIC
        ):
            return None

        active_members = self.group_member_repository.get_active_by_group(group.id)
        filled_spots = 0
        for member in active_members:
            if member.status.name == "CONFIRMED":
                filled_spots += 1
                continue
            payment = member.payment
            if payment is None and member.payment_id:
                payment = self.payment_repository.get_by_pk(pk=member.payment_id)
            if payment is None or not self.payment_service.is_expired(payment):
                filled_spots += 1

        return AvailabilityGroupDTO(
            id=group.id,
            total_spots=group.total_spots,
            filled_spots=filled_spots,
            spot_price=group.spot_price,
            closing_deadline=group.closing_deadline,
        )

    @staticmethod
    def generate_slots(
        *,
        opening_hours: list[dict],
        busy_intervals: list[tuple[time, time]],
        base_price_hour: int,
        date: date_,
        now: Optional[datetime] = None,
        group_intervals: Optional[list[dict]] = None,
    ) -> list[dict]:
        """Função pura (backend-api-e-fluxos.md §2.5): gera slots de 1h
        dentro do `opening_hours` do dia da semana de `date`; marca `busy`
        quando sobrepõe algum item de `busy_intervals` (já resolvidos como
        "ativos" pelo caller) ou quando o slot já passou.

        `group_intervals` (T-C, Onda 3, param novo e opcional — assinatura
        anterior preservada, `None`/omitido reproduz o comportamento
        original de T-B1 exatamente): lista de
        `{"start_time", "end_time", "group": AvailabilityGroupDTO}` — slots
        que sobrepõem um desses intervalos (e não estão `busy`/passados)
        saem como `open_group` com o `group` correspondente.

        Sem acesso a DB/HTTP — testável isoladamente com dados soltos.
        """
        now = now or datetime.now(timezone.utc)
        group_intervals = group_intervals or []

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

            group = None
            if is_busy or is_past:
                status = "busy"
            else:
                for interval in group_intervals:
                    if (
                        slot_start < interval["end_time"]
                        and slot_end > interval["start_time"]
                    ):
                        group = interval["group"]
                        break
                status = "open_group" if group is not None else "free"

            slots.append(
                {
                    "start_time": slot_start,
                    "end_time": slot_end,
                    "status": status,
                    "price": base_price_hour,
                    "group": group,
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
        group_repository: GroupRepository = Depends(GroupRepository.get_instance()),
        group_member_repository: GroupMemberRepository = Depends(
            GroupMemberRepository.get_instance()
        ),
    ) -> "AvailabilityService":
        return AvailabilityService(
            court_repository=court_repository,
            booking_repository=booking_repository,
            group_repository=group_repository,
            group_member_repository=group_member_repository,
            payment_repository=payment_repository,
            payment_service=payment_service,
        )
