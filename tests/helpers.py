from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Building, Room, RoomType, User, UserRole


def register_student(
    client: TestClient,
    suffix: str,
    password: str = "a-secure-password",
) -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"student{suffix}@example.com",
            "password": password,
            "student_id": f"ST{suffix}",
            "first_name": "Test",
            "last_name": suffix,
        },
    )
    assert response.status_code == 201
    return response.json()


def login_student(
    client: TestClient,
    suffix: str,
    password: str = "a-secure-password",
) -> str:
    response = client.post(
        "/api/auth/login",
        data={"username": f"student{suffix}@example.com", "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def register_and_login_student(client: TestClient, suffix: str) -> tuple[dict, str]:
    student = register_student(client, suffix)
    token = login_student(client, suffix)
    return student, token


def create_admin(db: Session, email: str = "admin@example.com", password: str = "admin-password") -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
    )
    db.add(user)
    db.flush()
    return user


def login_admin(
    client: TestClient,
    email: str = "admin@example.com",
    password: str = "admin-password",
) -> str:
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_room(db: Session, building_name: str, number: str, weekly_rate: str = "185.00") -> Room:
    building = Building(name=building_name, address="1 Campus Road")
    db.add(building)
    db.flush()
    room = Room(
        building_id=building.id,
        room_number=number,
        room_type=RoomType.SINGLE,
        capacity=1,
        weekly_rate=Decimal(weekly_rate),
    )
    db.add(room)
    db.flush()
    return room
