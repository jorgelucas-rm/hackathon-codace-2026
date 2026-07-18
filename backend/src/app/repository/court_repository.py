from typing import Type

from src.app.model.entity.booking import Booking
from src.app.model.entity.court import Court, court_sport
from src.app.model.entity.group_member import GroupMember
from src.app.model.entity.open_group import OpenGroup
from src.app.model.entity.review import Review
from src.app.repository.base_repository import BaseRepository


class CourtRepository(BaseRepository[Court]):

    @property
    def model(self) -> Type[Court]:
        return Court

    def get_by_company(self, company_id: int) -> list[Court]:
        return (
            self.session.query(Court)
            .filter(Court.company_id == company_id)
            .order_by(Court.id.asc())
            .all()
        )

    def delete_cascade(self, court_id: int) -> None:
        """Exclui a quadra e todo o histórico dependente numa única transação.

        Apenas bulk deletes explícitos, na ordem das FKs (filhos primeiro),
        sem `session.delete` — evita o cascade da relação `court.bookings` e
        remove manualmente a junção `court_sport`. `payment` não tem FK real
        (referência polimórfica), então fica sem quebrar constraint.
        """
        session = self.session

        booking_ids = [
            row[0]
            for row in session.query(Booking.id)
            .filter(Booking.court_id == court_id)
            .all()
        ]

        if booking_ids:
            group_ids = [
                row[0]
                for row in session.query(OpenGroup.id)
                .filter(OpenGroup.booking_id.in_(booking_ids))
                .all()
            ]
            if group_ids:
                session.query(GroupMember).filter(
                    GroupMember.group_id.in_(group_ids)
                ).delete(synchronize_session=False)
                session.query(OpenGroup).filter(
                    OpenGroup.id.in_(group_ids)
                ).delete(synchronize_session=False)

            session.query(Review).filter(
                Review.booking_id.in_(booking_ids)
            ).delete(synchronize_session=False)
            session.query(Booking).filter(
                Booking.court_id == court_id
            ).delete(synchronize_session=False)

        session.execute(court_sport.delete().where(court_sport.c.court_id == court_id))
        session.query(Court).filter(Court.id == court_id).delete(
            synchronize_session=False
        )
        session.commit()

    @property
    def orderable_fields(self) -> dict:
        return {
            "id": Court.id,
            "name": Court.name,
            "base_price_hour": Court.base_price_hour,
        }

    @property
    def equal_filters(self) -> dict:
        return {
            "company_id": Court.company_id,
            "status": Court.status,
        }
