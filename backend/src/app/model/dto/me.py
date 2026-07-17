from typing import Optional

from pydantic import BaseModel

from src.app.model.dto.company import CompanyReadDTO
from src.app.model.dto.user import UserReadDTO


class MeUserReadDTO(BaseModel):
    auth_type: str = "USER"
    entity: Optional[UserReadDTO] = None


class MeCompanyReadDTO(BaseModel):
    auth_type: str = "COMPANY"
    entity: Optional[CompanyReadDTO] = None
