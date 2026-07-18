from typing import Type

from src.app.model.entity.court import Court
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
