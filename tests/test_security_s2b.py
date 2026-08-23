from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.main import create_app
from tests.helpers import bearer, create_admin, create_room, login_admin


def test_collection_pagination_is_bounded_and_exposes_headers(
    client: TestClient,
    db_session: Session,
) -> None:
    create_admin(db_session)
    create_room(db_session, "Pagination Hall A", "101")
    create_room(db_session, "Pagination Hall B", "102")
    create_room(db_session, "Pagination Hall C", "103")
    token = login_admin(client)

    response = client.get(
        "/api/admin/rooms?page=1&per_page=2",
        headers=bearer(token),
    )
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.headers["X-Page"] == "1"
    assert response.headers["X-Per-Page"] == "2"
    assert response.headers["X-Total-Count"] == "3"

    second_page = client.get(
        "/api/admin/rooms?page=2&per_page=2",
        headers=bearer(token),
    )
    assert second_page.status_code == 200
    assert len(second_page.json()) == 1


def test_invalid_pagination_is_rejected(client: TestClient, db_session: Session) -> None:
    create_admin(db_session)
    token = login_admin(client)
    assert client.get("/api/admin/bookings?page=0", headers=bearer(token)).status_code == 422
    assert (
        client.get("/api/admin/bookings?per_page=101", headers=bearer(token)).status_code
        == 422
    )


def test_request_id_header_is_present(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_valid_incoming_request_id_is_preserved(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "test-request-123"})
    assert response.headers["X-Request-ID"] == "test-request-123"


def test_production_unhandled_exception_is_generic() -> None:
    settings = Settings(
        environment="production",
        jwt_secret_key="x" * 48,
        database_url="postgresql+psycopg://unused:unused@localhost:5432/unused",
    )
    app: FastAPI = create_app(settings)

    @app.get("/__boom", include_in_schema=False)
    def boom() -> None:
        raise RuntimeError("database password=super-secret")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/__boom", headers={"X-Request-ID": "prod-test-1"})

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error",
        "request_id": "prod-test-1",
    }
    assert "super-secret" not in response.text
    assert response.headers["X-Request-ID"] == "prod-test-1"
