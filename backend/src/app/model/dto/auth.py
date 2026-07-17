from pydantic import BaseModel, EmailStr, Field

from src.app.model.dto.validators import CnpjStr
from src.app.model.enum import Level


class AuthUser(BaseModel):
    ip: str
    user_id: int
    role: Level


class AuthCompany(BaseModel):
    ip: str
    company_id: int
    role: Level


class LoginUser(BaseModel):
    email: EmailStr
    password: str = Field(...)


class LoginCompany(BaseModel):
    cnpj: CnpjStr
    password: str = Field(...)
