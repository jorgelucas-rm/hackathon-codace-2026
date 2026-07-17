from fastapi import Depends

from src.app.model.dto.pagination import Pagination
from src.app.model.dto.user import UserCreateDTO, UserReadDTO, UserUpdateDTO
from src.app.model.entity.user import User
from src.app.model.enum import ErrorCode, Level
from src.app.repository.user_repository import UserRepository
from src.infra.exception import ConflictException, NotFoundException
from src.infra.security import hash_password


class UserService:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_all_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        order_by: str | None = None,
        order_direction: str | None = None,
        filters: dict | None = None,
    ) -> Pagination[UserReadDTO]:
        items, total, total_filtered = self.user_repository.get_paginated(
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_direction=order_direction,
            filters=filters,
        )
        return Pagination[UserReadDTO](
            items=[UserReadDTO.model_validate(i) for i in items],
            total=total,
            total_filtered=total_filtered,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    def get_by_id(self, user_id: int) -> User:
        user = self.user_repository.get_by_pk(pk=user_id)
        if not user:
            raise NotFoundException(resource="User", error_code=ErrorCode.NOT_FOUND)
        return user

    def register(self, dto: UserCreateDTO) -> User:
        """Auto-cadastro público — sempre criado com o papel USER (nunca ADMIN)."""
        if self.user_repository.get_by_email(dto.email):
            raise ConflictException(
                message="There is already a user with that e-mail.",
                error_code=ErrorCode.EMAIL_IN_USE,
            )

        user = User(
            name=dto.name,
            email=dto.email,
            password=hash_password(dto.password),
            role=Level.USER,
        )
        return self.user_repository.save(entity=user)

    def update(self, user_id: int, dto: UserUpdateDTO) -> User:
        user = self.get_by_id(user_id)

        for field, value in dto.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        return self.user_repository.save(entity=user)

    @staticmethod
    def get_service(
        user_repository: UserRepository = Depends(UserRepository.get_instance()),
    ) -> "UserService":
        return UserService(user_repository=user_repository)
