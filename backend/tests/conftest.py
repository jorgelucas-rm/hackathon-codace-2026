"""Base de testes compartilhada por todos os executores (Onda 0).

Banco descartável: usa o mesmo servidor Postgres do docker-compose (já
disponível em DATABASE_HOST/PORT) mas com um database dedicado
(`<POSTGRES_DB>_test`), criado automaticamente se não existir. Tabelas são
criadas uma vez por sessão de teste e truncadas após cada teste (autouse) —
isolamento sem o custo de recriar o schema a cada teste.

Convenções para quem escreve testes de fase (T-A1..T-F):
- Use o fixture `client` para bater na API via HTTP (TestClient) — é o que a
  maioria dos testes de rota deve usar.
- Use `db_session` para inspecionar/preparar estado direto no banco quando o
  teste precisar ir além do que a API expõe.
- Use `create_user`/`create_company` (factories) para variações customizadas,
  ou os atalhos prontos `auth_user`/`auth_company` (usuário e empresa já
  autenticados, com headers Bearer prontos).
- Corrida pelo mesmo slot/vaga: não é necessário thread real — chame o
  service/rota duas vezes em sequência (a segunda deve ver o estado
  já commitado pela primeira) e valide o 409 (`SLOT_UNAVAILABLE`/`GROUP_FULL`).
  O lock (`SELECT ... FOR UPDATE`) protege concorrência real; o teste
  sequencial valida a regra de negócio.
"""

import os
import sys
import uuid
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Precisa ser setado antes do primeiro import de `src.environments` (lido na
# importação do módulo). load_dotenv() não sobrescreve env vars já setadas.
os.environ.setdefault("POSTGRES_DB", os.getenv("POSTGRES_DB", "codace") + "_test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.app.main import app
from src.app.model.entity import BaseModel
from src.app.model.entity.company import Company
from src.app.model.entity.user import User
from src.app.model.enum import AuthType, Level
from src.environments import DATABASE_URL
from src.infra.security import hash_password
from src.infra.security.jwt_service import JWTService
from src.infra.storage import get_session


def _ensure_test_database() -> None:
    db_name = DATABASE_URL.rsplit("/", 1)[1]
    admin_url = DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        admin_engine.dispose()


_ensure_test_database()

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    BaseModel.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.begin() as conn:
        for table in reversed(BaseModel.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def _override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@test.com"


@pytest.fixture()
def create_user(db_session):
    def _create(**overrides) -> User:
        defaults = dict(
            name="Test User",
            email=_unique_email("user"),
            password=hash_password("Str0ng!Pass1"),
            role=Level.USER,
        )
        defaults.update(overrides)
        user = User(**defaults)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create


@pytest.fixture()
def create_company(db_session):
    def _create(**overrides) -> Company:
        defaults = dict(
            cnpj=f"{uuid.uuid4().int % 10**14:014d}",
            name="Test Company",
            email=_unique_email("company"),
            password=hash_password("Str0ng!Pass1"),
            street="Rua Teste",
            number="100",
            neighborhood="Centro",
            city="São Paulo",
            state="SP",
            zip_code="01000000",
        )
        defaults.update(overrides)
        company = Company(**defaults)
        db_session.add(company)
        db_session.commit()
        db_session.refresh(company)
        return company

    return _create


def auth_headers_for_user(user: User) -> dict:
    token = JWTService.create_access_token(
        sub=user.id, level=user.role.value, auth_type=AuthType.USER.value
    )
    return {"Authorization": f"Bearer {token}"}


def auth_headers_for_company(company: Company) -> dict:
    token = JWTService.create_access_token(
        sub=company.id, level=Level.COMPANY.value, auth_type=AuthType.COMPANY.value
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_user(create_user):
    user = create_user()
    return user, auth_headers_for_user(user)


@pytest.fixture()
def auth_company(create_company):
    company = create_company()
    return company, auth_headers_for_company(company)
