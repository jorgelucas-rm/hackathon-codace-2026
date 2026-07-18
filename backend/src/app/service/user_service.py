import io
from pathlib import Path

from fastapi import Depends, UploadFile
from minio import Minio, error

from src.app.adapter import MinioAdapter
from src.app.model.dto.avatar import AvatarPresetDTO
from src.app.model.dto.favorite import FavoriteCourtsDTO
from src.app.model.dto.pagination import Pagination
from src.app.model.dto.user import (
    UserCreateDTO,
    UserProfileUpdateDTO,
    UserReadDTO,
    UserUpdateDTO,
)
from src.app.model.entity.user import User
from src.app.model.enum import ErrorCode, Level
from src.app.repository.user_repository import UserRepository
from src.app.service.photo_upload import validate_and_upload_photo
from src.infra.exception import ConflictException, NotFoundException
from src.infra.security import hash_password

AVATAR_OBJECT_PREFIX = "avatar/"
# Arquivos reais em `src/app/assets/avatars/` (copiados de `frontend/avatars/`
# — o container do backend não monta o volume do frontend, então os presets
# precisam de uma cópia própria aqui para o seed poder lê-los do disco).
AVATAR_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "avatars"
# Avatares fixos (nossos) vivem no mesmo prefixo que os uploads dos usuários,
# para não exigir um fluxo de busca/listagem separado no bucket.
AVATAR_PRESET_FILENAMES = [
    "avatar_00.svg",
    "avatar_01.svg",
    "avatar_02.svg",
    "avatar_03.svg",
    "avatar_04.svg",
    "avatar_05.svg",
    "avatar_06.svg",
    "avatar_07.svg",
]
AVATAR_PRESET_KEYS = {f"{AVATAR_OBJECT_PREFIX}{name}" for name in AVATAR_PRESET_FILENAMES}
DEFAULT_AVATAR = f"{AVATAR_OBJECT_PREFIX}avatar_00.svg"


def seed_avatars(minio_client: Minio, bucket: str) -> None:
    """Seed idempotente dos avatares padrão no MinIO — sobe cada arquivo de
    `AVATAR_ASSETS_DIR` para `avatar/<filename>` só se ainda não existir no
    bucket, para que os presets em `AVATAR_PRESET_FILENAMES` sempre resolvam
    para uma URL pré-assinada válida.
    """
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)

    for filename in AVATAR_PRESET_FILENAMES:
        object_name = f"{AVATAR_OBJECT_PREFIX}{filename}"
        try:
            minio_client.stat_object(bucket_name=bucket, object_name=object_name)
            continue
        except error.S3Error as e:
            if e.code not in ("NoSuchKey", "NoSuchBucket"):
                raise

        content = (AVATAR_ASSETS_DIR / filename).read_bytes()
        minio_client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=io.BytesIO(content),
            length=len(content),
            content_type="image/svg+xml",
        )


class UserService:

    def __init__(self, user_repository: UserRepository, minio_adapter: MinioAdapter):
        self.user_repository = user_repository
        self.minio_adapter = minio_adapter

    def to_read_dto(self, user: User) -> UserReadDTO:
        """`avatar` sempre expõe a URL pré-assinada resolvida na hora — o
        nome do objeto no bucket nunca é exposto pela API."""
        dto = UserReadDTO.model_validate(user)
        dto.avatar = self.minio_adapter.get_file_from_minio(user.avatar)
        return dto

    def list_avatar_presets(self) -> list[AvatarPresetDTO]:
        return [
            AvatarPresetDTO(
                id=name,
                url=self.minio_adapter.get_file_from_minio(
                    f"{AVATAR_OBJECT_PREFIX}{name}"
                ),
            )
            for name in AVATAR_PRESET_FILENAMES
        ]

    def upload_avatar(self, user_id: int, file: UploadFile) -> User:
        user = self.get_by_id(user_id)

        previous_avatar = user.avatar
        object_name = validate_and_upload_photo(
            self.minio_adapter, file, object_prefix=AVATAR_OBJECT_PREFIX
        )

        user.avatar = object_name
        user = self.user_repository.save(entity=user)

        if previous_avatar not in AVATAR_PRESET_KEYS:
            self.minio_adapter.delete_file_from_minio(object_name=previous_avatar)

        return user

    def set_avatar_preset(self, user_id: int, preset: str) -> User:
        if preset not in AVATAR_PRESET_FILENAMES:
            raise NotFoundException(
                resource="Avatar preset", error_code=ErrorCode.NOT_FOUND
            )

        user = self.get_by_id(user_id)
        previous_avatar = user.avatar

        user.avatar = f"{AVATAR_OBJECT_PREFIX}{preset}"
        user = self.user_repository.save(entity=user)

        if previous_avatar not in AVATAR_PRESET_KEYS:
            self.minio_adapter.delete_file_from_minio(object_name=previous_avatar)

        return user

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
            items=[self.to_read_dto(i) for i in items],
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
            avatar=DEFAULT_AVATAR,
        )
        return self.user_repository.save(entity=user)

    def update(self, user_id: int, dto: UserUpdateDTO) -> User:
        user = self.get_by_id(user_id)

        for field, value in dto.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        return self.user_repository.save(entity=user)

    def update_profile(self, user_id: int, dto: UserProfileUpdateDTO) -> User:
        """`PATCH /users/me` — só os campos do próprio perfil. `UserProfileUpdateDTO`
        não tem `role`/`situation`, então não há como o usuário comum alterá-los
        por aqui (proteção é o schema, não uma checagem manual)."""
        user = self.get_by_id(user_id)

        for field, value in dto.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        return self.user_repository.save(entity=user)

    def list_favorites(self, user_id: int) -> FavoriteCourtsDTO:
        user = self.get_by_id(user_id)
        return FavoriteCourtsDTO(court_ids=list(user.favorite_courts or []))

    def add_favorite(self, user_id: int, court_id: int) -> FavoriteCourtsDTO:
        """Idempotente: favoritar de novo o mesmo `court_id` não duplica."""
        user = self.get_by_id(user_id)

        current = list(user.favorite_courts or [])
        if court_id not in current:
            current.append(court_id)
            # Reatribui a lista inteira (em vez de mutar in place) para que o
            # SQLAlchemy detecte a mudança na coluna JSON e gere o UPDATE.
            user.favorite_courts = current
            user = self.user_repository.save(entity=user)

        return FavoriteCourtsDTO(court_ids=list(user.favorite_courts or []))

    def remove_favorite(self, user_id: int, court_id: int) -> FavoriteCourtsDTO:
        """Idempotente: desfavoritar um `court_id` que nunca foi favoritado não
        dá erro."""
        user = self.get_by_id(user_id)

        current = list(user.favorite_courts or [])
        if court_id in current:
            current.remove(court_id)
            user.favorite_courts = current
            user = self.user_repository.save(entity=user)

        return FavoriteCourtsDTO(court_ids=list(user.favorite_courts or []))

    @staticmethod
    def get_service(
        user_repository: UserRepository = Depends(UserRepository.get_instance()),
        minio_adapter: MinioAdapter = Depends(MinioAdapter.get_instance),
    ) -> "UserService":
        return UserService(user_repository=user_repository, minio_adapter=minio_adapter)
