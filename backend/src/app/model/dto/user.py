from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.app.model.dto.validators import PasswordStr, serializable_enum
from src.app.model.enum import Level


class UserReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: serializable_enum(Level)
    situation: bool
    avatar: Optional[str] = None


class UserCreateDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=250)
    email: EmailStr
    password: PasswordStr


class UserUpdateDTO(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=250)
    role: Optional[Level] = Field(default=None)
    situation: Optional[bool] = Field(default=None)
