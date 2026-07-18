import os
from pathlib import Path

from dotenv import load_dotenv

# Caminho absoluto: garante que o .env é encontrado independente do cwd de
# onde o processo é iniciado (uvicorn, alembic, pytest, docker).
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")


def get_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is not set")
    return value


def get_env_default(name: str, default: str) -> str:
    return os.getenv(name, default)


############### SECURITY CONFIG ###############
JWT_SECRET = get_env("JWT_SECRET")
JWT_ALGORITHM = get_env("JWT_ALGORITHM")
JWT_TOKEN_EXPIRE = get_env("JWT_TOKEN_EXPIRE")

############### DATABASE CONN ###############
DATABASE_HOST = get_env("DATABASE_HOST")
DATABASE_PORT = get_env("DATABASE_PORT")
DATABASE_NAME = get_env("POSTGRES_DB")
DATABASE_USER = get_env("POSTGRES_USER")
DATABASE_PASSWORD = get_env("POSTGRES_PASSWORD")
DATABASE_URL = f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

############### FRONTEND ###############
FRONTEND_URL = get_env("FRONTEND_URL")

############### MINIO CONN (object storage) ###############
MINIO_HOST = get_env("MINIO_HOST")
MINIO_ROOT_USER = get_env("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = get_env("MINIO_ROOT_PASSWORD")
MINIO_SECURE = get_env("MINIO_SECURE")
MINIO_DEFAULT_BUCKET = get_env("MINIO_DEFAULT_BUCKET")
MINIO_PUBLIC_HOST = get_env("MINIO_PUBLIC_HOST")
MINIO_PUBLIC_SECURE = get_env("MINIO_PUBLIC_SECURE")

############### MARKETPLACE BUSINESS RULES (MVP) ###############
# Defaults sensatos via get_env_default: não quebram o compose se ausentes do .env.
PAYMENT_TTL_MINUTES = int(get_env_default("PAYMENT_TTL_MINUTES", "15"))
REFUND_DEADLINE_HOURS = int(get_env_default("REFUND_DEADLINE_HOURS", "24"))
PLATFORM_FEE_PCT = int(get_env_default("PLATFORM_FEE_PCT", "10"))
GATEWAY_FEE_PCT = int(get_env_default("GATEWAY_FEE_PCT", "2"))
GROUP_RISK_HOURS = int(get_env_default("GROUP_RISK_HOURS", "6"))
REMINDER_HOURS = int(get_env_default("REMINDER_HOURS", "2"))
SEED_DEMO = get_env_default("SEED_DEMO", "false").lower() in ("1", "true", "yes")
