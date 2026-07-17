from typing import Optional, Type

from src.app.model.entity.user import User
from src.app.repository.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):

    @property
    def model(self) -> Type[User]:
        return User

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter(User.email == email).first()

    @property
    def orderable_fields(self) -> dict:
        return {
            "id": User.id,
            "name": User.name,
            "email": User.email,
            "role": User.role,
            "situation": User.situation,
        }

    @property
    def like_filters(self) -> dict:
        return {
            "name": User.name,
            "email": User.email,
        }

    @property
    def equal_filters(self) -> dict:
        return {
            "id": User.id,
            "role": User.role,
            "situation": User.situation,
        }
