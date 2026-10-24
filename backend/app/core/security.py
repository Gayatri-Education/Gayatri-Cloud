"""Cryptographic security utilities: password hashing and JWT management."""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

# Security parameters
SALT_BYTES = 32


def get_pbkdf2_iterations() -> int:
    """Return iteration count (reduced for testing speed, 600_000 in production)."""
    return 10_000 if settings.is_testing else 600_000


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = os.urandom(SALT_BYTES)
    iterations = get_pbkdf2_iterations()
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    # Store format: algorithm$iterations$salt_hex$hash_hex
    return f"pbkdf2_sha256${iterations}${salt.hex()}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored PBKDF2 hash using constant-time comparison."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False

        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = bytes.fromhex(parts[3])

        computed_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return secrets.compare_digest(computed_hash, expected_hash)
    except Exception:
        return False


def hash_token(token: str) -> str:
    """Compute SHA-256 hash of a refresh token for safe database persistence."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_jwt_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str = "access",
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT token with standard claims and bounded lifetime."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": secrets.token_hex(16),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: str, email: str, is_super_admin: bool = False) -> str:
    """Generate short-lived access token."""
    return create_jwt_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
        extra_claims={"email": email, "is_super_admin": is_super_admin},
    )


def create_refresh_token(user_id: str) -> str:
    """Generate long-lived session refresh token."""
    return create_jwt_token(
        subject=user_id,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def decode_jwt_token(token: str) -> dict[str, Any] | None:
    """Decode and verify signature and expiry of a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["sub", "exp", "type"]},
        )
        return payload
    except jwt.PyJWTError:
        return None


# --- AES-256-GCM Credential Encryption & Masking ---


def _get_encryption_key() -> bytes:
    """Derive a 256-bit symmetric encryption key from settings.SECRET_KEY."""
    return hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()


def encrypt_credential(secret_text: str) -> str:
    """Encrypt secret credential using AES-256-GCM with a random 12-byte nonce."""
    key = _get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, secret_text.encode("utf-8"), None)
    return f"{nonce.hex()}${ciphertext.hex()}"


def decrypt_credential(ciphertext_payload: str) -> str:
    """Decrypt AES-256-GCM ciphertext payload."""
    try:
        parts = ciphertext_payload.split("$")
        if len(parts) != 2:
            raise ValueError("Malformed ciphertext format.")
        nonce = bytes.fromhex(parts[0])
        ciphertext = bytes.fromhex(parts[1])
        key = _get_encryption_key()
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as err:
        raise ValueError("Failed to decrypt credential.") from err


def mask_credential(secret_text: str) -> str:
    """Mask secret key for safe display, revealing only prefix and last 4 characters."""
    if len(secret_text) <= 8:
        return "..." + secret_text[-2:] if len(secret_text) >= 2 else "..."
    prefix = secret_text[:3]
    suffix = secret_text[-4:]
    return f"{prefix}...{suffix}"


def compute_key_fingerprint(secret_text: str) -> str:
    """Generate SHA-256 fingerprint for credential identification."""
    return hashlib.sha256(secret_text.encode("utf-8")).hexdigest()
