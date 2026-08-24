from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.rate_limit import LOGIN_ACCOUNT_RULE, REGISTER_IP_RULE
from app.services import auth_service, student_service


def test_request_body_limit_rejects_oversized_payload(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        content=b"x" * (settings.max_request_body_bytes + 1),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "Request body too large"}


def test_login_rejects_oversized_identifier_before_authentication(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def should_not_authenticate(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("authentication should not be attempted")

    monkeypatch.setattr(auth_service, "authenticate_user", should_not_authenticate)
    response = client.post(
        "/api/auth/login",
        data={"username": "a" * 255, "password": "valid-length-password"},
    )
    assert response.status_code == 422
    assert called is False


def test_failed_login_is_rate_limited_by_account(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject(*args, **kwargs):
        raise auth_service.InvalidCredentialsError

    monkeypatch.setattr(auth_service, "authenticate_user", reject)
    payload = {"username": "target@example.com", "password": "wrong-password-value"}

    for _ in range(LOGIN_ACCOUNT_RULE.limit):
        response = client.post("/api/auth/login", data=payload)
        assert response.status_code == 401

    blocked = client.post("/api/auth/login", data=payload)
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1


def test_registration_is_rate_limited_by_ip(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def duplicate(*args, **kwargs):
        raise student_service.StudentAlreadyExistsError

    monkeypatch.setattr(student_service, "create_student", duplicate)
    payload = {
        "email": "rate-limit@example.com",
        "password": "a-secure-password",
        "student_id": "STRATE01",
        "first_name": "Rate",
        "last_name": "Limit",
    }

    for _ in range(REGISTER_IP_RULE.limit):
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 409

    blocked = client.post("/api/auth/register", json=payload)
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1


def test_room_and_booking_inputs_have_resilience_bounds(client: TestClient) -> None:
    long_window = client.get(
        "/api/rooms/available",
        params={"start_date": "2026-01-01", "end_date": "2029-01-01"},
    )
    assert long_window.status_code == 422


def test_render_uses_trusted_cf_connecting_ip_for_rate_limits(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RENDER", "true")
    from app.api.routes.auth import _client_ip

    # Starlette Request is needed because httpx.Request does not expose .client.
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/health",
        "headers": [
            (b"cf-connecting-ip", b"203.0.113.42"),
            (b"x-forwarded-for", b"198.51.100.9"),
        ],
        "client": ("10.0.0.8", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "query_string": b"",
        "root_path": "",
        "http_version": "1.1",
    }
    assert _client_ip(Request(scope)) == "203.0.113.42"


def test_non_render_ignores_forwarding_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RENDER", raising=False)
    from app.api.routes.auth import _client_ip
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/health",
        "headers": [(b"cf-connecting-ip", b"203.0.113.42")],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "query_string": b"",
        "root_path": "",
        "http_version": "1.1",
    }
    assert _client_ip(Request(scope)) == "127.0.0.1"
