from typing import Union

from fastapi import Depends

from src.app.model.dto import (
    LoginCompany,
    LoginUser,
    MeCompanyReadDTO,
    MeUserReadDTO,
)
from src.app.model.dto.company import CompanyReadDTO
from src.app.model.dto.user import UserReadDTO
from src.app.model.enum import AuthType, ErrorCode, Level
from src.app.repository import CompanyRepository, UserRepository
from src.infra.context import RequestContext
from src.infra.exception import NotFoundException, UnauthorizedException
from src.infra.security import JWTService, verify_password


class AuthService:
    """Serviço responsável pela autenticação de usuários e empresas."""

    def __init__(
        self,
        user_repository: UserRepository,
        company_repository: CompanyRepository,
    ):
        self.user_repository = user_repository
        self.company_repository = company_repository

    def user_login(self, login: LoginUser) -> str:
        """Autentica um usuário pelo e-mail e senha, retornando um token JWT."""
        user = self.user_repository.get_by_email(login.email)

        if (
            not user
            or not user.situation
            or not verify_password(
                plain_password=login.password,
                hashed_password=user.password,
            )
        ):
            raise UnauthorizedException(
                message="Invalid credentials",
                error_code=ErrorCode.INVALID_CREDENTIALS,
            )

        return JWTService.create_access_token(
            sub=user.id,
            level=user.role.value,
            auth_type=AuthType.USER.value,
        )

    def company_login(self, login: LoginCompany) -> str:
        """Autentica uma empresa pelo CNPJ e senha, retornando um token JWT."""
        company = self.company_repository.get_by_cnpj(login.cnpj)

        if (
            not company
            or not company.situation
            or not verify_password(
                plain_password=login.password,
                hashed_password=company.password,
            )
        ):
            raise UnauthorizedException(
                message="Invalid credentials",
                error_code=ErrorCode.INVALID_CREDENTIALS,
            )

        return JWTService.create_access_token(
            sub=company.id,
            level=Level.COMPANY.value,
            auth_type=AuthType.COMPANY.value,
        )

    def get_me(self) -> Union[MeUserReadDTO, MeCompanyReadDTO]:
        """Retorna os dados do autenticado atual (usuário ou empresa) conforme o tipo do token."""
        auth_type = RequestContext.get_auth_type()

        handlers = {
            AuthType.USER: self._get_me_user,
            AuthType.COMPANY: self._get_me_company,
        }

        return handlers[auth_type]()

    def _get_me_user(self) -> MeUserReadDTO:
        auth = RequestContext.get_auth_user()
        user = self.user_repository.get_by_pk(pk=auth.user_id)

        if user is None:
            raise NotFoundException(resource="User", error_code=ErrorCode.NOT_FOUND)

        return MeUserReadDTO(entity=UserReadDTO.model_validate(user))

    def _get_me_company(self) -> MeCompanyReadDTO:
        auth = RequestContext.get_auth_company()
        company = self.company_repository.get_by_pk(pk=auth.company_id)

        if company is None:
            raise NotFoundException(resource="Company", error_code=ErrorCode.NOT_FOUND)

        return MeCompanyReadDTO(
            entity=CompanyReadDTO.model_validate(company),
        )

    @staticmethod
    def get_service(
        user_repository: UserRepository = Depends(UserRepository.get_instance()),
        company_repository: CompanyRepository = Depends(
            CompanyRepository.get_instance()
        ),
    ) -> "AuthService":
        return AuthService(
            user_repository=user_repository,
            company_repository=company_repository,
        )
