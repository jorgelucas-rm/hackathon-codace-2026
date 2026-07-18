from typing import Optional, Type

from sqlalchemy.orm import selectinload

from src.app.model.entity.company import Company
from src.app.model.entity.court import Court, court_sport
from src.app.model.enum.court_status import CourtStatus
from src.app.repository.base_repository import BaseRepository


class CompanyRepository(BaseRepository[Company]):

    @property
    def model(self) -> Type[Company]:
        return Company

    def get_by_cnpj(self, cnpj: str) -> Optional[Company]:
        return self.session.query(Company).filter(Company.cnpj == cnpj).first()

    def search_public(
        self,
        sport_id: Optional[int] = None,
        name_like: Optional[str] = None,
    ) -> list[Company]:
        """Candidatos ativos para a busca pública (`GET /companies`).

        Filtro por esporte é feito via join relacional real com
        `court`/`court_sport` (não JSON). Distância/raio/comodidades são
        filtrados em memória pelo service (Haversine em Python puro).
        """
        query = (
            self.session.query(Company)
            .options(selectinload(Company.courts).selectinload(Court.sports))
            .filter(Company.situation.is_(True))
        )

        if sport_id is not None:
            # Subquery (IN), não DISTINCT: Company tem colunas JSON (photos/
            # amenities/opening_hours) e o tipo `json` do Postgres não tem
            # operador de igualdade — um DISTINCT sobre o SELECT completo
            # quebraria. IN por id evita comparar as colunas JSON.
            matching_company_ids = (
                self.session.query(Court.company_id)
                .join(court_sport, court_sport.c.court_id == Court.id)
                .filter(court_sport.c.sport_id == sport_id)
                .filter(Court.status == CourtStatus.ACTIVE)
                .scalar_subquery()
            )
            query = query.filter(Company.id.in_(matching_company_ids))

        if name_like:
            query = query.filter(Company.name.ilike(f"%{name_like}%"))

        return query.all()

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
