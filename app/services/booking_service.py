from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking
from app.models.building import Building
from app.models.enums import BookingStatus
from app.models.room import Room
from app.models.student import Student
from app.schemas.booking import BookingCreate


class BookingNotFoundError(Exception):
    pass


class StudentNotFoundError(Exception):
    pass


class RoomNotFoundError(Exception):
    pass


class RoomUnavailableError(Exception):
    pass


class StudentBookingConflictError(Exception):
    pass


class BookingStateError(Exception):
    pass


class BookingOwnershipError(Exception):
    pass


BLOCKING_STATUSES = (BookingStatus.PENDING, BookingStatus.CONFIRMED)


def _booking_query():
    return select(Booking).options(
        joinedload(Booking.student).joinedload(Student.user),
        joinedload(Booking.room).joinedload(Room.building),
    )


def _constraint_name(exc: IntegrityError) -> str | None:
    original = exc.orig
    diag = getattr(original, "diag", None)
    return getattr(diag, "constraint_name", None)


def list_bookings(db: Session) -> list[Booking]:
    statement = _booking_query().order_by(Booking.created_at.desc(), Booking.id.desc())
    return list(db.scalars(statement).all())


def get_booking(db: Session, booking_id: int) -> Booking:
    booking = db.scalar(_booking_query().where(Booking.id == booking_id))
    if booking is None:
        raise BookingNotFoundError
    return booking


def list_student_bookings_by_db_id(db: Session, student_id: int) -> list[Booking]:
    statement = (
        _booking_query()
        .where(Booking.student_id == student_id)
        .order_by(Booking.start_date.desc(), Booking.id.desc())
    )
    return list(db.scalars(statement).all())


def list_student_bookings(db: Session, student_identifier: str) -> list[Booking]:
    student = db.scalar(select(Student).where(Student.student_id == student_identifier.strip()))
    if student is None:
        raise StudentNotFoundError
    return list_student_bookings_by_db_id(db, student.id)


def _room_has_overlap(db: Session, room_id: int, data: BookingCreate) -> bool:
    statement = select(
        select(Booking.id)
        .where(
            Booking.room_id == room_id,
            Booking.status.in_(BLOCKING_STATUSES),
            Booking.start_date < data.end_date,
            Booking.end_date > data.start_date,
        )
        .exists()
    )
    return bool(db.scalar(statement))


def _student_has_overlap(db: Session, student_id: int, data: BookingCreate) -> bool:
    statement = select(
        select(Booking.id)
        .where(
            Booking.student_id == student_id,
            Booking.status.in_(BLOCKING_STATUSES),
            Booking.start_date < data.end_date,
            Booking.end_date > data.start_date,
        )
        .exists()
    )
    return bool(db.scalar(statement))


def create_booking(db: Session, student: Student, data: BookingCreate) -> Booking:
    room = db.get(Room, data.room_id)
    if room is None or not room.is_active or not room.building.is_active:
        raise RoomNotFoundError

    if _room_has_overlap(db, room.id, data):
        raise RoomUnavailableError
    if _student_has_overlap(db, student.id, data):
        raise StudentBookingConflictError

    billable_weeks = ((data.end_date - data.start_date).days + 6) // 7
    booking = Booking(
        student_id=student.id,
        room_id=room.id,
        start_date=data.start_date,
        end_date=data.end_date,
        amount=room.weekly_rate * billable_weeks,
        status=BookingStatus.PENDING,
    )
    db.add(booking)

    try:
        db.commit()
    except IntegrityError as exc:
        constraint = _constraint_name(exc)
        db.rollback()
        if constraint == "excl_booking_room_overlap":
            raise RoomUnavailableError from exc
        if constraint == "excl_booking_student_overlap":
            raise StudentBookingConflictError from exc
        raise

    return get_booking(db, booking.id)


def confirm_booking(db: Session, booking_id: int) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise BookingNotFoundError
    if booking.status != BookingStatus.PENDING:
        raise BookingStateError

    booking.status = BookingStatus.CONFIRMED
    db.commit()
    return get_booking(db, booking.id)


def cancel_booking(db: Session, booking_id: int) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise BookingNotFoundError
    if booking.status == BookingStatus.CANCELLED:
        raise BookingStateError

    booking.status = BookingStatus.CANCELLED
    db.commit()
    return get_booking(db, booking.id)


def cancel_own_booking(db: Session, booking_id: int, student_id: int) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise BookingNotFoundError
    if booking.student_id != student_id:
        raise BookingOwnershipError
    return cancel_booking(db, booking_id)


def revenue_summary(db: Session) -> tuple[Decimal, int]:
    statement = select(
        func.coalesce(func.sum(Booking.amount), 0),
        func.count(Booking.id),
    ).where(Booking.status == BookingStatus.CONFIRMED)
    total, count = db.execute(statement).one()
    return Decimal(total), int(count)


def analytics_summary(db: Session, on_date: date) -> dict[str, int | Decimal | date]:
    total_rooms = int(
        db.scalar(
            select(func.count(Room.id))
            .join(Room.building)
            .where(Room.is_active.is_(True), Building.is_active.is_(True))
        )
        or 0
    )

    occupied_rooms = int(
        db.scalar(
            select(func.count(func.distinct(Booking.room_id)))
            .join(Room, Booking.room_id == Room.id)
            .join(Building, Room.building_id == Building.id)
            .where(
                Room.is_active.is_(True),
                Building.is_active.is_(True),
                Booking.status == BookingStatus.CONFIRMED,
                Booking.start_date <= on_date,
                Booking.end_date > on_date,
            )
        )
        or 0
    )

    status_counts = db.execute(
        select(
            func.count(Booking.id),
            func.sum(case((Booking.status == BookingStatus.PENDING, 1), else_=0)),
            func.sum(case((Booking.status == BookingStatus.CONFIRMED, 1), else_=0)),
            func.sum(case((Booking.status == BookingStatus.CANCELLED, 1), else_=0)),
        )
    ).one()

    revenue, confirmed_count = revenue_summary(db)
    return {
        "on_date": on_date,
        "total_rooms": total_rooms,
        "occupied_rooms": occupied_rooms,
        "available_rooms": max(total_rooms - occupied_rooms, 0),
        "pending_booking_count": int(status_counts[1] or 0),
        "confirmed_booking_count": int(status_counts[2] or 0),
        "cancelled_booking_count": int(status_counts[3] or 0),
        "total_confirmed_revenue": revenue,
        "revenue_booking_count": confirmed_count,
    }
