from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditLog, Booking, BookingStatus
from tests.helpers import (
    bearer,
    create_admin,
    create_room,
    login_admin,
    register_and_login_student,
)


def test_request_logging_is_sparse_and_does_not_log_query_values(
    client: TestClient,
    caplog,
) -> None:
    request_logger = logging.getLogger("dorm_management.requests")
    previous_level = request_logger.level
    previous_propagate = request_logger.propagate
    request_logger.setLevel(logging.INFO)
    request_logger.propagate = True
    try:
        with caplog.at_level(logging.INFO):
            response = client.get(
                "/health?token=do-not-log-this",
                headers={"X-Request-ID": "safe-log-test"},
            )
    finally:
        request_logger.setLevel(previous_level)
        request_logger.propagate = previous_propagate

    assert response.status_code == 200
    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "dorm_management.requests"
    ]
    assert any("request_id=safe-log-test" in message for message in messages)
    assert any(
        "method=GET" in message and "path=/health" in message and "status=200" in message
        for message in messages
    )
    assert all("do-not-log-this" not in message for message in messages)
    assert all("token=" not in message for message in messages)


def test_admin_building_mutation_creates_persistent_audit_event(
    client: TestClient,
    db_session: Session,
) -> None:
    admin = create_admin(db_session)
    token = login_admin(client)

    response = client.post(
        "/api/buildings",
        headers={**bearer(token), "X-Request-ID": "audit-building-1"},
        json={"name": "Audit Hall", "address": "1 Audit Road"},
    )

    assert response.status_code == 201
    event = db_session.scalar(select(AuditLog).where(AuditLog.action == "building.create"))
    assert event is not None
    assert event.actor_user_id == admin.id
    assert event.resource_type == "building"
    assert event.resource_id == response.json()["id"]
    assert event.request_id == "audit-building-1"
    assert event.details is None


def test_admin_booking_confirmation_is_audited(
    client: TestClient,
    db_session: Session,
) -> None:
    admin = create_admin(db_session)
    token = login_admin(client)
    student, _ = register_and_login_student(client, "AUDITCONFIRM")
    room = create_room(db_session, "Audit Booking Hall", "201", "200.00")
    booking = Booking(
        student_id=student["id"],
        room_id=room.id,
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=44),
        amount=Decimal("400.00"),
        status=BookingStatus.PENDING,
    )
    db_session.add(booking)
    db_session.flush()

    response = client.patch(
        f"/api/admin/bookings/{booking.id}/confirm",
        headers={**bearer(token), "X-Request-ID": "audit-booking-1"},
    )

    assert response.status_code == 200
    event = db_session.scalar(select(AuditLog).where(AuditLog.action == "booking.confirm"))
    assert event is not None
    assert event.actor_user_id == admin.id
    assert event.resource_id == booking.id
    assert event.request_id == "audit-booking-1"


def test_audit_log_endpoint_is_admin_only_and_paginated(
    client: TestClient,
    db_session: Session,
) -> None:
    create_admin(db_session)
    admin_token = login_admin(client)
    _, student_token = register_and_login_student(client, "AUDITREAD")

    for index in range(3):
        response = client.post(
            "/api/buildings",
            headers={**bearer(admin_token), "X-Request-ID": f"audit-read-{index}"},
            json={"name": f"Audit Read Hall {index}", "address": f"{index} Audit Road"},
        )
        assert response.status_code == 201

    forbidden = client.get("/api/admin/audit-logs", headers=bearer(student_token))
    assert forbidden.status_code == 403

    response = client.get(
        "/api/admin/audit-logs?page=1&per_page=2",
        headers=bearer(admin_token),
    )
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.headers["X-Total-Count"] == "3"
    assert response.headers["X-Page"] == "1"
    assert response.headers["X-Per-Page"] == "2"


def test_failed_admin_mutation_does_not_create_audit_event(
    client: TestClient,
    db_session: Session,
) -> None:
    create_admin(db_session)
    token = login_admin(client)

    response = client.patch(
        "/api/rooms/999999",
        headers={**bearer(token), "X-Request-ID": "audit-failed-1"},
        json={"weekly_rate": "199.00"},
    )

    assert response.status_code == 404
    assert db_session.scalar(select(func.count(AuditLog.id))) == 0
