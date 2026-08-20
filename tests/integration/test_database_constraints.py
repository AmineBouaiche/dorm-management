from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Booking, BookingStatus, Building, Room, RoomType, Student, User, UserRole


def make_user(db: Session, email: str = "student@example.com") -> User:
    user = User(email=email, password_hash="not-a-real-hash", role=UserRole.STUDENT)
    db.add(user)
    db.flush()
    return user


def make_student(db: Session, user: User, student_id: str = "ST20260001") -> Student:
    student = Student(user_id=user.id, student_id=student_id, first_name="Test", last_name="Student")
    db.add(student)
    db.flush()
    return student


def make_building(db: Session, name: str = "Test Hall") -> Building:
    building = Building(name=name, address="1 Test Street")
    db.add(building)
    db.flush()
    return building


def make_room(db: Session, building: Building, room_number: str = "101") -> Room:
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


def test_duplicate_user_email_is_rejected(db_session: Session) -> None:
    make_user(db_session, "duplicate@example.com")
    db_session.add(User(email="duplicate@example.com", password_hash="hash", role=UserRole.ADMIN))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_duplicate_student_id_is_rejected(db_session: Session) -> None:
    first_user = make_user(db_session, "first@example.com")
    make_student(db_session, first_user, "ST-DUP")
    second_user = make_user(db_session, "second@example.com")
    db_session.add(Student(user_id=second_user.id, student_id="ST-DUP", first_name="Second", last_name="Student"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_room_number_is_unique_within_building(db_session: Session) -> None:
    building = make_building(db_session)
    make_room(db_session, building, "101")
    db_session.add(
        Room(
            building_id=building.id,
            room_number="101",
            room_type=RoomType.SHARED,
            capacity=2,
            weekly_rate=Decimal("145.00"),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_same_room_number_is_allowed_in_different_buildings(db_session: Session) -> None:
    first = make_building(db_session, "First Hall")
    second = make_building(db_session, "Second Hall")
    make_room(db_session, first, "101")
    make_room(db_session, second, "101")
    db_session.flush()


def test_room_capacity_must_be_positive(db_session: Session) -> None:
    building = make_building(db_session)
    db_session.add(
        Room(
            building_id=building.id,
            room_number="000",
            room_type=RoomType.SINGLE,
            capacity=0,
            weekly_rate=Decimal("100.00"),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_room_weekly_rate_cannot_be_negative(db_session: Session) -> None:
    building = make_building(db_session)
    db_session.add(
        Room(
            building_id=building.id,
            room_number="102",
            room_type=RoomType.SINGLE,
            capacity=1,
            weekly_rate=Decimal("-0.01"),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_booking_end_date_must_follow_start_date(db_session: Session) -> None:
    user = make_user(db_session)
    student = make_student(db_session, user)
    building = make_building(db_session)
    room = make_room(db_session, building)
    db_session.add(
        Booking(
            student_id=student.id,
            room_id=room.id,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 1),
            amount=Decimal("2500.00"),
            status=BookingStatus.CONFIRMED,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_booking_foreign_keys_are_enforced(db_session: Session) -> None:
    db_session.add(
        Booking(
            student_id=999999,
            room_id=999999,
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            amount=Decimal("2500.00"),
            status=BookingStatus.CONFIRMED,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_database_rejects_overlapping_bookings_for_same_room(db_session: Session) -> None:
    first_user = make_user(db_session, "room-first@example.com")
    first_student = make_student(db_session, first_user, "ST-ROOM-1")
    second_user = make_user(db_session, "room-second@example.com")
    second_student = make_student(db_session, second_user, "ST-ROOM-2")
    building = make_building(db_session, "Exclusion Room Hall")
    room = make_room(db_session, building, "901")

    db_session.add(
        Booking(
            student_id=first_student.id,
            room_id=room.id,
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            amount=Decimal("2500.00"),
            status=BookingStatus.PENDING,
        )
    )
    db_session.flush()

    db_session.add(
        Booking(
            student_id=second_student.id,
            room_id=room.id,
            start_date=date(2027, 1, 1),
            end_date=date(2027, 8, 1),
            amount=Decimal("2500.00"),
            status=BookingStatus.CONFIRMED,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_database_rejects_overlapping_bookings_for_same_student(db_session: Session) -> None:
    user = make_user(db_session, "student-overlap@example.com")
    student = make_student(db_session, user, "ST-STUDENT-OVERLAP")
    first_building = make_building(db_session, "Exclusion Student Hall A")
    second_building = make_building(db_session, "Exclusion Student Hall B")
    first_room = make_room(db_session, first_building, "902")
    second_room = make_room(db_session, second_building, "902")

    db_session.add(
        Booking(
            student_id=student.id,
            room_id=first_room.id,
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            amount=Decimal("2500.00"),
            status=BookingStatus.PENDING,
        )
    )
    db_session.flush()

    db_session.add(
        Booking(
            student_id=student.id,
            room_id=second_room.id,
            start_date=date(2026, 10, 1),
            end_date=date(2027, 5, 1),
            amount=Decimal("2500.00"),
            status=BookingStatus.CONFIRMED,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()
