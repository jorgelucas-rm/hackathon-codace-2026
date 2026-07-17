from typing import Optional, Type

from src.app.model.entity.company import Company
from src.app.repository.base_repository import BaseRepository


class CompanyRepository(BaseRepository[Company]):

    @property
    def model(self) -> Type[Company]:
        return Company

    def get_by_cnpj(self, cnpj: str) -> Optional[Company]:
        return self.session.query(Company).filter(Company.cnpj == cnpj).first()

    @property
    def orderable_fields(self) -> dict:
        return {
            "id": Company.id,
            "cnpj": Company.cnpj,
            "name": Company.name,
            "email": Company.email,
            "city": Company.city,
            "state": Company.state,
            "situation": Company.situation,
        }

    @property
    def like_filters(self) -> dict:
        return {
            "cnpj": Company.cnpj,
            "name": Company.name,
            "email": Company.email,
            "street": Company.street,
            "neighborhood": Company.neighborhood,
            "city": Company.city,
            "zip_code": Company.zip_code,
        }

    @property
    def equal_filters(self) -> dict:
        return {
            "id": Company.id,
            "state": Company.state,
            "situation": Company.situation,
        }
