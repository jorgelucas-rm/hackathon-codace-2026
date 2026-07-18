from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.app.model.dto.court import CourtReadDTO
from src.app.model.dto.validators import CnpjStr, PasswordStr

# ~500KB binário em base64 (overhead ~4/3) — mesmo limite usado em `dto/court.py`.
MAX_PHOTO_BASE64_CHARS = 700_000


def _validate_photos_size(photos: Optional[list[str]]) -> Optional[list[str]]:
    if not photos:
        return photos
    for photo in photos:
        if len(photo) > MAX_PHOTO_BASE64_CHARS:
            raise ValueError("Photo exceeds max size of ~500KB")
    return photos


class OpeningHourDTO(BaseModel):
    """Um item por dia da semana — ver `modelo-de-dominio.md` §2."""

    dia_semana: str
    abertura: Optional[str] = None
    fechamento: Optional[str] = None
    fechado: bool = False


class CompanyReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cnpj: str
    name: str
    email: EmailStr
    street: str
    number: str
    neighborhood: str
    city: str
    state: str
    zip_code: str
    situation: bool
    description: Optional[str] = None
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photos: list[str] = Field(default_factory=list)
    amenities: list[str] = Field(default_factory=list)
    opening_hours: list[OpeningHourDTO] = Field(default_factory=list)


class CompanyCreateDTO(BaseModel):
    cnpj: CnpjStr
    name: str = Field(..., min_length=1, max_length=250)
    email: EmailStr
    password: PasswordStr
    street: str = Field(..., min_length=1, max_length=250)
    number: str = Field(..., min_length=1, max_length=20)
    neighborhood: str = Field(..., min_length=1, max_length=150)
    city: str = Field(..., min_length=1, max_length=150)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., min_length=1, max_length=10)


class CompanyUpdateDTO(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=250)
    email: Optional[EmailStr] = Field(default=None)
    street: Optional[str] = Field(default=None, min_length=1, max_length=250)
    number: Optional[str] = Field(default=None, min_length=1, max_length=20)
    neighborhood: Optional[str] = Field(default=None, min_length=1, max_length=150)
    city: Optional[str] = Field(default=None, min_length=1, max_length=150)
    state: Optional[str] = Field(default=None, min_length=2, max_length=2)
    zip_code: Optional[str] = Field(default=None, min_length=1, max_length=10)
    situation: Optional[bool] = Field(default=None)


class CompanyMeUpdateDTO(BaseModel):
    """Atualização de perfil pela própria company autenticada (`PATCH /companies/me`)."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=250)
    description: Optional[str] = Field(default=None, max_length=5000)
    phone: Optional[str] = Field(default=None, max_length=20)
    street: Optional[str] = Field(default=None, min_length=1, max_length=250)
    number: Optional[str] = Field(default=None, min_length=1, max_length=20)
    neighborhood: Optional[str] = Field(default=None, min_length=1, max_length=150)
    city: Optional[str] = Field(default=None, min_length=1, max_length=150)
    state: Optional[str] = Field(default=None, min_length=2, max_length=2)
    zip_code: Optional[str] = Field(default=None, min_length=1, max_length=10)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    photos: Optional[list[str]] = Field(default=None)
    amenities: Optional[list[str]] = Field(default=None)
    opening_hours: Optional[list[OpeningHourDTO]] = Field(default=None)

    @field_validator("photos")
    @classmethod
    def _validate_photos(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        return _validate_photos_size(v)


class CompanySearchCardDTO(BaseModel):
    """Card da busca pública (`GET /companies`)."""

    id: int
    name: str
    cover_photo: Optional[str] = None
    distance_km: Optional[float] = None
    min_price_hour: Optional[int] = None
    nota_media: Optional[float] = None


class CompanyDetailDTO(CompanyReadDTO):
    """Detalhe público completo (`GET /companies/{id}`)."""

    courts: list[CourtReadDTO] = Field(default_factory=list)
    nota_media: Optional[float] = None
