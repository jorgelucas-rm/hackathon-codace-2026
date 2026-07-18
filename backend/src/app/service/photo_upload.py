"""Validação/upload/resolução de fotos — compartilhado entre `user_service`
(avatar), `company_service` e `court_service` para não duplicar a mesma
lógica 3x. Mesmo padrão já usado pelo avatar: a coluna guarda a *object key*,
nunca a URL; a resolução pra URL pré-assinada só acontece na hora de montar o
DTO de leitura."""

from uuid import uuid4

from fastapi import UploadFile

from src.app.adapter import MinioAdapter
from src.app.model.enum import ErrorCode
from src.infra.exception import BadRequestException

MAX_PHOTO_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_PHOTO_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
}


def validate_and_upload_photo(
    minio_adapter: MinioAdapter, file: UploadFile, object_prefix: str
) -> str:
    """Valida content-type/tamanho e sobe o arquivo pro bucket. Retorna a
    object key gerada (`{object_prefix}{uuid}{extensao}`)."""
    extension = ALLOWED_PHOTO_CONTENT_TYPES.get(file.content_type)
    if not extension:
        raise BadRequestException(
            error_type="Invalid photo file type",
            details=f"Allowed types: {', '.join(ALLOWED_PHOTO_CONTENT_TYPES)}",
            error_code=ErrorCode.INVALID_FILE_TYPE,
        )

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_PHOTO_SIZE_BYTES:
        raise BadRequestException(
            error_type="Photo file too large",
            details=f"Max size is {MAX_PHOTO_SIZE_BYTES // (1024 * 1024)}MB",
            error_code=ErrorCode.FILE_TOO_LARGE,
        )

    object_name = f"{object_prefix}{uuid4().hex}{extension}"
    minio_adapter.upload_file_to_minio(file=file, object_name=object_name)
    return object_name


def resolve_photo_urls(minio_adapter: MinioAdapter, keys: list[str]) -> list[str]:
    """Resolve uma lista de object keys pra URLs pré-assinadas. Keys que não
    existem mais no bucket (ex.: removidas manualmente) são silenciosamente
    descartadas em vez de derrubar a resposta com 500/404."""
    if not keys:
        return []
    urls = minio_adapter.get_files_from_minio(keys)
    return [urls[key] for key in keys if urls.get(key)]


def resolve_single_photo_url(minio_adapter: MinioAdapter, key: str | None) -> str | None:
    if not key:
        return None
    return minio_adapter.get_files_from_minio([key]).get(key)
