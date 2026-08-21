from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.database import get_db
from app.schemas.admin import AdminAnalytics
from app.schemas.building import BuildingRead
from app.schemas.room import RoomRead
from app.schemas.booking import BookingRead
from app.schemas.student import StudentRead
from app.services import booking_service, building_service, room_service, student_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _student_to_read(student) -> StudentRead:
    return StudentRead(
        id=student.id,
        student_id=student.student_id,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.user.email,
    )


@router.get("/buildings", response_model=list[BuildingRead])
def list_all_buildings(db: Session = Depends(get_db)) -> list[BuildingRead]:
    return building_service.list_buildings(db, active_only=False)


@router.get("/rooms", response_model=list[RoomRead])
def list_all_rooms(db: Session = Depends(get_db)) -> list[RoomRead]:
    return room_service.list_rooms(db, active_only=False)


@router.get("/students", response_model=list[StudentRead])
def list_students(db: Session = Depends(get_db)) -> list[StudentRead]:
    return [_student_to_read(student) for student in student_service.list_students(db)]


@router.get("/bookings", response_model=list[BookingRead])
def list_bookings(db: Session = Depends(get_db)) -> list[BookingRead]:
    return booking_service.list_bookings(db)


@router.patch("/bookings/{booking_id}/confirm", response_model=BookingRead)
def confirm_booking(booking_id: int, db: Session = Depends(get_db)) -> BookingRead:
    try:
        return booking_service.confirm_booking(db, booking_id)
    except booking_service.BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found") from exc
    except booking_service.BookingStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking cannot be confirmed") from exc


@router.patch("/bookings/{booking_id}/cancel", response_model=BookingRead)
def cancel_booking(booking_id: int, db: Session = Depends(get_db)) -> BookingRead:
    try:
        return booking_service.cancel_booking(db, booking_id)
    except booking_service.BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found") from exc
    except booking_service.BookingStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking is already cancelled") from exc


@router.get("/analytics", response_model=AdminAnalytics)
def analytics(
    on_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AdminAnalytics:
    return AdminAnalytics(**booking_service.analytics_summary(db, on_date or date.today()))
