from typing import Optional, Type

from sqlalchemy import func

from src.app.model.entity.review import Review
from src.app.repository.base_repository import BaseRepository


class ReviewRepository(BaseRepository[Review]):

    @property
    def model(self) -> Type[Review]:
        return Review

    def get_by_booking_and_user(
        self, booking_id: int, user_id: int
    ) -> Optional[Review]:
        """Trava de "uma avaliação por usuário por agendamento" — checagem em
        nível de aplicação, além do `UniqueConstraint` do banco (ver
        `entity/review.py`)."""
        return (
            self.session.query(Review)
            .filter(Review.booking_id == booking_id, Review.user_id == user_id)
            .first()
        )

    def get_average_and_count(self, company_id: int) -> tuple[Optional[float], int]:
        """`AVG(rating)`/contagem por `company_id` — usado por
        `CompanyService` para preencher `nota_media`."""
        avg_rating, count = (
            self.session.query(func.avg(Review.rating), func.count(Review.id))
            .filter(Review.company_id == company_id)
            .one()
        )
        return (float(avg_rating) if avg_rating is not None else None, count or 0)

    @property
    def orderable_fields(self) -> dict:
        return {
            "id": Review.id,
            "rating": Review.rating,
            "helpful_count": Review.helpful_count,
            "created_at": Review.created_at,
        }

    @property
    def equal_filters(self) -> dict:
        return {
            "company_id": Review.company_id,
            "booking_id": Review.booking_id,
            "user_id": Review.user_id,
            "rating": Review.rating,
        }
