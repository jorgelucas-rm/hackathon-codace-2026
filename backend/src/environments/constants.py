import os

from dotenv import load_dotenv

load_dotenv()


def get_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is not set")
    return value


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
