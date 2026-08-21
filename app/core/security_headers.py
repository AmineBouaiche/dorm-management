from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    """Attach conservative browser security headers to every HTTP response."""

    def __init__(self, app: ASGIApp, allow_swagger_assets: bool = False) -> None:
        self.app = app
        self.allow_swagger_assets = allow_swagger_assets

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                script_sources = "'self'"
                style_sources = "'self' https://fonts.googleapis.com"
                if self.allow_swagger_assets:
                    script_sources += " 'unsafe-inline' https://cdn.jsdelivr.net"
                    style_sources += " https://cdn.jsdelivr.net"

                content_security_policy = (
                    "default-src 'self'; "
                    f"script-src {script_sources}; "
                    f"style-src {style_sources}; "
                    "font-src 'self' https://fonts.gstatic.com; "
                    "img-src 'self' data: https://fastapi.tiangolo.com; "
                    "connect-src 'self'; "
                    "frame-ancestors 'none'; "
                    "base-uri 'self'; "
                    "form-action 'self'"
                )

                headers.extend(
                    [
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"strict-origin-when-cross-origin"),
                        (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                        (b"content-security-policy", content_security_policy.encode("ascii")),
                    ]
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
