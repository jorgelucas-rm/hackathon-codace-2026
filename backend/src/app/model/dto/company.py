from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.app.model.dto.validators import CnpjStr, PasswordStr


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
