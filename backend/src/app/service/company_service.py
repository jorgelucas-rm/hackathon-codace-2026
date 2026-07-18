import math
from typing import Optional

from fastapi import Depends

from src.app.model.dto.company import (
    CompanyCreateDTO,
    CompanyDetailDTO,
    CompanyMeUpdateDTO,
    CompanyReadDTO,
    CompanySearchCardDTO,
    CompanyUpdateDTO,
)
from src.app.model.dto.court import CourtReadDTO
from src.app.model.dto.pagination import Pagination
from src.app.model.entity.company import Company
from src.app.model.entity.court import Court
from src.app.model.enum import ErrorCode
from src.app.model.enum.court_status import CourtStatus
from src.app.repository.company_repository import CompanyRepository
from src.infra.exception import ConflictException, NotFoundException
from src.infra.security import hash_password

EARTH_RADIUS_KM = 6371.0


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distância em km entre duas coordenadas — Haversine em Python puro
    (sem PostGIS), conforme decisão de reconciliação do prompt (item 4)."""
    lat1_r, lng1_r, lat2_r, lng2_r = map(math.radians, (lat1, lng1, lat2, lng2))
    dlat = lat2_r - lat1_r
    dlng = lng2_r - lng1_r
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    )
    return EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


class CompanyService:

    def __init__(self, company_repository: CompanyRepository):
        self.company_repository = company_repository

    def get_all_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        order_by: str | None = None,
        order_direction: str | None = None,
        filters: dict | None = None,
    ) -> Pagination[CompanyReadDTO]:
        items, total, total_filtered = self.company_repository.get_paginated(
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_direction=order_direction,
            filters=filters,
        )
        return Pagination[CompanyReadDTO](
            items=[CompanyReadDTO.model_validate(i) for i in items],
            total=total,
            total_filtered=total_filtered,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    def get_by_id(self, company_id: int) -> Company:
        company = self.company_repository.get_by_pk(pk=company_id)
        if not company:
            raise NotFoundException(resource="Company", error_code=ErrorCode.NOT_FOUND)
        return company

    def register(self, dto: CompanyCreateDTO) -> Company:
        """Auto-cadastro público de empresa."""
        if self.company_repository.get_by_cnpj(dto.cnpj):
            raise ConflictException(
                message="There is already a company with that CNPJ.",
                error_code=ErrorCode.CNPJ_IN_USE,
            )

        company = Company(
            cnpj=dto.cnpj,
            name=dto.name,
            email=dto.email,
            password=hash_password(dto.password),
            street=dto.street,
            number=dto.number,
            neighborhood=dto.neighborhood,
            city=dto.city,
            state=dto.state,
            zip_code=dto.zip_code,
        )
        return self.company_repository.save(entity=company)

    def update(self, company_id: int, dto: CompanyUpdateDTO) -> Company:
        company = self.get_by_id(company_id)

        for field, value in dto.model_dump(exclude_unset=True).items():
            setattr(company, field, value)

        return self.company_repository.save(entity=company)

    def update_me(self, company_id: int, dto: CompanyMeUpdateDTO) -> Company:
        """`PATCH /companies/me` — a própria company autenticada atualiza seu perfil."""
        company = self.get_by_id(company_id)

        for field, value in dto.model_dump(exclude_unset=True).items():
            setattr(company, field, value)

        return self.company_repository.save(entity=company)

    def _active_courts(self, company: Company) -> list[Court]:
        return [c for c in company.courts if c.status == CourtStatus.ACTIVE]

    def _to_search_card(
        self, company: Company, distance_km: Optional[float]
    ) -> CompanySearchCardDTO:
        active_courts = self._active_courts(company)
        min_price_hour = min(
            (c.base_price_hour for c in active_courts), default=None
        )
        cover_photo = company.photos[0] if company.photos else None
        return CompanySearchCardDTO(
            id=company.id,
            name=company.name,
            cover_photo=cover_photo,
            distance_km=round(distance_km, 2) if distance_km is not None else None,
            min_price_hour=min_price_hour,
            # `nota_media` ainda não existe (sem entidade Review) — placeholder
            # preenchido na Fase F por outro executor.
            nota_media=None,
        )

    def search_public(
        self,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        raio_km: Optional[float] = None,
        sport_id: Optional[int] = None,
        amenities: Optional[list[str]] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Pagination[CompanySearchCardDTO]:
        """Busca pública da vitrine (`GET /companies`).

        Filtro por esporte é relacional (join via repository); raio/distância
        e comodidades são calculados em memória sobre os candidatos —
        Haversine em Python puro, sem PostGIS. Ordenação default por
        distância quando lat/lng são informados; senão, por nome.
        """
        companies = self.company_repository.search_public(
            sport_id=sport_id, name_like=q
        )

        candidates: list[tuple[Company, Optional[float]]] = []
        for company in companies:
            if amenities:
                company_amenities = set(company.amenities or [])
                if not set(amenities).issubset(company_amenities):
                    continue

            distance_km = None
            has_coordinates = (
                lat is not None
                and lng is not None
                and company.latitude is not None
                and company.longitude is not None
            )
            if has_coordinates:
                distance_km = _haversine_km(lat, lng, company.latitude, company.longitude)
                if raio_km is not None and distance_km > raio_km:
                    continue

            candidates.append((company, distance_km))

        if lat is not None and lng is not None:
            candidates.sort(key=lambda pair: (pair[1] is None, pair[1]))
        else:
            candidates.sort(key=lambda pair: pair[0].name.lower())

        total = len(candidates)
        start = (page - 1) * page_size
        page_items = candidates[start : start + page_size]
        total_pages = (total + page_size - 1) // page_size if page_size else 0

        return Pagination[CompanySearchCardDTO](
            items=[self._to_search_card(c, d) for c, d in page_items],
            total=total,
            total_filtered=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_detail(self, company_id: int) -> CompanyDetailDTO:
        company = self.get_by_id(company_id)
        active_courts = self._active_courts(company)
        return CompanyDetailDTO(
            **CompanyReadDTO.model_validate(company).model_dump(),
            courts=[CourtReadDTO.model_validate(c) for c in active_courts],
            nota_media=None,
        )

    @staticmethod
    def get_service(
        company_repository: CompanyRepository = Depends(
            CompanyRepository.get_instance()
        ),
    ) -> "CompanyService":
        return CompanyService(company_repository=company_repository)
