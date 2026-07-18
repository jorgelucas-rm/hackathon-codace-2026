from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.app.model.dto.sport import SportReadDTO
from src.app.model.dto.validators import serializable_enum
from src.app.model.enum.court_status import CourtStatus

# ~500KB binário em base64 (overhead ~4/3) — mesmo limite de fotos usado em
# `dto/company.py`.
MAX_PHOTO_BASE64_CHARS = 700_000


def _validate_photos_size(photos: Optional[list[str]]) -> Optional[list[str]]:
    if not photos:
        return photos
    for photo in photos:
        if len(photo) > MAX_PHOTO_BASE64_CHARS:
            raise ValueError("Photo exceeds max size of ~500KB")
    return photos


class CompanySummaryDTO(BaseModel):
    """Dados resumidos da arena, embutidos no detalhe público da quadra."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str
    state: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CourtReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    capacity: int
    photos: list[str] = Field(default_factory=list)
    base_price_hour: int
    status: serializable_enum(CourtStatus)
    sports: list[SportReadDTO] = Field(default_factory=list)


class CourtDetailDTO(CourtReadDTO):
    company: CompanySummaryDTO


class CourtCreateDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    capacity: int = Field(..., ge=1)
    photos: list[str] = Field(default_factory=list)
    base_price_hour: int = Field(..., ge=0)
    sport_ids: list[int] = Field(default_factory=list)

    @field_validator("photos")
    @classmethod
    def _validate_photos(cls, v: list[str]) -> list[str]:
        return _validate_photos_size(v) or []


class CourtUpdateDTO(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    capacity: Optional[int] = Field(default=None, ge=1)
    photos: Optional[list[str]] = Field(default=None)
    base_price_hour: Optional[int] = Field(default=None, ge=0)
    status: Optional[CourtStatus] = Field(default=None)
    sport_ids: Optional[list[int]] = Field(default=None)

    @field_validator("photos")
    @classmethod
    def _validate_photos(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        return _validate_photos_size(v)
