from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import User
from tests.helpers import bearer, create_admin, login_admin, register_and_login_student, register_student


def test_registration_hashes_password(client: TestClient, db_session: Session) -> None:
    payload = register_student(client, "40001", "correct-horse-battery-staple")
    assert payload["student_id"] == "ST40001"
    assert "password" not in payload

    user = db_session.scalar(select(User).where(User.email == "student40001@example.com"))
    assert user is not None
    assert user.password_hash != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", user.password_hash)


def test_duplicate_registration_returns_409(client: TestClient) -> None:
    register_student(client, "40002")
    response = client.post(
        "/api/auth/register",
        json={
            "email": "student40002@example.com",
            "password": "a-secure-password",
            "student_id": "ST40002",
            "first_name": "Again",
            "last_name": "Duplicate",
        },
    )
    assert response.status_code == 409


def test_login_and_me_for_student(client: TestClient) -> None:
    student, token = register_and_login_student(client, "40003")
    response = client.get("/api/auth/me", headers=bearer(token))
    assert response.status_code == 200
    assert response.json()["role"] == "student"
    assert response.json()["student"]["student_id"] == student["student_id"]


def test_login_rejects_wrong_password(client: TestClient) -> None:
    register_student(client, "40004")
    response = client.post(
        "/api/auth/login",
        data={"username": "student40004@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_protected_endpoint_rejects_missing_and_invalid_token(client: TestClient) -> None:
    assert client.get("/api/students/me").status_code == 401
    assert client.get("/api/students/me", headers=bearer("not-a-jwt")).status_code == 401


def test_admin_login_and_me(client: TestClient, db_session: Session) -> None:
    create_admin(db_session)
    token = login_admin(client)
    response = client.get("/api/auth/me", headers=bearer(token))
    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert response.json()["student"] is None
