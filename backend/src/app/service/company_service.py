import math
from typing import Optional

from fastapi import Depends, UploadFile

from src.app.adapter import MinioAdapter
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
from src.app.repository.review_repository import ReviewRepository
from src.app.service.photo_upload import (
    resolve_photo_urls,
    resolve_single_photo_url,
    validate_and_upload_photo,
)
from src.infra.exception import ConflictException, NotFoundException
from src.infra.security import hash_password

COMPANY_PHOTO_OBJECT_PREFIX = "company/"

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

    def __init__(
        self,
        company_repository: CompanyRepository,
        minio_adapter: MinioAdapter,
        review_repository: Optional[ReviewRepository] = None,
    ):
        self.company_repository = company_repository
        self.minio_adapter = minio_adapter
        # Fase F (T-F, extensão aditiva autorizada): opcional para não
        # quebrar quem já injeta `CompanyService` diretamente (fora do
        # `get_service`) sem passar esse novo parâmetro.
        self.review_repository = review_repository

    def to_read_dto(self, company: Company) -> CompanyReadDTO:
        """`photos` sempre expõe URLs pré-assinadas resolvidas na hora — as
        object keys no bucket nunca são expostas pela API (mesmo padrão de
        `UserService.to_read_dto` pro avatar)."""
        dto = CompanyReadDTO.model_validate(company)
        dto.photos = resolve_photo_urls(self.minio_adapter, company.photos or [])
        return dto

    def _nota_media(self, company_id: int) -> Optional[float]:
        if self.review_repository is None:
            return None
        average, count = self.review_repository.get_average_and_count(company_id)
        if count == 0 or average is None:
            return None
        return round(average, 2)

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
            items=[self.to_read_dto(i) for i in items],
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
        cover_photo = resolve_single_photo_url(
            self.minio_adapter, company.photos[0] if company.photos else None
        )
        return CompanySearchCardDTO(
            id=company.id,
            name=company.name,
            cover_photo=cover_photo,
            distance_km=round(distance_km, 2) if distance_km is not None else None,
            min_price_hour=min_price_hour,
            nota_media=self._nota_media(company.id),
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
        courts = []
        for court in active_courts:
            court_dto = CourtReadDTO.model_validate(court)
            court_dto.photos = resolve_photo_urls(self.minio_adapter, court.photos or [])
            courts.append(court_dto)
        return CompanyDetailDTO(
            **self.to_read_dto(company).model_dump(),
            courts=courts,
            nota_media=self._nota_media(company.id),
        )

    def add_photo(self, company_id: int, file: UploadFile) -> Company:
        company = self.get_by_id(company_id)
        object_name = validate_and_upload_photo(
            self.minio_adapter, file, object_prefix=f"{COMPANY_PHOTO_OBJECT_PREFIX}{company_id}/"
        )
        company.photos = [*(company.photos or []), object_name]
        return self.company_repository.save(entity=company)

    def remove_photo(self, company_id: int, index: int) -> Company:
        company = self.get_by_id(company_id)
        photos = list(company.photos or [])
        if index < 0 or index >= len(photos):
            raise NotFoundException(resource="Photo", error_code=ErrorCode.NOT_FOUND)

        object_name = photos.pop(index)
        company.photos = photos
        company = self.company_repository.save(entity=company)
        self.minio_adapter.delete_file_from_minio(object_name=object_name)
        return company

    @staticmethod
    def get_service(
        company_repository: CompanyRepository = Depends(
            CompanyRepository.get_instance()
        ),
        review_repository: ReviewRepository = Depends(
            ReviewRepository.get_instance()
        ),
        minio_adapter: MinioAdapter = Depends(MinioAdapter.get_instance),
    ) -> "CompanyService":
        return CompanyService(
            company_repository=company_repository,
            review_repository=review_repository,
            minio_adapter=minio_adapter,
        )
