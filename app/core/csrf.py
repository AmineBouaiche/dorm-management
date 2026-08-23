import hmac
from collections.abc import Iterable

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
CSRF_EXEMPT_PATHS = {"/api/auth/login", "/api/auth/session", "/api/auth/register"}


class CSRFMiddleware:
    """Require a double-submit CSRF token for cookie-authenticated unsafe API requests."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET").upper()
        path = scope.get("path", "")
        if method in SAFE_METHODS or path in CSRF_EXEMPT_PATHS or not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        headers = _headers(scope.get("headers", []))
        cookies = _cookies(headers.get("cookie", ""))
        if settings.auth_cookie_name not in cookies:
            # Bearer-token API clients are not vulnerable to browser CSRF because
            # Authorization headers are not attached automatically cross-origin.
            await self.app(scope, receive, send)
            return

        cookie_token = cookies.get(settings.csrf_cookie_name, "")
        header_token = headers.get("x-csrf-token", "")
        if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
            response = JSONResponse({"detail": "CSRF validation failed"}, status_code=403)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def _headers(raw_headers: Iterable[tuple[bytes, bytes]]) -> dict[str, str]:
    return {key.decode("latin1").lower(): value.decode("latin1") for key, value in raw_headers}


def _cookies(raw_cookie: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for part in raw_cookie.split(";"):
        if "=" not in part:
            continue
        key, value = part.strip().split("=", 1)
        parsed[key] = value
    return parsed
