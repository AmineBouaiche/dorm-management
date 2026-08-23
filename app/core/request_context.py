from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send


REQUEST_ID_HEADER = b"x-request-id"
REQUEST_LOGGER = logging.getLogger("dorm_management.requests")


class RequestIDMiddleware:
    """Assign a non-sensitive correlation ID to every HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _incoming_request_id(scope) or uuid.uuid4().hex
        state: dict[str, Any] = scope.setdefault("state", {})
        state["request_id"] = request_id
        started = time.perf_counter()
        status_code = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            REQUEST_LOGGER.info(
                "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
                request_id,
                scope.get("method", "UNKNOWN"),
                scope.get("path", ""),
                status_code,
                duration_ms,
            )


def _incoming_request_id(scope: Scope) -> str | None:
    for name, value in scope.get("headers", []):
        if name.lower() != REQUEST_ID_HEADER:
            continue
        try:
            candidate = value.decode("ascii").strip()
        except UnicodeDecodeError:
            return None
        if 1 <= len(candidate) <= 64 and all(ch.isalnum() or ch in "-_." for ch in candidate):
            return candidate
        return None
