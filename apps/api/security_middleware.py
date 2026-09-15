"""
security_middleware.py — OWASP API Security Headers Middleware.

Injects hardened HTTP headers on every response to satisfy OWASP Top 10 security standards:
- Defense against clickjacking (X-Frame-Options: DENY)
- Prevention of MIME-type sniffing (X-Content-Type-Options: nosniff)
- Strict Transport Security (HSTS)
- Strict Content Security Policy (CSP)
- Permissions policy scoping microphone access strictly to self for LiveKit
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Apply OWASP API Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        return response
