import io
from datetime import timedelta

from fastapi import Depends, UploadFile
from minio import Minio, error

from src.app.model.enum import ErrorCode
from src.environments import MINIO_DEFAULT_BUCKET
from src.infra.exception import NotFoundException, StorageException
from src.infra.storage import get_minio_client, get_minio_presign_client


class MinioAdapter:
    def __init__(self, minio_client: Minio, minio_presign_client: Minio):
        self.minio_client = minio_client
        self.minio_presign_client = minio_presign_client

    def get_file_from_minio(self, object_name: str) -> str:
        try:
            url = self.minio_presign_client.presigned_get_object(
                bucket_name=MINIO_DEFAULT_BUCKET,
                object_name=object_name,
                expires=timedelta(minutes=30),
            )
            return url
        except error.S3Error as e:
            if e.code in ("NoSuchKey", "NoSuchBucket"):
                raise NotFoundException(resource="File", error_code=ErrorCode.NOT_FOUND)
            raise StorageException(message=f"Could not retrieve file: {e.message}")

    def get_files_from_minio(self, object_names: list[str]) -> dict[str, str | None]:
        urls: dict[str, str | None] = {}
        for object_name in object_names:
            try:
                urls[object_name] = self.minio_presign_client.presigned_get_object(
                    bucket_name=MINIO_DEFAULT_BUCKET,
                    object_name=object_name,
                    expires=timedelta(minutes=30),
                )
            except error.S3Error as e:
                if e.code in ("NoSuchKey", "NoSuchBucket"):
                    urls[object_name] = None
                else:
                    raise StorageException(
                        message=f"Could not retrieve file: {e.message}"
                    )
        return urls

    def delete_file_from_minio(self, object_name: str) -> None:
        try:
            self.minio_client.remove_object(
                bucket_name=MINIO_DEFAULT_BUCKET,
                object_name=object_name,
            )
        except error.S3Error as e:
            if e.code not in ("NoSuchKey", "NoSuchBucket"):
                raise StorageException(message=f"Could not delete file: {e.message}")

    def _ensure_bucket(self) -> None:
        if not self.minio_client.bucket_exists(MINIO_DEFAULT_BUCKET):
            self.minio_client.make_bucket(MINIO_DEFAULT_BUCKET)

    def upload_file_to_minio(
        self,
        file: UploadFile,
        object_name: str,
    ) -> str:
        self._ensure_bucket()

        content = file.file.read()
        content_type = file.content_type or "application/octet-stream"

        self.minio_client.put_object(
            bucket_name=MINIO_DEFAULT_BUCKET,
            object_name=object_name,
            data=io.BytesIO(content),
            length=len(content),
            content_type=content_type,
        )

        return object_name

    @staticmethod
    def get_instance(
        minio_client: Minio = Depends(get_minio_client),
        minio_presign_client: Minio = Depends(get_minio_presign_client),
    ) -> "MinioAdapter":
        return MinioAdapter(
            minio_client=minio_client, minio_presign_client=minio_presign_client
        )
