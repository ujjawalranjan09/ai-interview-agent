"""S3/MinIO file storage client using boto3."""

import io
import logging

import boto3
from botocore.config import Config as BotoConfig

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=BotoConfig(
                signature_version="s3v4",
                connect_timeout=3,
                read_timeout=3,
                retries={"max_attempts": 0},
            ),
        )
    return _client


def upload_file(file_bytes: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    client = _get_client()
    client.upload_fileobj(
        io.BytesIO(file_bytes),
        settings.S3_BUCKET,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    logger.info("Uploaded %s to s3://%s/%s", content_type, settings.S3_BUCKET, key)
    return key


def get_presigned_url(key: str, expires_seconds: int = 3600) -> str:
    client = _get_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=expires_seconds,
    )


def delete_file(key: str) -> None:
    client = _get_client()
    client.delete_object(Bucket=settings.S3_BUCKET, Key=key)


def download_file(key: str) -> bytes:
    client = _get_client()
    buf = io.BytesIO()
    client.download_fileobj(settings.S3_BUCKET, key, buf)
    return buf.getvalue()
