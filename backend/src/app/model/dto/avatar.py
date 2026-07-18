from pydantic import BaseModel, Field


class AvatarPresetDTO(BaseModel):
    id: str
    url: str | None = None


class AvatarPresetSelectDTO(BaseModel):
    preset: str = Field(..., min_length=1)
