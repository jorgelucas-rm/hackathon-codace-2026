from typing import Optional, Type

from src.app.model.entity.sport import Sport
from src.app.repository.base_repository import BaseRepository


class SportRepository(BaseRepository[Sport]):

    @property
    def model(self) -> Type[Sport]:
        return Sport

    def get_by_name(self, name: str) -> Optional[Sport]:
        return self.session.query(Sport).filter(Sport.name == name).first()

    def get_all(self) -> list[Sport]:
        return self.session.query(Sport).order_by(Sport.name.asc()).all()

    def get_by_ids(self, ids: list[int]) -> list[Sport]:
        if not ids:
            return []
        return self.session.query(Sport).filter(Sport.id.in_(ids)).all()

    @property
    def orderable_fields(self) -> dict:
        return {"id": Sport.id, "name": Sport.name}
