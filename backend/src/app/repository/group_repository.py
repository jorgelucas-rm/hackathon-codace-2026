from typing import Optional, Type

from src.app.model.entity.open_group import OpenGroup
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
