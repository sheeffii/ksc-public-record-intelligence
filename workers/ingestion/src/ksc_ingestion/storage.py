"""Object storage for fetched artifacts.

Key scheme (docs/INGESTION.md):

    documents/<case_number>/<official version ref, "/" → "_">/<sha256>.pdf

The key contains the hash, so storing the same bytes twice is a no-op and two
different versions never collide. Objects are never overwritten.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import Protocol

from minio import Minio
from minio.error import S3Error

from ksc_api.config import Settings

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def storage_key(case_number: str, official_ref: str, sha256: str, extension: str = "pdf") -> str:
    safe_ref = _UNSAFE.sub("_", official_ref.replace("/", "_"))
    return f"documents/{case_number}/{safe_ref}/{sha256}.{extension}"


class ObjectStore(Protocol):
    def exists(self, key: str) -> bool: ...

    def put(self, key: str, data: bytes, content_type: str) -> None: ...


@dataclass
class InMemoryObjectStore:
    """For tests and dry runs."""

    objects: dict[str, bytes] = field(default_factory=dict)

    def exists(self, key: str) -> bool:
        return key in self.objects

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self.objects.setdefault(key, data)


class MinioObjectStore:
    def __init__(self, settings: Settings, *, bucket: str | None = None) -> None:
        self.bucket = bucket or settings.minio_bucket_documents
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self.bucket):
            self._client.make_bucket(self.bucket)

    def exists(self, key: str) -> bool:
        try:
            self._client.stat_object(self.bucket, key)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject", "NotFound"}:
                return False
            raise
        return True

    def put(self, key: str, data: bytes, content_type: str) -> None:
        if self.exists(key):
            return
        self._client.put_object(
            self.bucket, key, io.BytesIO(data), length=len(data), content_type=content_type
        )
