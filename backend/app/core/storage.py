"""Object Storage Abstraction Layer and Content Validation Engine."""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.config import settings

# Supported MIME types and extensions
ALLOWED_MIME_TYPES = {
    "application/pdf": [".pdf"],
    "text/plain": [".txt", ".text"],
    "text/markdown": [".md", ".markdown"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/webp": [".webp"],
    "text/vtt": [".vtt"],
}

# Magic byte signatures for deep content sniffing
MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    "application/pdf": [b"%PDF-"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [b"PK\x03\x04"],
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": [b"PK\x03\x04"],
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit


class StorageService(ABC):
    """Abstract interface for object storage implementations."""

    @abstractmethod
    def upload_file(self, content: bytes, storage_path: str, content_type: str) -> str:
        """Upload raw binary bytes to the given storage path and return the storage URI."""
        pass

    @abstractmethod
    def download_file(self, storage_path: str) -> bytes:
        """Download binary content from the given storage path."""
        pass

    @abstractmethod
    def file_exists(self, storage_path: str) -> bool:
        """Check whether a file exists at the given storage path."""
        pass

    @abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        """Delete file at the given storage path."""
        pass

    @abstractmethod
    def generate_presigned_download_url(
        self, storage_path: str, expires_in_seconds: int = 3600
    ) -> str:
        """Generate a short-lived download URL for authorized client retrieval."""
        pass


class LocalStorageAdapter(StorageService):
    """Deterministic local filesystem storage adapter for development and testing."""

    def __init__(self, base_directory: str | None = None) -> None:
        self.base_dir = Path(base_directory or settings.LOCAL_STORAGE_PATH).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, storage_path: str) -> Path:
        """Enforce strict containment within the base directory to prevent path traversal."""
        # Normalize and remove leading slashes
        clean_rel_path = os.path.normpath(storage_path).lstrip("/\\")
        target_path = (self.base_dir / clean_rel_path).resolve()

        # Path traversal guard
        try:
            target_path.relative_to(self.base_dir)
        except ValueError as err:
            raise ValueError(f"Path traversal attempt detected: {storage_path}") from err

        return target_path

    def upload_file(self, content: bytes, storage_path: str, content_type: str) -> str:
        target_path = self._resolve_safe_path(storage_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)
        return f"local://{storage_path.lstrip('/')}"

    def download_file(self, storage_path: str) -> bytes:
        target_path = self._resolve_safe_path(storage_path)
        if not target_path.exists() or not target_path.is_file():
            raise FileNotFoundError(f"File not found in local storage: {storage_path}")
        return target_path.read_bytes()

    def file_exists(self, storage_path: str) -> bool:
        try:
            target_path = self._resolve_safe_path(storage_path)
            return target_path.exists() and target_path.is_file()
        except ValueError:
            return False

    def delete_file(self, storage_path: str) -> bool:
        target_path = self._resolve_safe_path(storage_path)
        if target_path.exists() and target_path.is_file():
            target_path.unlink()
            return True
        return False

    def generate_presigned_download_url(
        self, storage_path: str, expires_in_seconds: int = 3600
    ) -> str:
        # Generates local download URI format
        clean_path = storage_path.lstrip("/")
        return f"/api/v1/courses/sources/files/{clean_path}?expires={expires_in_seconds}"


class S3StorageAdapter(StorageService):
    """Production AWS S3 storage adapter with private ACLs and server-side encryption."""

    def __init__(
        self,
        bucket_name: str | None = None,
        region: str | None = None,
    ) -> None:
        self.bucket = bucket_name or settings.AWS_S3_BUCKET
        self.region = region or settings.AWS_REGION
        self._s3_client: Any = None

    def _get_client(self) -> Any:
        if self._s3_client is None:
            try:
                import boto3  # type: ignore[import-untyped]
                from botocore.config import Config  # type: ignore[import-untyped]

                self._s3_client = boto3.client(
                    "s3",
                    region_name=self.region,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    config=Config(signature_version="s3v4"),
                )
            except ImportError as err:
                raise RuntimeError(
                    "boto3 is required for S3StorageAdapter but is not installed."
                ) from err
        return self._s3_client

    def upload_file(self, content: bytes, storage_path: str, content_type: str) -> str:
        client = self._get_client()
        key = storage_path.lstrip("/")
        client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )
        return f"s3://{self.bucket}/{key}"

    def download_file(self, storage_path: str) -> bytes:
        client = self._get_client()
        key = storage_path.lstrip("/")
        res = client.get_object(Bucket=self.bucket, Key=key)
        return res["Body"].read()

    def file_exists(self, storage_path: str) -> bool:
        client = self._get_client()
        key = storage_path.lstrip("/")
        try:
            client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def delete_file(self, storage_path: str) -> bool:
        client = self._get_client()
        key = storage_path.lstrip("/")
        client.delete_object(Bucket=self.bucket, Key=key)
        return True

    def generate_presigned_download_url(
        self, storage_path: str, expires_in_seconds: int = 3600
    ) -> str:
        client = self._get_client()
        key = storage_path.lstrip("/")
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in_seconds,
        )


