from fastapi import Depends, UploadFile

from src.app.adapter import MinioAdapter
from src.app.model.dto.court import (
    CompanySummaryDTO,
    CourtCreateDTO,
    CourtDetailDTO,
    CourtReadDTO,
    CourtUpdateDTO,
)
from src.app.model.entity.court import Court
from src.app.model.entity.sport import Sport
from src.app.model.enum import ErrorCode
from src.app.repository.court_repository import CourtRepository
from src.app.repository.sport_repository import SportRepository
from src.app.service.photo_upload import resolve_photo_urls, validate_and_upload_photo
from src.infra.exception import ForbiddenException, NotFoundException

COURT_PHOTO_OBJECT_PREFIX = "court/"


class CourtService:

    def __init__(
        self,
        court_repository: CourtRepository,
        sport_repository: SportRepository,
        minio_adapter: MinioAdapter,
    ):
        self.court_repository = court_repository
        self.sport_repository = sport_repository
        self.minio_adapter = minio_adapter

    def to_read_dto(self, court: Court) -> CourtReadDTO:
        """`photos` sempre expõe URLs pré-assinadas resolvidas na hora — mesmo
        padrão de `UserService.to_read_dto`/`CompanyService.to_read_dto`."""
        dto = CourtReadDTO.model_validate(court)
        dto.photos = resolve_photo_urls(self.minio_adapter, court.photos or [])
        return dto

    def list_by_company(self, company_id: int) -> list[CourtReadDTO]:
        courts = self.court_repository.get_by_company(company_id)
        return [self.to_read_dto(c) for c in courts]

    def get_by_id(self, court_id: int) -> Court:
        court = self.court_repository.get_by_pk(pk=court_id)
        if not court:
            raise NotFoundException(resource="Court", error_code=ErrorCode.NOT_FOUND)
        return court

    def get_detail(self, court_id: int) -> CourtDetailDTO:
        court = self.get_by_id(court_id)
        return CourtDetailDTO(
            **self.to_read_dto(court).model_dump(),
            company=CompanySummaryDTO.model_validate(court.company),
        )

    def create(self, company_id: int, dto: CourtCreateDTO) -> Court:
        sports = self._resolve_sports(dto.sport_ids)
        court = Court(
            company_id=company_id,
            name=dto.name,
            capacity=dto.capacity,
            base_price_hour=dto.base_price_hour,
            sports=sports,
        )
        return self.court_repository.save(entity=court)

    def update(self, court_id: int, company_id: int, dto: CourtUpdateDTO) -> Court:
        court = self.get_by_id(court_id)

        if court.company_id != company_id:
            raise ForbiddenException(
                message="You do not own this court",
                error_code=ErrorCode.RESOURCE_NOT_OWNED,
            )

        data = dto.model_dump(exclude_unset=True, exclude={"sport_ids"})
        for field, value in data.items():
            setattr(court, field, value)

        if dto.sport_ids is not None:
            court.sports = self._resolve_sports(dto.sport_ids)

        return self.court_repository.save(entity=court)

    def add_photo(self, court_id: int, company_id: int, file: UploadFile) -> Court:
        court = self.get_by_id(court_id)
        if court.company_id != company_id:
            raise ForbiddenException(
                message="You do not own this court",
                error_code=ErrorCode.RESOURCE_NOT_OWNED,
            )

        object_name = validate_and_upload_photo(
            self.minio_adapter, file, object_prefix=f"{COURT_PHOTO_OBJECT_PREFIX}{court_id}/"
        )
        court.photos = [*(court.photos or []), object_name]
        return self.court_repository.save(entity=court)

    def remove_photo(self, court_id: int, company_id: int, index: int) -> Court:
        court = self.get_by_id(court_id)
        if court.company_id != company_id:
            raise ForbiddenException(
                message="You do not own this court",
                error_code=ErrorCode.RESOURCE_NOT_OWNED,
            )

        photos = list(court.photos or [])
        if index < 0 or index >= len(photos):
            raise NotFoundException(resource="Photo", error_code=ErrorCode.NOT_FOUND)

        object_name = photos.pop(index)
        court.photos = photos
        court = self.court_repository.save(entity=court)
        self.minio_adapter.delete_file_from_minio(object_name=object_name)
        return court

    def _resolve_sports(self, sport_ids: list[int]) -> list[Sport]:
        if not sport_ids:
            return []

        sports = self.sport_repository.get_by_ids(sport_ids)
        found_ids = {s.id for s in sports}
        missing = set(sport_ids) - found_ids
        if missing:
            raise NotFoundException(resource="Sport", error_code=ErrorCode.NOT_FOUND)
        return sports

    @staticmethod
    def get_service(
        court_repository: CourtRepository = Depends(CourtRepository.get_instance()),
        sport_repository: SportRepository = Depends(SportRepository.get_instance()),
        minio_adapter: MinioAdapter = Depends(MinioAdapter.get_instance),
    ) -> "CourtService":
        return CourtService(
            court_repository=court_repository,
            sport_repository=sport_repository,
            minio_adapter=minio_adapter,
        )
