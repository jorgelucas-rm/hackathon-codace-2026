import threading

from minio import Minio

from src.environments.constants import (
    MINIO_HOST,
    MINIO_PUBLIC_HOST,
    MINIO_PUBLIC_SECURE,
    MINIO_ROOT_PASSWORD,
    MINIO_ROOT_USER,
    MINIO_SECURE,
)


class _MinioClient:
    """Client usado para operações internas (upload, delete, gestão de bucket).

    Conecta no host interno do MinIO, nunca exposto em URLs pré-assinadas.
    """

    _instance: Minio | None = None
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> Minio:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = Minio(
                        endpoint=MINIO_HOST,
                        access_key=MINIO_ROOT_USER,
                        secret_key=MINIO_ROOT_PASSWORD,
                        secure=MINIO_SECURE.lower() == "true",
                    )
        return cls._instance


class _MinioPresignClient:
    """Client usado exclusivamente para gerar URLs pré-assinadas.

    Configurado com o host público para que as URLs geradas sejam acessíveis
    externamente. A região é fixa para evitar uma consulta DNS ao host
    público a partir de dentro da rede do container.
    """

    _instance: Minio | None = None
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> Minio:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = Minio(
                        endpoint=MINIO_PUBLIC_HOST,
                        access_key=MINIO_ROOT_USER,
                        secret_key=MINIO_ROOT_PASSWORD,
                        secure=MINIO_PUBLIC_SECURE.lower() == "true",
                        region="us-east-1",
                    )
        return cls._instance


def get_minio_client() -> Minio:
    return _MinioClient.get_instance()


def get_minio_presign_client() -> Minio:
    return _MinioPresignClient.get_instance()
