from fastapi import Depends

from src.app.model.dto.company import CompanyCreateDTO, CompanyReadDTO, CompanyUpdateDTO
from src.app.model.dto.pagination import Pagination
from src.app.model.entity.company import Company
from src.app.model.enum import ErrorCode
from src.app.repository.company_repository import CompanyRepository
from src.infra.exception import ConflictException, NotFoundException
from src.infra.security import hash_password


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

    @staticmethod
    def get_service(
        company_repository: CompanyRepository = Depends(
            CompanyRepository.get_instance()
        ),
    ) -> "CompanyService":
        return CompanyService(company_repository=company_repository)
