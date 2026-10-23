"""Authentication endpoints for User Registration, Login, Session Refresh, and Profile."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.identity import UserAccount
from app.db.session import get_db
from app.domain.auth import (
    AuthService,
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    get_current_user,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new personal user account",
)
async def register(
    req: UserRegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> UserAccount:
    """Create a new user account with email and password credentials."""
    return await AuthService.register_user(session, req)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT tokens",
)
async def login(
    req: UserLoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Verify credentials and return access and refresh tokens."""
    user_agent = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None
    return await AuthService.authenticate_user(session, req, user_agent, ip_address)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and issue new access token",
)
async def refresh_token(
    req: RefreshTokenRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Rotate session refresh token with replay prevention."""
    user_agent = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None
    return await AuthService.refresh_session(session, req.refresh_token, user_agent, ip_address)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke session refresh token",
)
async def logout(
    req: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Revoke session and invalidate refresh token."""
    await AuthService.revoke_session(session, req.refresh_token)
    return {"status": "ok", "message": "Session revoked successfully."}


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: UserAccount = Depends(get_current_user),
) -> UserAccount:
    """Return profile details for the authenticated user."""
    return current_user
