"""Authentication Domain Service and Schemas."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models.identity import AuthIdentity, SessionDevice, UserAccount
from app.db.session import get_db

# --- Schemas ---


class UserRegisterRequest(BaseModel):
    """Schema for registering a new user."""

    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(min_length=2, max_length=255)


class UserLoginRequest(BaseModel):
    """Schema for user authentication."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for rotating a session refresh token."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Schema for JWT authentication response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class UserResponse(BaseModel):
    """Safe public user representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    is_super_admin: bool
    created_at: datetime


# --- Service ---


class AuthService:
    """Service orchestrating registration, authentication, and session control."""

    @staticmethod
    async def register_user(session: AsyncSession, req: UserRegisterRequest) -> UserAccount:
        """Register a new global user account with hashed credentials."""
        # 1. Check for existing active user
        normalized_email = req.email.lower().strip()
        existing = await session.execute(
            select(UserAccount).where(UserAccount.email == normalized_email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            )

        # 2. Create UserAccount
        user = UserAccount(
            email=normalized_email,
            full_name=req.full_name.strip(),
            is_active=True,
            is_verified=False,
            is_super_admin=False,
        )
        session.add(user)
        await session.flush()

        # 3. Create AuthIdentity with hashed password
        auth_identity = AuthIdentity(
            user_id=user.id,
            provider="email",
            credential_hash=hash_password(req.password),
            is_active=True,
        )
        session.add(auth_identity)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def authenticate_user(
        session: AsyncSession,
        req: UserLoginRequest,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """Authenticate user with constant-time resistance to user enumeration."""
        generic_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        normalized_email = req.email.lower().strip()
        res = await session.execute(
            select(UserAccount).where(UserAccount.email == normalized_email)
        )
        user = res.scalar_one_or_none()

        if not user or not user.is_active or user.is_deleted:
            # Constant-time dummy verify to mitigate timing attacks
            verify_password("dummy-pass", hash_password("dummy-pass"))
            raise generic_error

        # Retrieve password credential
        cred_res = await session.execute(
            select(AuthIdentity).where(
                AuthIdentity.user_id == user.id,
                AuthIdentity.provider == "email",
                AuthIdentity.is_active.is_(True),
            )
        )
        identity = cred_res.scalar_one_or_none()
        if not identity or not verify_password(req.password, identity.credential_hash):
            raise generic_error

        # Issue tokens
        access_token = create_access_token(user.id, user.email, user.is_super_admin)
        refresh_token = create_refresh_token(user.id)

        # Store session device with hashed refresh token
        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        session_device = SessionDevice(
            user_id=user.id,
            refresh_token_hash=hash_token(refresh_token),
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            is_revoked=False,
        )
        session.add(session_device)
        await session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    async def refresh_session(
        session: AsyncSession,
        refresh_token: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """Rotate session refresh token and generate new access token."""
        token_payload = decode_jwt_token(refresh_token)
        if not token_payload or token_payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        user_id = token_payload["sub"]
        token_digest = hash_token(refresh_token)

        # Verify active session device in database
        stmt = select(SessionDevice).where(
            SessionDevice.refresh_token_hash == token_digest,
            SessionDevice.user_id == user_id,
            SessionDevice.is_revoked.is_(False),
        )
        res = await session.execute(stmt)
        active_session = res.scalar_one_or_none()

        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired or was revoked.",
            )

        expires_at = (
            active_session.expires_at.replace(tzinfo=UTC)
            if active_session.expires_at.tzinfo is None
            else active_session.expires_at
        )
        if expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired or was revoked.",
            )

        # Invalidate old session device (token rotation)
        active_session.is_revoked = True
        await session.flush()

        # Retrieve user
        user_res = await session.execute(select(UserAccount).where(UserAccount.id == user_id))
        user = user_res.scalar_one_or_none()
        if not user or not user.is_active or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or disabled.",
            )

        # Issue new tokens
        new_access_token = create_access_token(user.id, user.email, user.is_super_admin)
        new_refresh_token = create_refresh_token(user.id)

        # Persist new session device
        new_device = SessionDevice(
            user_id=user.id,
            refresh_token_hash=hash_token(new_refresh_token),
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            is_revoked=False,
        )
        session.add(new_device)
        await session.commit()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    async def revoke_session(session: AsyncSession, refresh_token: str) -> bool:
        """Revoke an active refresh token session."""
        token_digest = hash_token(refresh_token)
        stmt = (
            update(SessionDevice)
            .where(SessionDevice.refresh_token_hash == token_digest)
            .values(is_revoked=True)
        )
        res = await session.execute(stmt)
        await session.commit()
        return res.rowcount > 0


# --- Dependency ---


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_db),
) -> UserAccount:
    """FastAPI dependency to extract and validate the current authenticated user."""
    auth_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not authorization or not authorization.startswith("Bearer "):
        raise auth_exception

    token = authorization.split(" ")[1]
    payload = decode_jwt_token(token)
    if not payload or payload.get("type") != "access":
        raise auth_exception

    user_id = payload.get("sub")
    if not user_id:
        raise auth_exception

    res = await session.execute(select(UserAccount).where(UserAccount.id == user_id))
    user = res.scalar_one_or_none()

    if not user or not user.is_active or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or disabled.",
        )

    return user
