"""Security Headers Middleware for ASGI / FastAPI.
Ensures every HTTP response contains hardened security headers according to OWASP guidelines.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects essential security headers into all outgoing HTTP responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # 1. Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 2. Prevent clickjacking / framing
        response.headers["X-Frame-Options"] = "DENY"

        # 3. Cross-Site Scripting protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 4. Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 5. Restrict permissions (camera, microphone, geolocation)
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # 6. Content Security Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"

        # 7. HSTS (HTTP Strict Transport Security)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
