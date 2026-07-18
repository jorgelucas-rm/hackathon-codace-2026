from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.app.model.dto.validators import PasswordStr, serializable_enum
from src.app.model.enum import Level
from src.app.model.enum.skill_level import SkillLevel


class UserReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: serializable_enum(Level)
    situation: bool
    avatar: Optional[str] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sports_of_interest: list[int] = Field(default_factory=list)
    favorite_courts: list[int] = Field(default_factory=list)
    skill_level: Optional[serializable_enum(SkillLevel)] = None


class UserCreateDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=250)
    email: EmailStr
    password: PasswordStr


class UserUpdateDTO(BaseModel):
    """Uso exclusivo da rota ADMIN `PUT /admin/users/{id}` — troca `role`/
    `situation`, que um usuário comum nunca pode setar em si mesmo. NÃO
    reutilizar para `PATCH /users/me` (ver `UserProfileUpdateDTO`)."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=250)
    role: Optional[Level] = Field(default=None)
    situation: Optional[bool] = Field(default=None)


class UserProfileUpdateDTO(BaseModel):
    """DTO da rota `PATCH /users/me` (o próprio usuário atualizando seu
    perfil). Deliberadamente sem `role`/`situation` (exclusivos da rota
    admin) e sem `avatar`/`photo` (tratado por rota própria de upload)."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=250)
    phone: Optional[str] = Field(default=None, max_length=20)
    street: Optional[str] = Field(default=None, max_length=250)
    number: Optional[str] = Field(default=None, max_length=20)
    zip_code: Optional[str] = Field(default=None, max_length=10)
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
    sports_of_interest: Optional[list[int]] = Field(default=None)
    skill_level: Optional[serializable_enum(SkillLevel)] = Field(default=None)