_storage_singleton: StorageService | None = None


def get_storage_service() -> StorageService:
    """Dependency / Factory to obtain the active storage service."""
    global _storage_singleton
    if _storage_singleton is None:
        if settings.STORAGE_BACKEND == "s3":
            _storage_singleton = S3StorageAdapter()
        else:
            _storage_singleton = LocalStorageAdapter()
    return _storage_singleton


def validate_file_content(content: bytes, filename: str, declared_mime_type: str) -> None:
    """Perform strict content validation, size enforcement, and magic-byte sniff checks."""
    # 1. Size Check
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File size ({len(content)} bytes) exceeds maximum limit of {MAX_FILE_SIZE_BYTES} bytes."
        )

    if len(content) == 0:
        raise ValueError("File content is empty.")

    # 2. MIME Type Allowlist Check
    if declared_mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"MIME type '{declared_mime_type}' is not supported. Allowed: {list(ALLOWED_MIME_TYPES.keys())}"
        )

    # 3. Extension Match Check
    ext = Path(filename).suffix.lower()
    allowed_exts = ALLOWED_MIME_TYPES[declared_mime_type]
    if ext not in allowed_exts:
        raise ValueError(
            f"File extension '{ext}' does not match declared MIME type '{declared_mime_type}' (expected {allowed_exts})."
        )

    # 4. Deep Inspection / Magic Byte Check (MIME Spoofing Protection)
    if declared_mime_type in MAGIC_SIGNATURES:
        valid_signatures = MAGIC_SIGNATURES[declared_mime_type]
        if not any(content.startswith(sig) for sig in valid_signatures):
            raise ValueError(
                f"Content verification failed: Binary signature does not match '{declared_mime_type}'."
            )

    # Special check for WebP
    if declared_mime_type == "image/webp":
        if not (content.startswith(b"RIFF") and len(content) > 12 and content[8:12] == b"WEBP"):
            raise ValueError(
                "Content verification failed: Binary signature does not match WebP image."
            )

    # Special check for plain text / markdown / vtt (ensure valid UTF-8 and no null bytes)
    if declared_mime_type in {"text/plain", "text/markdown", "text/vtt"}:
        if b"\x00" in content:
            raise ValueError("Binary executable/null characters detected in text source.")
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as err:
            raise ValueError("Text content could not be decoded as UTF-8.") from err


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and invalid characters."""
    base = os.path.basename(filename)
    # Strip any non-alphanumeric, underscore, dash, dot characters
    cleaned = re.sub(r"[^\w\.-]", "_", base)
    if not cleaned or cleaned.startswith("."):
        cleaned = f"file_{cleaned}"
    return cleaned
