from datetime import date as date_
from datetime import datetime
from typing import Optional, Type

from src.app.model.entity.booking import Booking
from src.app.model.entity.court import Court, court_sport
from src.app.model.entity.open_group import OpenGroup
from src.app.model.enum.group_status import GroupStatus
from src.app.model.enum.group_visibility import GroupVisibility
from src.app.repository.base_repository import BaseRepository


class GroupRepository(BaseRepository[OpenGroup]):

    @property
    def model(self) -> Type[OpenGroup]:
        return OpenGroup

    def get_by_booking(self, booking_id: int) -> Optional[OpenGroup]:
        return (
            self.session.query(OpenGroup)
            .filter(OpenGroup.booking_id == booking_id)
            .first()
        )

    def get_for_update(self, group_id: int) -> Optional[OpenGroup]:
        """Lock de linha (`SELECT ... FOR UPDATE`) no `OpenGroup` — base da
        exclusividade de vaga em `POST /api/groups/{id}/join`
        (backend-api-e-fluxos.md §3.3), mesmo padrão do lock de `Court` em
        `BookingRepository.get_court_for_update`."""
        return (
            self.session.query(OpenGroup)
            .filter(OpenGroup.id == group_id)
            .with_for_update()
            .first()
        )

    def search_public(
        self,
        now: datetime,
        sport_id: Optional[int] = None,
        court_id: Optional[int] = None,
        date: Optional[date_] = None,
    ) -> list[OpenGroup]:
        """`GET /api/groups` (busca pública, backend-api-e-fluxos.md §2.7):
        só grupos `OPEN` + `PUBLIC` com `closing_deadline` futuro. Filtros
        opcionais por esporte (via junção `court_sport`), quadra e data do
        agendamento associado."""
        query = (
            self.session.query(OpenGroup)
            .join(Booking, OpenGroup.booking_id == Booking.id)
            .filter(
                OpenGroup.status == GroupStatus.OPEN,
                OpenGroup.visibility == GroupVisibility.PUBLIC,
                OpenGroup.closing_deadline > now,
            )
        )
        if court_id is not None:
            query = query.filter(Booking.court_id == court_id)
        if date is not None:
            query = query.filter(Booking.date == date)
        if sport_id is not None:
            query = query.join(Court, Booking.court_id == Court.id).join(
                court_sport, Court.id == court_sport.c.court_id
            ).filter(court_sport.c.sport_id == sport_id)

        return query.order_by(Booking.date.asc(), Booking.start_time.asc()).all()

    @property
    def orderable_fields(self) -> dict:
        return {
            "id": OpenGroup.id,
            "status": OpenGroup.status,
            "closing_deadline": OpenGroup.closing_deadline,
            "created_at": OpenGroup.created_at,
        }

    @property
    def equal_filters(self) -> dict:
        return {
            "status": OpenGroup.status,
            "visibility": OpenGroup.visibility,
        }
