from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Booking, BookingStatus, Building, Room, RoomType, Student, User, UserRole
from tests.helpers import bearer, create_admin, login_admin


def seed_room(db: Session, building_name: str = "North Hall", room_number: str = "101") -> Room:
    building = Building(name=building_name, address="1 Campus Road")
    db.add(building)
    db.flush()
    room = Room(
        building_id=building.id,
        room_number=room_number,
        room_type=RoomType.SINGLE,
        capacity=1,
        weekly_rate=Decimal("185.00"),
    )
    db.add(room)
    db.flush()
    return room


def seed_student(db: Session) -> Student:
    user = User(email="student@example.com", password_hash="hash", role=UserRole.STUDENT)
    db.add(user)
    db.flush()
    student = Student(user_id=user.id, student_id="ST20260001", first_name="Test", last_name="Student")
    db.add(student)
    db.flush()
    return student


def test_create_building_and_room(client: TestClient, db_session: Session) -> None:
    create_admin(db_session)
    token = login_admin(client)
    building_response = client.post(
        "/api/buildings",
        headers=bearer(token),
        json={"name": "Clifton Hall", "address": "10 University Road"},
    )
    assert building_response.status_code == 201
    building_id = building_response.json()["id"]

    room_response = client.post(
        "/api/rooms",
        headers=bearer(token),
        json={
            "building_id": building_id,
            "room_number": "A101",
            "room_type": "single",
            "capacity": 1,
            "weekly_rate": "195.00",
        },
    )
    assert room_response.status_code == 201
    assert room_response.json()["room_number"] == "A101"
    assert room_response.json()["building"]["name"] == "Clifton Hall"


def test_get_unknown_room_returns_404(client: TestClient) -> None:
    response = client.get("/api/rooms/999999")
    assert response.status_code == 404


def test_available_rooms_excludes_overlapping_confirmed_booking(
    client: TestClient, db_session: Session
) -> None:
    booked_room = seed_room(db_session, "Booked Hall", "101")
    free_room = seed_room(db_session, "Free Hall", "201")
    student = seed_student(db_session)
    db_session.add(
        Booking(
            student_id=student.id,
            room_id=booked_room.id,
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            amount=Decimal("2500.00"),
            status=BookingStatus.CONFIRMED,
        )
    )
    db_session.flush()

    response = client.get(
        "/api/rooms/available",
        params={"start_date": "2026-10-01", "end_date": "2027-05-01"},
    )

    assert response.status_code == 200
    room_ids = {room["id"] for room in response.json()}
    assert booked_room.id not in room_ids
    assert free_room.id in room_ids


def test_cancelled_booking_does_not_block_room(client: TestClient, db_session: Session) -> None:
    room = seed_room(db_session)
    student = seed_student(db_session)
    db_session.add(
        Booking(
            student_id=student.id,
            room_id=room.id,
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            amount=Decimal("2500.00"),
            status=BookingStatus.CANCELLED,
        )
    )
    db_session.flush()

    response = client.get(
        "/api/rooms/available",
        params={"start_date": "2026-10-01", "end_date": "2027-05-01"},
    )

    assert response.status_code == 200
    assert room.id in {item["id"] for item in response.json()}


def test_adjacent_booking_does_not_block_room(client: TestClient, db_session: Session) -> None:
    room = seed_room(db_session)
    student = seed_student(db_session)
    db_session.add(
        Booking(
            student_id=student.id,
            room_id=room.id,
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            amount=Decimal("2500.00"),
            status=BookingStatus.CONFIRMED,
        )
    )
    db_session.flush()

    response = client.get(
        "/api/rooms/available",
        params={"start_date": "2027-06-30", "end_date": "2027-07-31"},
    )

    assert response.status_code == 200
    assert room.id in {item["id"] for item in response.json()}


def test_invalid_availability_window_returns_422(client: TestClient) -> None:
    response = client.get(
        "/api/rooms/available",
        params={"start_date": "2027-01-01", "end_date": "2026-01-01"},
    )
    assert response.status_code == 422


def test_admin_can_update_building_image_and_status(client: TestClient, db_session: Session) -> None:
    create_admin(db_session)
    token = login_admin(client)
    created = client.post(
        "/api/buildings",
        headers=bearer(token),
        json={"name": "Image Hall", "address": "5 Campus Road"},
    )
    building_id = created.json()["id"]

    updated = client.patch(
        f"/api/buildings/{building_id}",
        headers=bearer(token),
        json={"image_url": "/static/assets/residences/image-hall.webp", "is_active": False},
    )

    assert updated.status_code == 200
    assert updated.json()["image_url"] == "/static/assets/residences/image-hall.webp"
    assert updated.json()["is_active"] is False
    assert building_id not in {item["id"] for item in client.get("/api/buildings").json()}

    admin_list = client.get("/api/admin/buildings", headers=bearer(token))
    assert admin_list.status_code == 200
    assert building_id in {item["id"] for item in admin_list.json()}


def test_admin_can_update_room_weekly_rate_and_deactivate_it(client: TestClient, db_session: Session) -> None:
    room = seed_room(db_session, "Editable Hall", "E101")
    create_admin(db_session)
    token = login_admin(client)

    updated = client.patch(
        f"/api/rooms/{room.id}",
        headers=bearer(token),
        json={"weekly_rate": "205.50", "is_active": False},
    )

    assert updated.status_code == 200
    assert Decimal(updated.json()["weekly_rate"]) == Decimal("205.50")
    assert updated.json()["is_active"] is False
    assert client.get(f"/api/rooms/{room.id}").status_code == 404
    assert room.id not in {item["id"] for item in client.get("/api/rooms").json()}

    admin_list = client.get("/api/admin/rooms", headers=bearer(token))
    assert admin_list.status_code == 200
    assert room.id in {item["id"] for item in admin_list.json()}


def test_inactive_building_hides_rooms_from_availability(client: TestClient, db_session: Session) -> None:
    room = seed_room(db_session, "Inactive Residence", "I101")
    room.building.is_active = False
    db_session.flush()

    response = client.get(
        "/api/rooms/available",
        params={"start_date": "2027-09-01", "end_date": "2028-06-30"},
    )

    assert response.status_code == 200
    assert room.id not in {item["id"] for item in response.json()}
