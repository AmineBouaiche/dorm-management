from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import bearer, create_admin, create_room, login_admin, register_and_login_student


def test_admin_only_endpoints_reject_student(client: TestClient) -> None:
    _, token = register_and_login_student(client, "43001")
    assert client.get("/api/admin/students", headers=bearer(token)).status_code == 403
    assert client.get("/api/admin/bookings", headers=bearer(token)).status_code == 403
    assert client.get("/api/admin/analytics", headers=bearer(token)).status_code == 403


def test_admin_can_create_building_and_room(client: TestClient, db_session: Session) -> None:
    create_admin(db_session)
    token = login_admin(client)
    building = client.post(
        "/api/buildings",
        headers=bearer(token),
        json={"name": "Admin Created Hall", "address": "10 University Road"},
    )
    assert building.status_code == 201

    room = client.post(
        "/api/rooms",
        headers=bearer(token),
        json={
            "building_id": building.json()["id"],
            "room_number": "A101",
            "room_type": "single",
            "capacity": 1,
            "weekly_rate": "195.00",
        },
    )
    assert room.status_code == 201


def test_student_cannot_create_building(client: TestClient) -> None:
    _, token = register_and_login_student(client, "43002")
    response = client.post(
        "/api/buildings",
        headers=bearer(token),
        json={"name": "Forbidden Hall", "address": "No Access"},
    )
    assert response.status_code == 403


def test_admin_lists_students_and_bookings(client: TestClient, db_session: Session) -> None:
    student, student_token = register_and_login_student(client, "43003")
    room = create_room(db_session, "Listing Hall", "101")
    booking = client.post(
        "/api/bookings",
        headers=bearer(student_token),
        json={"room_id": room.id, "start_date": "2026-09-01", "end_date": "2027-06-30"},
    )
    assert booking.status_code == 201

    create_admin(db_session)
    admin_token = login_admin(client)
    students = client.get("/api/admin/students", headers=bearer(admin_token))
    bookings = client.get("/api/admin/bookings", headers=bearer(admin_token))
    assert students.status_code == 200
    assert student["student_id"] in {item["student_id"] for item in students.json()}
    assert bookings.status_code == 200
    assert booking.json()["id"] in {item["id"] for item in bookings.json()}


def test_admin_analytics_reports_occupancy_and_revenue(client: TestClient, db_session: Session) -> None:
    _, student_token = register_and_login_student(client, "43004")
    occupied_room = create_room(db_session, "Analytics Hall A", "201", "200.00")
    create_room(db_session, "Analytics Hall B", "202", "180.00")
    booking = client.post(
        "/api/bookings",
        headers=bearer(student_token),
        json={"room_id": occupied_room.id, "start_date": "2026-09-01", "end_date": "2027-06-30"},
    ).json()

    create_admin(db_session)
    admin_token = login_admin(client)
    assert client.patch(
        f"/api/admin/bookings/{booking['id']}/confirm",
        headers=bearer(admin_token),
    ).status_code == 200

    response = client.get(
        "/api/admin/analytics",
        params={"on_date": date(2026, 10, 1).isoformat()},
        headers=bearer(admin_token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_rooms"] == 2
    assert payload["occupied_rooms"] == 1
    assert payload["available_rooms"] == 1
    assert payload["confirmed_booking_count"] == 1
    assert Decimal(payload["total_confirmed_revenue"]) == Decimal("8800.00")
