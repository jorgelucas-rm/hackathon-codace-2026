from datetime import date as date_
from typing import Optional, Type

from src.app.model.entity.booking import Booking
from src.app.model.entity.court import Court
from src.app.model.enum.booking_status import BookingStatus
from src.app.repository.base_repository import BaseRepository

# Status considerados "ativos" para exclusividade de horário/disponibilidade
# (backend-api-e-fluxos.md §4.1): pendente (não expirado — checado à parte
# via `payment_service.is_expired`), confirmada, bloqueado.
ACTIVE_STATUSES = (
    BookingStatus.PENDING,
    BookingStatus.CONFIRMED,
    BookingStatus.BLOCKED,
)


class BookingRepository(BaseRepository[Booking]):

    @property
    def model(self) -> Type[Booking]:
        return Booking

    def get_court_for_update(self, court_id: int) -> Optional[Court]:
        """Lock de linha (`SELECT ... FOR UPDATE`) na `Court` — base da
        exclusividade de horário (backend-api-e-fluxos.md §4.1). Deve ser
        chamado dentro da mesma transação que revalida a sobreposição e cria
        o booking; o lock é liberado no commit/rollback da sessão."""
        return (
            self.session.query(Court)
            .filter(Court.id == court_id)
            .with_for_update()
            .first()
        )

    def get_active_by_court_and_date(
        self, court_id: int, date: date_
    ) -> list[Booking]:
        """Bookings `PENDING`/`CONFIRMED`/`BLOCKED` do dia — expiração de
        `PENDING` é responsabilidade do caller (via `payment_service`), não
        desta query (mantém o repositório livre de dependência de payment)."""
        return (
            self.session.query(Booking)
            .filter(
                Booking.court_id == court_id,
                Booking.date == date,
                Booking.status.in_(ACTIVE_STATUSES),
            )
            .order_by(Booking.start_time.asc())
            .all()
        )

    def get_by_creator(self, user_id: int) -> list[Booking]:
        return (
            self.session.query(Booking)
            .filter(Booking.creator_user_id == user_id)
            .order_by(Booking.date.asc(), Booking.start_time.asc())
            .all()
        )

    @property
    def orderable_fields(self) -> dict:
        return {
            "id": Booking.id,
            "date": Booking.date,
            "start_time": Booking.start_time,
            "status": Booking.status,
            "created_at": Booking.created_at,
        }

    @property
    def equal_filters(self) -> dict:
        return {
            "court_id": Booking.court_id,
            "creator_user_id": Booking.creator_user_id,
            "creator_company_id": Booking.creator_company_id,
            "date": Booking.date,
            "status": Booking.status,
            "type": Booking.type,
        }
