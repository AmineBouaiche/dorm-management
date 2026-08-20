from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import bearer, create_admin, create_room, login_admin, register_and_login_student


def test_student_creates_booking_as_authenticated_identity(client: TestClient, db_session: Session) -> None:
    student, token = register_and_login_student(client, "42001")
    room = create_room(db_session, "Booking Hall", "101", "185.00")

    response = client.post(
        "/api/bookings",
        headers=bearer(token),
        json={"room_id": room.id, "start_date": "2026-09-01", "end_date": "2027-06-30"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["student"]["student_id"] == student["student_id"]
    assert payload["status"] == "pending"
    assert Decimal(payload["amount"]) == Decimal("8140.00")


def test_booking_body_cannot_select_student_identity(client: TestClient, db_session: Session) -> None:
    _, token = register_and_login_student(client, "42002")
    room = create_room(db_session, "Identity Hall", "102")
    response = client.post(
        "/api/bookings",
        headers=bearer(token),
        json={
            "student_id": "ST-SOMEONE-ELSE",
            "room_id": room.id,
            "start_date": "2026-09-01",
            "end_date": "2027-06-30",
        },
    )
    assert response.status_code == 422


def test_overlapping_room_booking_returns_409(client: TestClient, db_session: Session) -> None:
    _, first_token = register_and_login_student(client, "42003")
    _, second_token = register_and_login_student(client, "42004")
    room = create_room(db_session, "Conflict Hall", "103")

    assert client.post(
        "/api/bookings",
        headers=bearer(first_token),
        json={"room_id": room.id, "start_date": "2026-09-01", "end_date": "2027-06-30"},
    ).status_code == 201

    response = client.post(
        "/api/bookings",
        headers=bearer(second_token),
        json={"room_id": room.id, "start_date": "2027-01-01", "end_date": "2027-08-01"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Room is unavailable for this period"


def test_student_cannot_hold_overlapping_rooms(client: TestClient, db_session: Session) -> None:
    _, token = register_and_login_student(client, "42005")
    first_room = create_room(db_session, "Student Hall A", "201")
    second_room = create_room(db_session, "Student Hall B", "201")

    assert client.post(
        "/api/bookings",
        headers=bearer(token),
        json={"room_id": first_room.id, "start_date": "2026-09-01", "end_date": "2027-06-30"},
    ).status_code == 201

    response = client.post(
        "/api/bookings",
        headers=bearer(token),
        json={"room_id": second_room.id, "start_date": "2026-10-01", "end_date": "2027-05-01"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Student already has an overlapping booking"


def test_student_can_list_and_cancel_own_booking(client: TestClient, db_session: Session) -> None:
    _, token = register_and_login_student(client, "42006")
    room = create_room(db_session, "Own Booking Hall", "301")
    created = client.post(
        "/api/bookings",
        headers=bearer(token),
        json={"room_id": room.id, "start_date": "2026-09-01", "end_date": "2027-06-30"},
    )
    booking_id = created.json()["id"]

    history = client.get("/api/bookings/me", headers=bearer(token))
    assert history.status_code == 200
    assert [booking["id"] for booking in history.json()] == [booking_id]

    cancelled = client.patch(f"/api/bookings/{booking_id}/cancel", headers=bearer(token))
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_student_cannot_cancel_another_students_booking(client: TestClient, db_session: Session) -> None:
    _, owner_token = register_and_login_student(client, "42007")
    _, other_token = register_and_login_student(client, "42008")
    room = create_room(db_session, "Ownership Hall", "401")
    created = client.post(
        "/api/bookings",
        headers=bearer(owner_token),
        json={"room_id": room.id, "start_date": "2026-09-01", "end_date": "2027-06-30"},
    )
    response = client.patch(
        f"/api/bookings/{created.json()['id']}/cancel",
        headers=bearer(other_token),
    )
    assert response.status_code == 403


def test_admin_can_confirm_booking_and_student_cannot(client: TestClient, db_session: Session) -> None:
    _, student_token = register_and_login_student(client, "42009")
    room = create_room(db_session, "Admin Hall", "501", "220.00")
    booking = client.post(
        "/api/bookings",
        headers=bearer(student_token),
        json={"room_id": room.id, "start_date": "2026-09-01", "end_date": "2027-06-30"},
    ).json()

    denied = client.patch(
        f"/api/admin/bookings/{booking['id']}/confirm",
        headers=bearer(student_token),
    )
    assert denied.status_code == 403

    create_admin(db_session)
    admin_token = login_admin(client)
    confirmed = client.patch(
        f"/api/admin/bookings/{booking['id']}/confirm",
        headers=bearer(admin_token),
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"


def test_booking_amount_uses_weekly_rate_and_rounds_partial_week_up(
    client: TestClient, db_session: Session
) -> None:
    _, token = register_and_login_student(client, "42010")
    room = create_room(db_session, "Weekly Billing Hall", "601", "185.00")

    response = client.post(
        "/api/bookings",
        headers=bearer(token),
        json={"room_id": room.id, "start_date": "2027-09-01", "end_date": "2027-09-09"},
    )

    assert response.status_code == 201
    assert Decimal(response.json()["amount"]) == Decimal("370.00")


def test_student_cannot_book_inactive_inventory(client: TestClient, db_session: Session) -> None:
    _, token = register_and_login_student(client, "42011")
    room = create_room(db_session, "Retired Hall", "701", "185.00")
    room.is_active = False
    db_session.flush()

    response = client.post(
        "/api/bookings",
        headers=bearer(token),
        json={"room_id": room.id, "start_date": "2027-09-01", "end_date": "2028-06-30"},
    )
    assert response.status_code == 404
